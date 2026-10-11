import numpy as np
import pandas as pd
from src.busqueda.v3 import variants


def _df(n, freq):
    rng = np.random.default_rng(1); idx = pd.date_range("2020-01-01", periods=n, freq=freq, tz="UTC")
    c = 30000 * np.exp(np.cumsum(rng.normal(0, 0.01, n))); o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + rng.uniform(0, 0.005, n)); l = np.minimum(o, c) * (1 - rng.uniform(0, 0.005, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": rng.uniform(1, 10, n)}, index=idx)


def test_truncation_causal():
    """Las señales hasta la vela t no cambian al añadir velas posteriores."""
    for tf, n, freq in (("1h", 24 * 60, "1h"), ("4h", 1200, "4h"), ("1d", 900, "1D")):
        df = _df(n, freq); full = variants(df, tf); cut = n - 37; part = variants(df.iloc[:cut], tf)
        assert len(full) > 0
        for k in full:
            a, b = full[k], part[k]
            assert np.array_equal(a.entry[:cut], b.entry), k
            assert np.allclose(np.nan_to_num(a.stop[:cut]), np.nan_to_num(b.stop)), k
            if a.exit is not None:
                assert np.array_equal(a.exit[:cut], b.exit), k


def test_count():
    assert sum(len(variants(_df(n, f), tf)) for tf, n, f in (("1h", 24 * 60, "1h"), ("4h", 1200, "4h"), ("1d", 900, "1D"))) == 28
