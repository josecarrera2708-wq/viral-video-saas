import numpy as np
import pandas as pd
from src.backtest.engine import run, Params
from src.busqueda.sim5 import simulate, Gestion, Costes


def _b5(n=6000, seed=1, drift=0.0):
    rng = np.random.default_rng(seed); idx = pd.date_range("2022-01-01", periods=n, freq="5min", tz="UTC")
    c = 30000 * np.exp(np.cumsum(rng.normal(drift, 0.002, n))); o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.0003, n))
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.001, n)); l = np.minimum(o, c) * (1 - rng.uniform(0, 0.001, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=idx)


def _signals(b5, every=37, seed=2):
    rng = np.random.default_rng(seed); i = np.arange(20, len(b5) - 1, every)
    d = rng.choice([-1, 1], len(i)).astype(np.int8); sd = b5["close"].to_numpy()[i] * 0.004
    return i, d, sd


def test_base_igual_que_motor():
    b5 = _b5(); f = np.zeros(len(b5)); i, d, sd = _signals(b5)
    ent = np.zeros(len(b5), np.int8); ent[i] = d; stop = np.zeros(len(b5)); stop[i] = sd
    p = Params(capital=1000, lot_step=1e-12, min_qty=1e-12, min_notional=0, tp_mult=2.0, max_bars=48)
    r = run(b5["open"], b5["high"], b5["low"], b5["close"], ent, stop, p, funding=f)
    t = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, Gestion(k=2.0, horas=4.0, modo=0))
    assert len(t) == r["n_trades"]
    assert np.array_equal(t["entrada"].to_numpy(), b5.index[r["entry_idx"]].to_numpy())
    assert np.allclose(t["R"].to_numpy(), r["r"], atol=1e-6)


def test_promediar_sin_segunda_pata_es_la_base():
    b5 = _b5(seed=3); f = np.zeros(len(b5)); i, d, sd = _signals(b5)
    t0 = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, Gestion(modo=0))
    t1 = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, Gestion(modo=1, a=1.0, m=0.0, b=1.0, hh=-1))
    assert np.allclose(t0["R"].to_numpy(), t1["R"].to_numpy(), atol=1e-9)


def test_perdida_maxima_acotada_y_activaciones():
    b5 = _b5(seed=4); f = np.zeros(len(b5)); i, d, sd = _signals(b5)
    for g in (Gestion(modo=1, a=1.0, m=1.0, b=2.0, hh=0.0), Gestion(modo=2, a=1.0, m=1.0, b=1.0, k2=2.0), Gestion(modo=0)):
        t = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, g)
        assert t["R"].min() > -2.0                       # pérdida máxima (−1) + costes + huecos
        if g.modo:
            assert t["activada"].any()


def test_no_mira_el_futuro():
    b5 = _b5(seed=5); f = np.zeros(len(b5)); i, d, sd = _signals(b5)
    g = Gestion(modo=1, a=1.0, m=1.0, b=2.0, hh=0.0)
    full = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, g)
    cut = full["salida"].iloc[len(full) // 2]
    m = b5.index <= cut; part = simulate(b5[m], f[m], b5.index[i] + pd.Timedelta("5min"), d, sd, g)
    k = len(full) // 2 + 1
    assert np.allclose(full["R"].to_numpy()[:k], part["R"].to_numpy()[:k])


def test_paseo_aleatorio_sin_ventaja():
    """Sin ventaja, ninguna gestión crea esperanza positiva (pierde los costes)."""
    b5 = _b5(n=60000, seed=6); f = np.zeros(len(b5)); i, d, sd = _signals(b5, every=13, seed=7)
    for g in (Gestion(modo=0), Gestion(modo=1, a=1.0, m=1.0, b=2.0, hh=0.0), Gestion(modo=2, a=1.0, m=1.0, b=1.0)):
        t = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, g, Costes())
        assert t["R"].mean() < 0.05


def test_entrada_limite():
    b5 = _b5(seed=8); f = np.zeros(len(b5)); i, d, sd = _signals(b5)
    c = b5["close"].to_numpy()[i]; lim = c - d * 0.5 * sd
    t = simulate(b5, f, b5.index[i] + pd.Timedelta("5min"), d, sd, Gestion(), lim=lim, lim_bars=6)
    assert 0 < len(t) < len(i)
