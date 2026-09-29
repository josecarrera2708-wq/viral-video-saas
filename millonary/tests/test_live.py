import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.backtest.data import load_perp
from src.backtest.funding import align_funding
from src.core.nucleo import CoreParams, compute_targets, run_core, _simulate
from src.live.config import LiveConfig, RiskLimits
from src.live.feed import BinanceFeed, BybitFeed, FeedRouter
from src.live.risk import RiskLayer, validate_bars
from src.live.pipeline import replay, process_pending
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
    kw.setdefault("min_history_bars", 300)
    cfg = LiveConfig(capital=capital, data_dir=d, **kw)
    return PaperTrader(cfg, Store(d / "s.db")), cfg


def now_after(bars): return bars.index[-1] + H4 + pd.Timedelta(seconds=60)


# ------------------------------------------------------------------ reproducción = backtest
def test_replay_matches_validated_backtest_simulator():
    d0, f0 = load_perp("4h"); mask = (d0.index >= "2022-06-01") & (d0.index < "2024-06-01")
    df, fund = d0[mask], f0[mask]                                   # velas + funding alineado del mismo tramo
    i0 = 2000                                                       # historia previa para el calentamiento
    cfg = LiveConfig(capital=1000.0, data_dir=pathlib.Path(tempfile.mkdtemp()), lot_step=1e-9, min_qty=1e-9,
                     min_notional=0.0, min_history_bars=1500, risk=RiskLimits(dd_halt=9.0, daily_loss_halt=9.0))
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
    """Con la MISMA medida que usa el vivo (caída desde máximos; pérdida desde la marca de las 00:00 UTC),
    los frenos (30 % / 7 %) no habrían saltado nunca en el histórico previo al ciego."""
    d0, f0 = load_perp("4h"); m = d0.index < "2025-07-01"
    eq = run_core(d0[m], f0[m])["equity"]
    dd = (1 - eq / eq.cummax()).max()
    day_start = eq.groupby(eq.index.floor("D")).transform("first")
    intraday = (1 - eq / day_start).max()
    assert dd < 0.30 and intraday < 0.07, (dd, intraday)


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
    bars = synth(2000); lim = RiskLimits(); v = lambda b, n: validate_bars(b, n, lim, H4, 1800)
    assert v(bars, now_after(bars)) == ([], [])
    assert any("atrasados" in p for p in v(bars, now_after(bars) + 3 * H4)[0])
    holed = bars.drop(bars.index[-8]); assert any("huecos" in p for p in v(holed, now_after(holed))[0])
    old_hole = bars.drop(bars.index[300]); pr, wr = v(old_hole, now_after(old_hole))
    assert pr == [] and any("antiguos" in w for w in wr)                    # un hueco antiguo NO bloquea (solo avisa)
    bad = bars.copy(); bad.iloc[-5, bad.columns.get_loc("high")] = bad.iloc[-5]["low"] * 0.5
    assert any("OHLC" in p for p in v(bad, now_after(bad))[0])
    jump = bars.copy(); jump.iloc[-1, jump.columns.get_indexer(["open", "high", "low", "close"])] *= 1.5
    pr, wr = v(jump, now_after(jump)); assert pr == [] and any("SALTO_GRANDE" in w for w in wr)   # un desplome real no bloquea
    assert any("insuficiente" in p for p in v(bars.iloc[:1000], now_after(bars.iloc[:1000]))[0])   # historia truncada bloquea
    assert any("abierta" in p for p in v(bars, bars.index[-1] + pd.Timedelta(hours=1))[0])


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
        if url.endswith("/time"): return {"serverTime": int(now.timestamp() * 1000)}
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
        if url.endswith("/time"): return {"retCode": 0, "result": {"timeSecond": str(int(now.timestamp()))}}
        sub = bars[bars.index <= pd.Timestamp(params["end"], unit="ms", tz="UTC")].iloc[-params["limit"]:]
        rows = [[str(int(t.timestamp() * 1000)), str(r.open), str(r.high), str(r.low), str(r.close), str(r.volume), "0"]
                for t, r in sub.iloc[::-1].iterrows()]
        return {"result": {"list": rows}}
    router = FeedRouter([BinanceFeed(http_get=blocked), BybitFeed(http_get=bybit_get)])
    got = router.bars(400, now)
    assert router.last_source == "bybit" and len(got) == 400 and "binance" in router.notes[0]
    def wrong(url, params=None):
        if url.endswith("/time"): return {"serverTime": int(now.timestamp() * 1000)}
        sub = bars[bars.index <= pd.Timestamp(params["endTime"], unit="ms", tz="UTC")].iloc[-params["limit"]:].copy()
        sub["close"] *= 1.02
        return _binance_rows(sub)
    with pytest.raises(RuntimeError, match="discrepan"):
        FeedRouter([BinanceFeed(http_get=wrong), BybitFeed(http_get=bybit_get)]).bars(400, now)
    with pytest.raises(RuntimeError, match="ninguna fuente"):
        FeedRouter([BinanceFeed(http_get=blocked), BybitFeed(http_get=blocked)]).bars(400, now)


