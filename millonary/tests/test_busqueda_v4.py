import numpy as np
import pandas as pd
from src.busqueda.v4 import variants


def _df(n, freq):
    rng = np.random.default_rng(3); idx = pd.date_range("2020-01-01", periods=n, freq=freq, tz="UTC")
    c = 30000 * np.exp(np.cumsum(rng.normal(0, 0.012, n))); o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.006, n)); l = np.minimum(o, c) * (1 - rng.uniform(0, 0.006, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": rng.uniform(1, 10, n)}, index=idx)


def test_truncation_causal():
    for tf, n, freq in (("4h", 1500, "4h"), ("1d", 900, "1D")):
        df = _df(n, freq); full = variants(df, tf)
        for cut in (n - 1, n - 4, n - 37):
            part = variants(df.iloc[:cut], tf)
            for k in full:
                assert np.array_equal(full[k].entry[:cut], part[k].entry), (k, cut)
                assert np.allclose(full[k].stop[:cut], part[k].stop, equal_nan=True), (k, cut)


def test_counts_and_signals():
    df = _df(1500, "4h"); v = variants(df, "4h"); assert len(v) == 136
    assert sum(int((s.entry != 0).sum()) > 0 for s in v.values()) > 100
