import numpy as np, pandas as pd
from src.desk1h.setups import all_specs
from src.desk1h.data import to_1h


def _bars(n=6000, seed=1):
    r = np.random.default_rng(seed); c = 20000 * np.exp(np.cumsum(r.normal(0, 0.004, n))); o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + abs(r.normal(0, 0.002, n))); l = np.minimum(o, c) * (1 - abs(r.normal(0, 0.002, n)))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": r.uniform(1, 9, n)}, index=pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC"))


def test_truncation_13_setups():
    df = _bars(); d2 = df.copy(); cut = 4000; d2.iloc[cut + 1:, :4] *= 1.37; a, b = all_specs(df), all_specs(d2)
    assert len(a) == 13
    for k in a:
        assert np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]), k
        assert np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True), k


def test_stops_valid_and_signals_exist():
    df = _bars(); n_sig = 0
    for k, sp in all_specs(df).items():
        e = sp.entry != 0; n_sig += int(e.sum())
        assert (np.nan_to_num(sp.stop[e], nan=0) > 0).all(), k
    assert n_sig > 50


def test_resample_needs_four_bars_and_sums_funding():
    i = pd.date_range("2026-01-01", periods=10, freq="15min", tz="UTC"); b = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1.0}, index=i)
    o, f = to_1h(b, np.full(10, 0.25)); assert len(o) == 2 and np.allclose(f, 1.0) and o["volume"].iloc[0] == 4
