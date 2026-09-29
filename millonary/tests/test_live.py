import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.backtest.data import load_perp
from src.backtest.funding import align_funding
from src.core.nucleo import CoreParams, compute_targets, run_core, _simulate
from src.live.config import LiveConfig, RiskLimits
from src.live.feed import BinanceFeed, BybitFeed, FeedRouter
from src.live.risk import RiskLayer, validate_bars
from src.live.runner import replay
from src.live.store import Store
from src.live.trader import PaperTrader, INTERVAL

H4 = pd.Timedelta("4h")


def synth(n=1200, seed=0, start="2024-01-01"):
    rng = np.random.default_rng(seed)
    c = 30000 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * 1.004; l = np.minimum(o, c) * 0.996
    idx = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=idx)


def mk_trader(capital=1000.0, **kw):
    d = pathlib.Path(tempfile.mkdtemp())
    cfg = LiveConfig(capital=capital, data_dir=d, **kw)
    return PaperTrader(cfg, Store(d / "s.db")), cfg


def now_after(bars): return bars.index[-1] + H4 + pd.Timedelta(seconds=60)


# ------------------------------------------------------------------ reproducción = backtest
def test_replay_matches_validated_backtest_simulator():
    d0, f0 = load_perp("4h"); mask = (d0.index >= "2022-06-01") & (d0.index < "2024-06-01")
    df, fund = d0[mask], f0[mask]                                   # velas + funding alineado del mismo tramo
    i0 = 2000                                                       # historia previa para el calentamiento
    cfg = LiveConfig(capital=1000.0, data_dir=pathlib.Path(tempfile.mkdtemp()), lot_step=1e-9, min_qty=1e-9,
                     min_notional=0.0, risk=RiskLimits(dd_halt=9.0, daily_loss_halt=9.0))
    tr = PaperTrader(cfg, Store(":memory:"))
    ev = pd.DataFrame({"time": df.index + H4, "funding_rate": fund})
    ev = ev[ev["funding_rate"] != 0]
    replay(cfg, df, ev, str(df.index[i0]), str(df.index[-1]), trader=tr)
    eq_live = pd.Series({pd.Timestamp(r["bar"]): r["equity"] for r in tr.st.rows("equity")})
    # simulador validado sobre el mismo tramo, arrancando plano en i0
    ct = compute_targets(df, cfg.core); sig, tgt = ct["sig"], ct["tgt"]
    n = len(df); r = df["close"].pct_change().fillna(0).to_numpy()
    target = np.zeros(n); changed = np.zeros(n, bool)
    target[i0 + 1:] = tgt[i0:-1]
    changed[i0 + 1:] = (sig[i0:-1] != sig[i0 - 1:-2])
    eq, expo, turn, fc = _simulate(r[i0 + 1:], target[i0 + 1:], changed[i0 + 1:], fund[i0 + 1:], cfg.core.cost, cfg.core.band)
    ref_final = 1000.0 * eq[-1]
    live_final = eq_live.iloc[-1]
    assert abs(live_final / ref_final - 1) < 0.005, (live_final, ref_final)
    n_live = len(tr.st.rows("trades")); n_ref = int((turn > 0).sum())
    assert abs(n_live - n_ref) <= max(3, 0.05 * n_ref), (n_live, n_ref)


def test_risk_brakes_are_outside_the_validated_envelope():
    """Los frenos (DD 30 %, pérdida diaria 7 %) no habrían saltado nunca en el histórico del núcleo."""
    df, f = load_perp("4h")
    res = run_core(df, f)
    eq = res["equity"]; dd = (1 - eq / eq.cummax()).max()
    day = eq.resample("1D").last().pct_change().dropna()
    assert dd < 0.30 and day.min() > -0.07, (dd, day.min())


