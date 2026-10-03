import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.acumulacion import forward as A
from src.cartera import gestor as G


def _px(n=120, seed=3):
    r = np.random.default_rng(seed); idx = pd.date_range("2026-09-01", periods=n, freq="1D", tz="UTC")
    return pd.Series(80000 * np.exp(np.cumsum(r.normal(0, 0.03, n))), index=idx)


def test_buy_hold_keeps_btc_and_enters_at_t0_close():
    px = _px(); t0 = px.index[10]; qty, p0, eq = A.buy_hold(px, t0)
    assert p0 == px.iloc[10] and abs(qty - 1000 * (1 - A.FEE) / p0) < 1e-12
    assert np.allclose(eq.values, qty * px.iloc[10:].values) and eq.index[0] == t0


def test_rebalanced_monthly_only_and_causal():
    px = _px(); R = pd.DataFrame({"a": px.pct_change().fillna(0.0), "b": 0.0, "c": 0.001}, index=px.index); w = {"a": .5, "b": .25, "c": .25}
    eq, W = A.rebalanced(R, w, px.index[5])
    me = G.month_end(W.index); back = np.abs(W.to_numpy() - np.array([.5, .25, .25])).sum(axis=1) < 1e-12
    assert back[0] and me[1:].any() and (back[1:] == me[1:]).all()                                  # vuelve al objetivo solo a fin de mes
    R2 = R.copy(); R2.iloc[60:] = -0.5; eq2, _ = A.rebalanced(R2, w, px.index[5])
    assert np.allclose(eq.iloc[:55], eq2.iloc[:55])                                                 # no mira al futuro
    assert abs(eq.iloc[0] - 1000 * (1 - G.COST)) < 1e-9


def test_btc_hold_dominates_mix_in_btc_when_btc_only_rises():
    idx = pd.date_range("2026-10-01", periods=200, freq="1D", tz="UTC"); px = pd.Series(80000 * 1.01 ** np.arange(200), index=idx)
    R = pd.DataFrame({"BTC": px.pct_change().fillna(0.0), "n": 0.0005, "c": 0.0003}, index=idx)
    _, p0, e1 = A.buy_hold(px, idx[0]); e2, _ = A.rebalanced(R, {"BTC": .5, "n": .25, "c": .25}, idx[0])
    assert (e1 / px).iloc[-1] > (e2 / px).iloc[-1]


def test_swept_converts_only_monthly_profits_and_keeps_base():
    idx = pd.date_range("2026-10-01", periods=120, freq="1D", tz="UTC"); px = pd.Series(80000.0, index=idx)
    R = pd.DataFrame({"n": 0.001, "c": 0.0005}, index=idx)
    u, b, e = A.swept(R, px, {"n": .5, "c": .5}, idx[0])
    me = G.month_end(idx); conv = b.diff().fillna(0) > 0
    assert (conv.to_numpy() <= me).all() and conv.sum() >= 3                     # solo convierte a fin de mes
    assert np.allclose(u[me].to_numpy()[1:], 1000 * (1 - 0 * G.COST), rtol=2e-3)  # la cuenta vuelve a 1.000
    R2 = R.copy(); R2[:] = -0.001; _, b2, _ = A.swept(R2, px, {"n": .5, "c": .5}, idx[0])
    assert b2.iloc[-1] == 0                                                         # con pérdidas no compra BTC
