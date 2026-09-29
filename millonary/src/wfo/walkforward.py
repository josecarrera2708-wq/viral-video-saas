"""Walk-forward del PROCESO completo: minar -> elegir -> operar en datos posteriores.

Para cada ventana T (cada 6 meses):
  1) el minero solo ve datos [2020-01-01, T)  (mercado TRUNCADO físicamente);
  2) se eligen las mejores M por fitness de entrenamiento (descorrelacionadas, solo con train);
  3) se opera cada una en [T, T+6m) (fuera de muestra) con costes reales.
La cartera equiponderada de las M concatena 3,5 años fuera de muestra. Se compara con:
  - nulo A: M estrategias ALEATORIAS elegibles (sin minar);
  - nulo B: M estrategias al azar entre las que el minero encontró con fitness>0 (aísla el valor del ranking);
  - comprar y mantener BTC.
El periodo ciego (>= 2025-07-01) NO se toca aquí.
"""
from __future__ import annotations
import json, random, sys, time
from pathlib import Path
import multiprocessing as mp
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.miner.features import Market
from src.miner.ga import Miner
from src.miner.strategy import random_genome, evaluate, genome_key
from src.robustness.funnel import daily
from src.robustness.stats import deflated_sharpe, sharpe_pp

ROOT = Path(__file__).resolve().parents[2]
START = "2020-01-01"
EDGES = ["2022-01-01", "2022-07-01", "2023-01-01", "2023-07-01", "2024-01-01", "2024-07-01",
         "2025-01-01", "2025-07-01"]                      # el último borde = inicio del ciego
M_MAX = 20
ISLANDS, POP, GENS = 4, 300, 15
N_NULL = 300
MK: dict = {}


def min_trades(tf): return 150 if tf == "1h" else 100


def fold_job(k: int) -> dict:
    T, END = EDGES[k], EDGES[k + 1]
    t0 = time.time()
    # 1) minado solo con datos < T
    trials, n_unique = {}, 0
    miners = []
    for seed in range(ISLANDS):
        mi = Miner(MK, ROOT / "data" / "wfo", seed=1000 * k + seed, train=(START, T)).run(POP, GENS, log=False)
        miners.append(mi)
        for key, t in mi.trials.items():
            if key not in trials or t["fitness"] > trials[key]["fitness"]:
                trials[key] = t
    n_unique = len(trials)
    mtr = miners[0].mk
    pos = sorted([t for t in trials.values() if t["fitness"] > 0], key=lambda t: -t["fitness"])
    # 2) dedupe por correlación de retornos diarios en TRAIN y selección top M_MAX
    kept, series = [], []
    for t in pos[:600]:
        g = t["_g"]; tf = g["tf"]; a, b = miners[0].rng_range[tf]
        d = daily(evaluate(g, mtr[tf], a, b)["_res"], mtr[tf], a, b)
        if len(d) < 200: continue
        if all(abs(d.corr(s)) < 0.8 for s in series):
            kept.append(t); series.append(d)
        if len(kept) >= M_MAX: break
    # 3) operar fuera de muestra
    def oos(g):
        m = MK[g["tf"]]; a, b = m.index_range(T, END)
        r = evaluate(g, m, a, b)
        return daily(r["_res"], m, a, b), r["trades"], r["sharpe"]
    mined = []
    for t in kept:
        d, nt, sh = oos(t["_g"]); mined.append({"key": t["key"], "fit": t["fitness"], "oos_daily": d, "oos_trades": nt})
    # nulo B: al azar entre las halladas con fitness>0
    rng = random.Random(7 + k)
    poolB = rng.sample(pos, min(N_NULL, len(pos)))
    nullB = [oos(t["_g"])[0] for t in poolB]
    # nulo A: aleatorias elegibles (mismos mínimos de operaciones y sin ruina en train, sin filtrar por rentabilidad)
    nullA = []
    while len(nullA) < N_NULL:
        g = random_genome(rng); tf = g["tf"]; a, b = miners[0].rng_range[tf]
        r = evaluate(g, mtr[tf], a, b)
        if r["trades"] < min_trades(tf) or r["ruined"]: continue
        nullA.append(oos(g)[0])
    return {"k": k, "T": T, "END": END, "n_unique": n_unique, "n_pos": len(pos), "n_kept": len(kept),
            "mined": mined, "nullA": nullA, "nullB": nullB, "secs": time.time() - t0}


