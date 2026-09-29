import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.miner.features import Market
from src.miner.strategy import random_genome, build_signals, ENTRY_TYPES, REGIMES, active, CHOICES


def synth(n=2500, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.008, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, n)))
    idx = pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c,
                         "volume": rng.uniform(100, 1000, n)}, index=idx)


def test_every_entry_and_regime_type_is_causal():
    df = synth()
    full = Market("1h", df=df, funding=np.zeros(len(df)))
    rng = random.Random(5)
    seen_e, seen_r = set(), set()
    genomes = []
    while len(seen_e) < len(ENTRY_TYPES) or len(seen_r) < len(REGIMES) or len(genomes) < 300:
        g = random_genome(rng); genomes.append(g); seen_e.add(g["entry"]); seen_r.add(g["regime"])
        if len(genomes) > 3000: break
    assert seen_e == set(ENTRY_TYPES) and seen_r == set(REGIMES)
    for g in genomes[:300]:
        e1, x1, s1 = build_signals(g, full)
        for m in (700, 1350, 2100):
            part = Market("1h", df=df.iloc[:m], funding=np.zeros(m))
            e2, x2, s2 = build_signals(g, part)
            assert np.array_equal(e1[:m], e2), (active(g), "entry")
            assert np.array_equal(x1[:m], x2), (active(g), "exit")
            assert np.allclose(s1[:m], s2, equal_nan=True), (active(g), "stop")