# ------------------------------------------------------------------ capa de riesgo
def test_risk_layer_limits():
    rl = RiskLayer(RiskLimits(), pathlib.Path(tempfile.mkdtemp()) / "KILL")
    assert rl.apply(0.5, 1000, 1000, 1000, False).target == 0.5
    assert rl.apply(3.0, 1000, 1000, 1000, False).target == 2.0                       # tope de exposición
    d = rl.apply(0.5, 690, 1000, 690, False); assert d.halted and d.flatten            # caída 31 % desde máximos
    d = rl.apply(0.5, 920, 1000, 1000, False); assert d.halted and d.flatten           # pérdida del día 8 %
    d = rl.apply(0.5, 950, 1000, 1000, False)                                          # 5 %: solo aviso
    assert not d.halted and d.target == 0.5 and any(f.startswith("AVISO_PERDIDA_DIARIA") for f in d.flags)
    d = rl.apply(0.5, 790, 1000, 790, False)                                           # caída 21 %: solo aviso
    assert not d.halted and any(f.startswith("AVISO_DD") for f in d.flags)
    assert rl.apply(0.5, 1000, 1000, 1000, True).halted                                # parado = sigue parado


def test_kill_switch_file_flattens():
    kf = pathlib.Path(tempfile.mkdtemp()) / "KILL"; kf.write_text("x")
    d = RiskLayer(RiskLimits(), kf).apply(0.5, 1000, 1000, 1000, False)
    assert d.flatten and d.halted and d.flags == ["KILL_SWITCH"]


def test_data_validation_catches_bad_data():
    bars = synth(1000); lim = RiskLimits()
    assert validate_bars(bars, now_after(bars), lim, H4) == []
    assert any("atrasados" in p for p in validate_bars(bars, now_after(bars) + 3 * H4, lim, H4))
    holed = bars.drop(bars.index[-20]); assert any("huecos" in p for p in validate_bars(holed, now_after(holed), lim, H4))
    bad = bars.copy(); bad.iloc[-5, bad.columns.get_loc("high")] = bad.iloc[-5]["low"] * 0.5
    assert any("OHLC" in p for p in validate_bars(bad, now_after(bad), lim, H4))
    jump = bars.copy(); jump.iloc[-1, jump.columns.get_indexer(["open", "high", "low", "close"])] *= 1.5
    assert any("sospechoso" in p for p in validate_bars(jump, now_after(jump), lim, H4))
    assert any("insuficiente" in p for p in validate_bars(bars.iloc[:100], now_after(bars.iloc[:100]), lim, H4))
    assert any("abierta" in p for p in validate_bars(bars, bars.index[-1] + pd.Timedelta(hours=1), lim, H4))


# ------------------------------------------------------------------ trader
def test_step_is_idempotent_and_survives_bad_data():
    bars = synth(1200); tr, cfg = mk_trader()
    fund = pd.DataFrame(columns=["time", "funding_rate"])
    a = tr.step(bars, fund, now_after(bars)); b = tr.step(bars, fund, now_after(bars))
    assert a["status"] == "ok" and b["status"] == "ya_procesada"
    n_eq = len(tr.st.rows("equity"))
    stale = tr.step(bars.iloc[:-1], fund, now_after(bars) + 5 * H4)
    assert stale["status"] in ("datos_no_fiables", "ya_procesada") and len(tr.st.rows("equity")) == n_eq


def test_small_account_respects_min_order_rules():
    bars = synth(1200); tr, cfg = mk_trader(capital=100.0)
    fund = pd.DataFrame(columns=["time", "funding_rate"])
    for i in range(1000, 1200):
        tr.step(bars.iloc[: i + 1], fund, bars.index[i] + H4 + pd.Timedelta(seconds=60))
    for t in tr.st.rows("trades"):
        assert abs(t["qty"]) >= cfg.min_qty - 1e-12
        u = round(abs(t["qty"]) / cfg.lot_step, 6); assert abs(u - round(u)) < 1e-6                 # múltiplo del lote