def test_feed_detects_clock_skew_and_bybit_error_codes():
    bars = synth(500); now = bars.index[-1] + H4 + pd.Timedelta(seconds=30)
    def skewed(url, params=None):
        if url.endswith("/time"): return {"serverTime": int(now.timestamp() * 1000) - 120_000}    # el reloj local va 2 min adelantado
        return []
    with pytest.raises(RuntimeError, match="desincronizado"):
        BinanceFeed(http_get=skewed).bars(100, now)
    def bybit_err(url, params=None):
        if url.endswith("/time"): return {"retCode": 0, "result": {"timeSecond": str(int(now.timestamp()))}}
        return {"retCode": 10006, "retMsg": "rate limit", "result": {"list": []}}
    with pytest.raises(RuntimeError, match="retCode"):
        BybitFeed(http_get=bybit_err).bars(100, now)


# ------------------------------------------------------------------ correcciones de la revisión adversarial
def _noF(): return pd.DataFrame(columns=["time", "funding_rate"])


def test_pending_bars_are_all_processed_in_order_after_an_outage():
    """Revisión #2: tras una caída no se pierde ninguna vela (ni sus cambios de señal)."""
    bars = synth(1300); rk = RiskLimits(dd_halt=9, daily_loss_halt=9)
    a, _ = mk_trader(100000.0, risk=rk); b, _ = mk_trader(100000.0, risk=rk)
    for i in range(1000, 1200):                                            # A: procesa cada vela a su hora
        a.step(bars.iloc[: i + 1], _noF(), bars.index[i] + H4 + pd.Timedelta(seconds=60))
    for i in range(1000, 1060):                                            # B: funciona, se cae, y se levanta tarde
        b.step(bars.iloc[: i + 1], _noF(), bars.index[i] + H4 + pd.Timedelta(seconds=60))
    now = bars.index[1199] + H4 + pd.Timedelta(seconds=60)
    res = process_pending(b, bars.iloc[:1200], _noF(), now)
    assert sum(r["status"] == "ok" for r in res) == 1199 - 1059            # procesó TODAS las pendientes, en orden
    assert b.st.get("units") == pytest.approx(a.st.get("units")) and len(b.st.rows("trades")) == len(a.st.rows("trades"))
    assert b.equity(float(bars["close"].iloc[1199])) == pytest.approx(a.equity(float(bars["close"].iloc[1199])), rel=1e-12)


def test_fresh_account_without_start_only_processes_latest_bar():
    bars = synth(1300); tr, cfg = mk_trader(100000.0)
    res = process_pending(tr, bars, _noF(), bars.index[-1] + H4 + pd.Timedelta(seconds=60))
    assert len(res) == 1 and res[0]["bar"] == str(bars.index[-1])


