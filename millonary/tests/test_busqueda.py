import numpy as np
import pandas as pd
from src.busqueda.setups import variants
from src.busqueda import evaluate as ev


def _synth(n=3000, seed=0, freq="1h"):
    rng = np.random.default_rng(seed); c = 30000 * np.exp(np.cumsum(rng.normal(0, 0.006, n)))
    o = np.r_[c[0], c[:-1]]; h = np.maximum(o, c) * (1 + rng.uniform(0, 0.004, n)); l = np.minimum(o, c) * (1 - rng.uniform(0, 0.004, n))
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=pd.date_range("2020-01-01", periods=n, freq=freq, tz="UTC"))


def test_causal_truncation():
    df = _synth(); cut = 2000; d2 = df.copy(); d2.iloc[cut + 1:, :4] *= 1.37
    a, b = variants(df, "1h"), variants(d2, "1h")
    assert len(a) == 192
    for k in a:
        assert np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]), k
        assert np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True), k


def test_pipeline_synthetic(monkeypatch):
    df = _synth(60000, 1)
    monkeypatch.setattr(ev, "PER", {"1h": {"construccion": ("2020-03-01", "2023-01-01"), "validacion": ("2023-01-01", "2025-01-01"), "examen": ("2025-01-01", "2026-09-01")}})
    o = ev.evaluate(write=False, tfs=("1h",), loader=lambda tf: (df, np.zeros(len(df))))
    assert o["n_variantes"] == 192 and len(o["finalistas"]) <= ev.N_FINAL
