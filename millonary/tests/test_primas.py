import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.primas import estrategias as S
from src.primas.data import expiries, symbol, last_friday


def _mkt(n_days=420, seed=0, prem=0.08):
    r = np.random.default_rng(seed); t = pd.date_range("2021-01-01", periods=n_days * 24, freq="1h", tz="UTC")
    s = 30000 * np.exp(np.cumsum(r.normal(0, 0.006, len(t))))
    spot = pd.DataFrame({"close": s}, index=t)
    fut = {}
    for e in expiries(t[-1] + pd.Timedelta(days=300)):
        left = ((e - (t + pd.Timedelta("1h"))) / pd.Timedelta("1D")).to_numpy()
        m = (left >= 0) & (left < 200)
        if m.any():
            fut[symbol(e)] = pd.DataFrame({"close": s[m] * (1 + prem * left[m] / 365)}, index=t[m])
    days = pd.date_range("2021-01-01", periods=n_days - 2, freq="1D", tz="UTC")
    return spot, fut, days


def test_expiries_are_last_fridays_0800():
    e = expiries(pd.Timestamp("2022-01-01", tz="UTC"))
    assert [symbol(x) for x in e] == ["BTCUSDT_210326", "BTCUSDT_210625", "BTCUSDT_210924", "BTCUSDT_211231"]
    assert all(x.weekday() == 4 and x.hour == 8 for x in e) and last_friday(2024, 3) == pd.Timestamp("2024-03-29 08:00", tz="UTC")


def test_basis_converges_to_locked_carry():
    spot, fut, days = _mkt()
    o = S.basis(spot, fut, days); tr = o["trades"]
    done = tr[tr["motivo"] == "vencimiento"]
    assert len(done) >= 3
    for _, t in done.iterrows():                      # convergencia exacta en la síntesis: ganancia = basis bloqueado − costes
        held = (t["salida"] - t["entrada"]) / pd.Timedelta("1D")
        locked = t["px_fut"] / t["px_spot"] - 1 - 0.08 * (1 / 24) / 365 * 0
        assert abs(t["ret"] - (locked - 2 * (S.SPOT_C + S.FUT_C) * 1.0)) < 0.0015, (t["ret"], locked, held)
    assert (1 + o["ret"]).prod() - 1 > 0


def test_basis_no_entry_when_basis_low_and_causal():
    spot, fut, days = _mkt(prem=0.02)
    assert S.basis(spot, fut, days)["n_ops"] == 0
    spot, fut, days = _mkt(); cut = days[200]
    sp2 = spot.copy(); sp2.loc[sp2.index >= cut + pd.Timedelta("1D"), "close"] *= 1.5
    f2 = {k: v.assign(close=np.where(v.index >= cut + pd.Timedelta("1D"), v["close"] * 0.7, v["close"])) for k, v in fut.items()}
    a, b = S.basis(spot, fut, days)["ret"], S.basis(sp2, f2, days)["ret"]
    assert np.allclose(a[a.index < cut], b[b.index < cut])


def test_basis_early_exit_triggers_when_basis_collapses():
    spot, fut, days = _mkt()
    k = sorted(fut)[0]; f = fut[k].copy(); half = f.index[len(f) * 3 // 4]
    f.loc[f.index >= half, "close"] = spot["close"].reindex(f.index[f.index >= half]).to_numpy()
    fut[k] = f
    tr = S.basis(spot, fut, days, early_exit=True)["trades"]
    assert (tr["motivo"] == "basis < 1 %").any()


def test_vrp_formula_cost_filter_and_causality():
    days = pd.date_range("2021-01-01", periods=200, freq="1D", tz="UTC"); r = np.random.default_rng(1)
    close = pd.Series(30000 * np.exp(np.cumsum(r.normal(0, 0.03, 200))), index=days)
    dv = pd.Series(60.0, index=days)
    o = S.vrp(close, dv, days[40:])
    lr = np.log(close.shift(-1) / close); d = days[50]; k = S.RISK_V / 3
    assert abs(o["ret"][d] - k * (1 - lr[d] ** 2 / (0.6 ** 2 / 365))) < 1e-12           # día sin rollo
    assert abs(o["ret"][days[40]] - (k * (1 - lr[days[40]] ** 2 / (0.6 ** 2 / 365)) - k * 2 * 30 * 1.5 / 100 / 0.6)) < 1e-12
    assert o["n_ops"] == int(np.ceil(159 / 30))                                           # 160 días con rollos cada 30 (el último día sin r)
    lo = S.vrp(close, pd.Series(10.0, index=days), days[40:], filt=True)                  # IV 10 % < RV ~57 %: nunca entra
    assert lo["n_ops"] == 0 and (lo["ret"] == 0).all()
    c2 = close.copy(); c2.iloc[121:] *= 2
    a, b = S.vrp(close, dv, days[40:])["ret"], S.vrp(c2, dv, days[40:])["ret"]
    assert np.allclose(a[:days[119]], b[:days[119]]) and not np.isclose(a[days[120]], b[days[120]])   # el día 120 usa P_121
