import sys, pathlib, random
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.miner.features import Market
from src.miner.strategy import random_genome, build_signals, ENTRY_TYPES, REGIMES, active, CHOICES, fix_grid


def synth(n=2500, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.008, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, n)))
    idx = pd.date_range("2022-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c,
                         "volume": rng.uniform(100, 1000, n)}, index=idx)


def synth_extra(df, seed=1):
    rng = np.random.default_rng(seed); n = len(df)
    ex = pd.DataFrame(index=df.index)
    ex["funding"] = rng.normal(1e-4, 5e-4, n); ex["premium"] = rng.normal(0, 1e-3, n)
    ex["oi_value"] = 3e9 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    for c in ("ls_top_acc", "ls_top_pos", "ls_all", "taker_ls"): ex[c] = rng.uniform(0.5, 2, n)
    ex["fng"] = np.clip(50 + np.cumsum(rng.normal(0, 3, n)) % 100, 0, 100)
    ex["vix"] = 15 + np.abs(np.cumsum(rng.normal(0, 0.3, n)) % 30)
    ex["y10"] = 3 + rng.normal(0, 0.1, n); ex["y2"] = 3 + rng.normal(0, 0.1, n)
    ex["usd"] = 120 + np.cumsum(rng.normal(0, 0.05, n))
    return ex


def test_every_entry_and_regime_type_is_causal():
    df = synth(); ex = synth_extra(df)
    full = Market("1h", df=df, funding=np.zeros(len(df)), extra=ex)
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
            part = Market("1h", df=df.iloc[:m], funding=np.zeros(m), extra=ex.iloc[:m])
            e2, x2, s2 = build_signals(g, part)
            assert np.array_equal(e1[:m], e2), (active(g), "entry")
            assert np.array_equal(x1[:m], x2), (active(g), "exit")
            assert np.allclose(s1[:m], s2, equal_nan=True), (active(g), "stop")


def test_exit_on_opposite_signal_works_for_single_side_strategies():
    """Revisión Opus #4: exit_opp no hacía nada en estrategias solo largos/cortos."""
    df = synth(); m = Market("1h", df=df, funding=np.zeros(len(df)))
    g = {k: v[0] for k, v in CHOICES.items()}
    g.update(entry="ma_cross", regime="none", regime2="none", fast=10, slow=50, side="long", exit_opp=True)
    ent, ex, _ = build_signals(g, m)
    assert (ex == -1).any()                                        # emite salida bajista aunque solo opere largos
    assert not (ent == -1).any()


def test_redundant_genes_collapse_to_same_key():
    from src.miner.strategy import genome_key
    base = {k: v[0] for k, v in CHOICES.items()}
    base.update(entry="ma_cross", fast=10, slow=50, side="both", regime2="none")
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
    df = synth(); full = Market("1h", df=df, funding=np.zeros(len(df)), extra=synth_extra(df))
    cut = str(df.index[1500])[:10]
    tr = full.truncate(cut)
    assert tr.df.index[-1] < pd.Timestamp(cut, tz="UTC")
    g = random_genome(random.Random(3))
    e1, _, _ = build_signals(g, full); e2, _, _ = build_signals(g, tr)
    assert np.array_equal(e1[:tr.n], e2)


def test_each_entry_and_each_regime_explicitly_causal():
    df = synth(); ex = synth_extra(df)
    full = Market("1h", df=df, funding=np.zeros(len(df)), extra=ex)
    rng = random.Random(11)
    genomes = []
    for e in ENTRY_TYPES:                                   # cada entrada, con filtros aleatorios
        for _ in range(4):
            g = random_genome(rng); g["entry"] = e; genomes.append(fix_grid(g))
    for r in REGIMES:                                       # cada filtro, en cada hueco, con entradas variadas
        for slot in ("regime", "regime2"):
            g = random_genome(rng); g[slot] = r; genomes.append(fix_grid(g))
    assert {g["entry"] for g in genomes} >= set(ENTRY_TYPES)
    for g in genomes:
        e1, x1, s1 = build_signals(g, full)
        for m in (900, 1700):
            part = Market("1h", df=df.iloc[:m], funding=np.zeros(m), extra=ex.iloc[:m])
            e2, x2, s2 = build_signals(g, part)
            assert np.array_equal(e1[:m], e2), (active(g), "entry")
            assert np.array_equal(x1[:m], x2), (active(g), "exit")
            assert np.allclose(s1[:m], s2, equal_nan=True), (active(g), "stop")


def test_new_price_action_entries_hand_examples():
    idx = pd.date_range("2024-01-01", periods=12, freq="4h", tz="UTC")
    o = np.full(12, 100.0)
    base = pd.DataFrame({"open": o, "high": o + 3, "low": o - 3, "close": o, "volume": 1.0}, index=idx)
    # barra madre en 4 (rango amplio), barra interior en 5, ruptura alcista en 6
    base.loc[idx[4], ["high", "low"]] = [110, 90]
    base.loc[idx[5], ["high", "low"]] = [104, 96]
    base.loc[idx[6], ["open", "high", "low", "close"]] = [100, 108, 99, 106]
    m = Market("4h", df=base, funding=np.zeros(12))
    g = {k: v[0] for k, v in CHOICES.items()}; g.update(entry="inside_break", regime="none", regime2="none")
    ent, _, _ = build_signals(g, m)
    assert ent[6] == 1 and ent[5] == 0
