import numpy as np
import pandas as pd
from src.busqueda.v11 import SETUPS


def _b5(n=12 * 24 * 150, seed=11):
    rng = np.random.default_rng(seed); idx = pd.date_range("2022-01-03", periods=n, freq="5min", tz="UTC")
    r = rng.standard_t(3, n) * 0.0015; c = 30000 * np.exp(np.cumsum(r)); o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.002, n)); l = np.minimum(o, c) * (1 - rng.uniform(0, 0.002, n))
    v = rng.uniform(5, 50, n); return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v, "trades": 100, "taker_buy_base": v * rng.uniform(0.3, 0.7, n)}, index=idx)


def _real():
    from src.busqueda.intradia5 import load5
    b5, _ = load5(); return b5[(b5.index >= "2022-01-01") & (b5.index < "2023-07-01")]


def test_causal_por_truncamiento():
    syn, real = _b5(), None
    for name, (fn, _, usa_oi) in SETUPS.items():
        if usa_oi:
            real = _real() if real is None else real
        b5 = real if usa_oi else syn
        full = fn(b5); assert len(full["t"]) > 0, name
        for cut in (len(b5) - 1, len(b5) - 300, len(b5) - 5000):
            part = fn(b5.iloc[:cut]); tc = b5.index[cut - 1] + pd.Timedelta("5min")
            m = full["t"] <= tc
            assert np.array_equal(full["t"][m], part["t"]), (name, cut)
            assert np.array_equal(full["d"][m], part["d"]) and np.allclose(full["sd"][m], part["sd"]), (name, cut)


def test_stops_en_rango():
    b5 = _b5(seed=12)
    for name, (fn, _, usa_oi) in SETUPS.items():
        if usa_oi: continue
        s = fn(b5); assert (s["sd"] > 0).all() and set(np.unique(s["d"])) <= {-1, 1}, name