def port(daily_list) -> pd.Series:
    df = pd.concat(daily_list, axis=1).fillna(0.0)
    return df.mean(axis=1)


def stats(r: pd.Series) -> dict:
    r = r.dropna(); n = len(r)
    eq = (1 + r).cumprod()
    dd = float((1 - eq / eq.cummax()).max())
    sd = r.std(ddof=1)
    return {"days": n, "sharpe": float(r.mean() / sd * np.sqrt(365)) if sd > 0 else 0.0,
            "total_ret": float(eq.iloc[-1] - 1), "maxdd": dd,
            "cagr": float(eq.iloc[-1] ** (365 / n) - 1) if n > 0 and eq.iloc[-1] > 0 else -1.0}


def aggregate(folds: list[dict]) -> dict:
    out = {"folds": [{k: f[k] for k in ("T", "END", "n_unique", "n_pos", "n_kept", "secs")} for f in folds]}
    rng = np.random.default_rng(0)
    variants = {}
    for M in (5, 10, 20):
        parts = [port([c["oos_daily"] for c in f["mined"][:M]]) for f in folds if f["mined"]]
        variants[M] = pd.concat(parts)
    out["mined"] = {f"M{M}": stats(v) for M, v in variants.items()}
    # por ventana (M=10)
    out["por_ventana_M10"] = [{"T": f["T"], "ret": float((1 + port([c["oos_daily"] for c in f["mined"][:10]])).prod() - 1)}
                              for f in folds if f["mined"]]
    # comprar y mantener
    d = pd.read_parquet(ROOT / "data" / "raw" / "perp_BTCUSDT_1h.parquet").set_index("time")["close"]
    bh = d.resample("1D").last().pct_change().dropna()
    bh = bh[(bh.index >= pd.Timestamp(EDGES[0], tz="UTC")) & (bh.index < pd.Timestamp(EDGES[-1], tz="UTC"))]
    out["buy_hold"] = stats(bh)
    # nulos: distribución del Sharpe de carteras de M=10 elegidas al azar en cada ventana
    def null_dist(key, M=10, reps=300):
        res = []
        for _ in range(reps):
            parts = []
            for f in folds:
                pool = f[key]; idx = rng.choice(len(pool), size=min(M, len(pool)), replace=False)
                parts.append(port([pool[i] for i in idx]))
            res.append(stats(pd.concat(parts)))
        return res
    for key in ("nullA", "nullB"):
        nd = null_dist(key)
        sh = np.array([x["sharpe"] for x in nd]); rt = np.array([x["total_ret"] for x in nd])
        m10 = out["mined"]["M10"]["sharpe"]
        out[key] = {"sharpe_mediana": float(np.median(sh)), "sharpe_p95": float(np.percentile(sh, 95)),
                    "ret_mediana": float(np.median(rt)), "pct_null_sharpe_above_mined": float((sh >= m10).mean())}
    # DSR del proceso: N = 3 variantes (M=5,10,20) probadas
    srs = np.array([sharpe_pp(variants[M].to_numpy()) for M in (5, 10, 20)])
    var_sr = float(srs.var(ddof=1)) if srs.var(ddof=1) > 0 else 1e-6
    for M in (5, 10, 20):
        out["mined"][f"M{M}"]["dsr_N3"] = deflated_sharpe(variants[M].to_numpy(), 3, var_sr)
    return out


if __name__ == "__main__":
    MK.update({"1h": Market("1h"), "4h": Market("4h")})
    folds_idx = list(range(len(EDGES) - 1))
    ctx = mp.get_context("fork")
    with ctx.Pool(4) as pool:
        folds = pool.map(fold_job, folds_idx, chunksize=1)
    for f in folds:
        print(f"ventana {f['T']}→{f['END']}: {f['n_unique']} pruebas únicas, {f['n_pos']} con fitness>0, "
              f"{f['n_kept']} elegidas, {f['secs']:.0f}s", flush=True)
    res = aggregate(folds)
    (ROOT / "reports" / "wfo_results.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "folds"}, indent=1, default=str))
