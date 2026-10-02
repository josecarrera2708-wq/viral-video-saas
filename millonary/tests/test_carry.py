import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.live.carry import CarryTrader, CarryConfig, process
from src.live.store import Store
from src.live.trader import reconcile_funding
from src.live.vision_feed import VisionFeed

H4 = pd.Timedelta("4h")


def bars(n=200, seed=0, vol=0.02):
    r = np.random.default_rng(seed); c = 60000 * np.exp(np.cumsum(r.normal(0, vol, n)))
    idx = pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC")
    df = pd.DataFrame({"open": c, "high": c * 1.01, "low": c * 0.99, "close": c, "volume": 1.0}, index=idx)
    return df, df.copy()


def events(idx, rate):
    t = pd.date_range(idx[0], idx[-1] + H4, freq="8h", tz="UTC")
    r = rate(np.arange(len(t))) if callable(rate) else np.full(len(t), rate)
    return pd.DataFrame({"time": t, "funding_rate": r, "synthetic": False})


def mk():
    d = pathlib.Path(tempfile.mkdtemp()); return CarryTrader(CarryConfig(), Store(d / "c.db"))


def test_enters_neutral_and_earns_only_funding():
    spot, perp = bars(); fu = events(spot.index, 0.0002); tr = mk(); start = spot.index[60] + H4
    start = start.floor("1D") + pd.Timedelta("1D")
    process(tr, spot, perp, fu, spot.index[-1] + H4 + pd.Timedelta("1min"), start)
    q_s, q_p = tr.st.get("spot"), tr.st.get("perp")
    assert q_s > 0 and q_p == pytest.approx(-q_s) and abs(q_s * 1000 - round(q_s * 1000)) < 1e-9          # misma cantidad, lote 0,001
    eq = pd.DataFrame(tr.st.rows("equity")).set_index("bar")
    after = eq.iloc[1:]
    inc = after["equity"].diff().dropna()
    fund = -after["funding"].iloc[1:]
    assert np.allclose(inc.to_numpy(), fund.to_numpy(), atol=1e-6)                 # el precio (±2 % por vela) no mueve la equity
    assert fund.sum() > 0 and len(tr.st.rows("trades")) == 2


def test_exits_when_7_day_funding_turns_negative():
    spot, perp = bars(400, vol=0.03); fu = events(spot.index, lambda i: np.where(i < 120, 0.0002, -0.0003)); tr = mk()
    start = spot.index[30].floor("1D") + pd.Timedelta("1D")
    process(tr, spot, perp, fu, spot.index[-1] + H4 + pd.Timedelta("1min"), start)
    reasons = [t["reason"] for t in tr.st.rows("trades")]
    assert reasons[0] == "entra" and reasons[-1] == "sale" and tr.st.get("spot") == 0 and tr.st.get("perp") == 0
    exit_bar = pd.Timestamp([t["bar"] for t in tr.st.rows("trades")][-1])
    assert exit_bar.hour == 0 and exit_bar > fu["time"].iloc[120]


def test_idempotent_and_never_trades_before_start():
    spot, perp = bars(); fu = events(spot.index, 0.0002); tr = mk(); start = pd.Timestamp("2026-01-20", tz="UTC"); now = spot.index[-1] + H4 + pd.Timedelta("1min")
    process(tr, spot, perp, fu, now, start); n1 = (len(tr.st.rows("equity")), len(tr.st.rows("trades")))
    process(tr, spot, perp, fu, now, start)
    assert (len(tr.st.rows("equity")), len(tr.st.rows("trades"))) == n1
    assert min(pd.Timestamp(r["bar"]) for r in tr.st.rows("equity")) == start


def test_provisional_funding_is_replaced_but_never_downgraded():
    spot, perp = bars(); tr = mk(); start = spot.index[0].floor("1D") + pd.Timedelta("1D"); now = spot.index[-1] + H4 + pd.Timedelta("1min")
    est = events(spot.index, 0.0002).assign(synthetic=True, estimado=True)
    process(tr, spot, perp, est, now, start)
    pend = tr.st.synthetic_funding(); assert pend
    fallback = est.assign(funding_rate=0.0001, estimado=False)
    assert reconcile_funding(tr.st, fallback, now) == 0.0 and len(tr.st.synthetic_funding()) == len(pend)
    real = est.assign(funding_rate=0.0003, synthetic=False, estimado=False)
    adj = reconcile_funding(tr.st, real, now)
    assert adj == pytest.approx(sum(u * p * (0.0003 - r) for _, r, u, p in pend)) and adj < 0 and tr.st.synthetic_funding() == []


def test_funding_estimate_follows_binance_formula():
    f = VisionFeed(get_bytes=lambda u: None)
    idx = pd.date_range("2026-10-01", periods=3 * 1440, freq="1min", tz="UTC")
    f._premium_day = lambda d: pd.Series(np.where(idx < pd.Timestamp("2026-10-02 04:00", tz="UTC"), 0.0003, 0.001), index=idx).loc[d:d + pd.Timedelta("1D") - pd.Timedelta("1min")]
    t = pd.DatetimeIndex(["2026-10-01 16:00", "2026-10-02 08:00"], tz="UTC")
    r, est = f.estimate_funding(t, pd.Timestamp("2026-10-04", tz="UTC"))
    assert est.all() and r[0] == pytest.approx(0.0001)                               # P = 0,03 % → P + clamp(0,01 % − P) = 0,01 %
    w = np.arange(1, 481); P = (0.0003 * w[:240].sum() + 0.001 * w[240:].sum()) / w.sum()   # pesos crecientes: lo reciente pesa más
    assert r[1] == pytest.approx(P + max(0.0001 - P, -0.0005))