def test_kill_and_halt_act_even_when_data_is_unreliable():
    """Revisión #5: la emergencia va antes que la validación de datos."""
    bars = synth(1300); tr, cfg = mk_trader(100000.0, risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    for i in range(1000, 1100):
        tr.step(bars.iloc[: i + 1], _noF(), bars.index[i] + H4 + pd.Timedelta(seconds=60))
    assert tr.st.get("units") > 0
    (cfg.data_dir / "KILL").write_text("x")
    stale_now = bars.index[1100] + H4 + 50 * H4                             # datos "atrasados": normalmente bloquearían
    r = tr.step(bars.iloc[:1101], _noF(), stale_now)
    assert r["status"] == "ok" and tr.st.get("units") == 0.0 and tr.st.get("halted") is True
    assert any("APLANADO_CON_DATOS_NO_FIABLES" in f for f in r["flags"])


def test_reset_halt_restarts_cleanly():
    """Revisión #6: la parada se puede deshacer (y no vuelve a saltar por un máximo antiguo)."""
    bars = synth(1300); tr, cfg = mk_trader(100000.0)
    for i in range(1000, 1050):
        tr.step(bars.iloc[: i + 1], _noF(), bars.index[i] + H4 + pd.Timedelta(seconds=60))
    (cfg.data_dir / "KILL").write_text("x")
    tr.step(bars.iloc[:1051], _noF(), bars.index[1050] + H4 + pd.Timedelta(seconds=60))
    assert tr.st.get("halted") is True
    with pytest.raises(RuntimeError, match="KILL"):
        tr.reset_halt(pd.Timestamp.now(tz="UTC"))
    (cfg.data_dir / "KILL").unlink()
    out = tr.reset_halt(pd.Timestamp.now(tz="UTC"))
    assert tr.st.get("halted") is False and tr.st.get("peak") == pytest.approx(out["peak"])
    r = tr.step(bars.iloc[:1052], _noF(), bars.index[1051] + H4 + pd.Timedelta(seconds=60))
    assert r["status"] == "ok" and not r.get("new_halt")


def test_late_funding_is_charged_later_and_never_lost():
    """Revisión #3: un funding publicado con retraso se cobra en la vela siguiente."""
    bars = synth(1300); tr, cfg = mk_trader(100000.0, risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    for i in range(1000, 1150):
        tr.step(bars.iloc[: i + 1], _noF(), bars.index[i] + H4 + pd.Timedelta(seconds=60))
    if tr.st.get("units") <= 0:
        pytest.skip("sin posición larga en este punto")
    t_close = bars.index[1150] + H4
    late = pd.DataFrame({"time": [t_close], "funding_rate": [0.001]})
    r1 = tr.step(bars.iloc[:1151], _noF(), t_close + pd.Timedelta(seconds=60))            # el evento aún no está publicado
    assert tr.st.rows("equity")[-1]["funding"] == 0.0
    r2 = tr.step(bars.iloc[:1152], late, bars.index[1151] + H4 + pd.Timedelta(seconds=60))  # aparece una vela después
    assert tr.st.rows("equity")[-1]["funding"] > 0


def test_truncated_history_is_rejected_not_traded():
    """Revisión #4: con historia corta la señal cambia; no se opera."""
    bars = synth(1300); d = pathlib.Path(tempfile.mkdtemp())
    tr = PaperTrader(LiveConfig(data_dir=d), Store(d / "s.db"))                         # min_history_bars = 1800 por defecto
    r = tr.step(bars, _noF(), now_after(bars))
    assert r["status"] == "datos_no_fiables" and any("insuficiente" in p for p in r["problems"])


def test_closing_dust_and_reducing_are_allowed_below_minimum_order():
    bars = synth(1300); tr, cfg = mk_trader(1000.0, risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    tr.st.set("units", 0.0004); tr.st.set("cash", 1000.0 - 0.0004 * float(bars["close"].iloc[1100]))
    (cfg.data_dir / "KILL").write_text("x")
    tr.step(bars.iloc[:1101], _noF(), bars.index[1100] + H4 + pd.Timedelta(seconds=60))
    assert tr.st.get("units") == 0.0                                                    # el polvo se cierra aunque sea < mínimo


def test_second_process_cannot_process_the_same_bar_twice():
    """Revisión #13: recomprobación de la vela procesada DENTRO de la transacción."""
    bars = synth(1300); d = pathlib.Path(tempfile.mkdtemp()); cfg = LiveConfig(data_dir=d, min_history_bars=300)
    a = PaperTrader(cfg, Store(d / "s.db")); b = PaperTrader(cfg, Store(d / "s.db"))
    now = now_after(bars.iloc[:1101])
    ra = a.step(bars.iloc[:1101], _noF(), now); rb = b.step(bars.iloc[:1101], _noF(), now)
    assert ra["status"] == "ok" and rb["status"] == "ya_procesada"
    assert len(a.st.rows("equity")) == 1