def test_funding_sign_long_pays_positive():
    bars = synth(1200); tr, cfg = mk_trader(capital=100000.0, risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    none = pd.DataFrame(columns=["time", "funding_rate"])
    for i in range(1000, 1150):
        tr.step(bars.iloc[: i + 1], none, bars.index[i] + H4 + pd.Timedelta(seconds=60))
    units = tr.st.get("units")
    if units <= 0:
        pytest.skip("la serie sintética no dejó posición larga en este punto")
    i = 1150; t_close = bars.index[i] + H4
    fund = pd.DataFrame({"time": [t_close], "funding_rate": [0.001]})
    before = tr.equity(float(bars["close"].iloc[i]))
    tr.step(bars.iloc[: i + 1], fund, t_close + pd.Timedelta(seconds=60))
    row = tr.st.rows("equity")[-1]
    assert row["funding"] == pytest.approx(units * float(bars["close"].iloc[i]) * 0.001)
    assert row["funding"] > 0                                                                       # coste para el largo


def test_kill_switch_flattens_position_through_trader():
    bars = synth(1200); tr, cfg = mk_trader(capital=100000.0)
    none = pd.DataFrame(columns=["time", "funding_rate"])
    for i in range(1000, 1100):
        tr.step(bars.iloc[: i + 1], none, bars.index[i] + H4 + pd.Timedelta(seconds=60))
    (cfg.data_dir / "KILL").write_text("stop")
    tr.step(bars.iloc[:1102], none, bars.index[1101] + H4 + pd.Timedelta(seconds=60))
    assert tr.st.get("units") == 0.0 and tr.st.get("halted") is True


# ------------------------------------------------------------------ feeds (sin red)
def _binance_rows(df):
    return [[int(t.timestamp() * 1000), str(r.open), str(r.high), str(r.low), str(r.close), str(r.volume),
             int((t + H4).timestamp() * 1000) - 1, "0", 1, "0", "0", "0"] for t, r in df.iterrows()]


def test_binance_feed_paginates_and_returns_only_closed_bars():
    bars = synth(4300)
    now = bars.index[-1] + pd.Timedelta(hours=1)                    # la última vela aún está abierta

    def fake_get(url, params=None):
        assert "fapi.binance.com" in url
        end = pd.Timestamp(params["endTime"], unit="ms", tz="UTC")
        sub = bars[bars.index <= end].iloc[-params["limit"]:]
        return _binance_rows(sub)
    got = BinanceFeed(http_get=fake_get).bars(4000, now)
    assert len(got) == 4000 and got.index[-1] == bars.index[-2]     # descarta la vela en formación
    assert got.index.is_monotonic_increasing and not got.index.has_duplicates
    assert (got.index.to_series().diff().dropna() == H4).all()


def test_router_falls_back_on_regional_block_and_detects_disagreement():
    bars = synth(500); now = bars.index[-1] + H4 + pd.Timedelta(seconds=30)

    def blocked(url, params=None): raise RuntimeError("HTTP 451")

    def bybit_get(url, params=None):
        sub = bars[bars.index <= pd.Timestamp(params["end"], unit="ms", tz="UTC")].iloc[-params["limit"]:]
        rows = [[str(int(t.timestamp() * 1000)), str(r.open), str(r.high), str(r.low), str(r.close), str(r.volume), "0"]
                for t, r in sub.iloc[::-1].iterrows()]
        return {"result": {"list": rows}}
    router = FeedRouter([BinanceFeed(http_get=blocked), BybitFeed(http_get=bybit_get)])
    got = router.bars(400, now)
    assert router.last_source == "bybit" and len(got) == 400 and "binance" in router.notes[0]
    def wrong(url, params=None):
        sub = bars[bars.index <= pd.Timestamp(params["endTime"], unit="ms", tz="UTC")].iloc[-params["limit"]:].copy()
        sub["close"] *= 1.02
        return _binance_rows(sub)
    with pytest.raises(RuntimeError, match="discrepan"):
        FeedRouter([BinanceFeed(http_get=wrong), BybitFeed(http_get=bybit_get)]).bars(400, now)
    with pytest.raises(RuntimeError, match="ninguna fuente"):
        FeedRouter([BinanceFeed(http_get=blocked), BybitFeed(http_get=blocked)]).bars(400, now)
