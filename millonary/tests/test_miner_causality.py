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


def test_exit_on_opposite_signal_works_for_single_side_strategies():
    """Revisión Opus #4: exit_opp no hacía nada en estrategias solo largos/cortos."""
    df = synth(); m = Market("1h", df=df, funding=np.zeros(len(df)))
    g = {k: v[0] for k, v in CHOICES.items()}
    g.update(entry="ma_cross", regime="none", fast=10, slow=50, side="long", exit_opp=True)
    ent, ex, _ = build_signals(g, m)
    assert (ex == -1).any()                                        # emite salida bajista aunque solo opere largos
    assert not (ent == -1).any()


def test_redundant_genes_collapse_to_same_key():
    from src.miner.strategy import genome_key
    base = {k: v[0] for k, v in CHOICES.items()}
    base.update(entry="ma_cross", fast=10, slow=50, side="both")
    a = dict(base, regime="ma_pair"); b = dict(base, regime="none")
    assert genome_key(a) == genome_key(b)
    c = dict(base, regime="volpct", vp_lo=0.0, vp_hi=1.0)
    assert genome_key(c) == genome_key(b)


def test_mutation_stays_on_grid_and_fast_below_slow():
    from src.miner.ga import Miner
    df = synth(); mk = {"1h": Market("1h", df=df, funding=np.zeros(len(df)))}
    m = Miner(mk, pathlib.Path("/tmp/_m"), seed=1, train=("2022-01-01", "2022-03-01"))
    rng = random.Random(0)
    for _ in range(500):
        g = m._mutate(random_genome(rng), rate=0.6)
        assert g["fast"] in CHOICES["fast"] and g["slow"] in CHOICES["slow"] and g["fast"] < g["slow"]


def test_truncated_market_cannot_see_the_future_and_matches_prefix():
    df = synth(); full = Market("1h", df=df, funding=np.zeros(len(df)))
    cut = str(df.index[1500])[:10]
    tr = full.truncate(cut)
    assert tr.df.index[-1] < pd.Timestamp(cut, tz="UTC")
    g = random_genome(random.Random(3))
    e1, _, _ = build_signals(g, full); e2, _, _ = build_signals(g, tr)
    assert np.array_equal(e1[:tr.n], e2)
