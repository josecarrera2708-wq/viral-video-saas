"""Embudo de robustez F5. Una candidata solo sobrevive si pasa TODAS las pruebas.
Los umbrales están fijados de antemano (config/gates.json) y no se retocan tras ver resultados."""
from __future__ import annotations
import json, sys
from pathlib import Path
import multiprocessing as mp
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.engine import Params, run
from src.backtest.metrics import summarize
from src.miner.features import Market
from src.miner.ga import SPLITS
from src.miner.strategy import (CHOICES, active, build_signals, evaluate, genome_key,
                                stop_distance)
from src.robustness.stats import deflated_sharpe, monte_carlo, pbo_cscv, sharpe_pp

ROOT = Path(__file__).resolve().parents[2]
GATES = json.loads((ROOT / "config" / "gates.json").read_text())
SENS_GENES = ["fast", "slow", "don_n", "rsi_n", "rsi_lo", "rsi_hi", "bb_n", "bb_k", "reg_n", "vp_lo",
              "vp_hi", "atr_n", "atr_k", "swing_cap", "tp", "max_bars", "sw_k"]
MK: dict[str, Market] = {}
STRESS = dict(taker_fee=0.001, maker_fee=0.0004, slippage=0.0005, stress_range_frac=0.1, tp_pen=0.0005)


def rebuild(active_json: str) -> dict:
    g = {k: v[0] for k, v in CHOICES.items()}
    g.update(entry="ma_cross", regime="none")
    g.update(json.loads(active_json))
    if isinstance(g.get("macd"), list): g["macd"] = tuple(g["macd"])
    return g


def rng_of(tf, key):
    return MK[tf].index_range(*SPLITS[key])


def pre_blind(tf):
    a, _ = rng_of(tf, "train"); _, b = rng_of(tf, "validation"); return a, b


def daily(res, m, a, b):
    eq = pd.Series(res["equity"], index=m.df.index[a:b])
    return eq.resample("1D").last().pct_change().dropna()


def trade_frac(res):
    return res["pnl"] / np.where(res["risk"] > 0, res["risk"] / res["risk_frac_real"], np.nan)


def blocks_test(res, m, a):
    """Rentabilidad por trimestre con log(1+retorno por operación): sin sesgo hacia lo reciente."""
    if res["n_trades"] == 0: return 0.0, 1.0
    t = m.df.index[a + res["exit_idx"]]
    fr = trade_frac(res)
    s = pd.Series(np.log1p(np.where(np.isfinite(fr), fr, 0.0)), index=t)
    q = s.groupby([t.year, (t.month - 1) // 3]).sum()
    share = float((q > 0).mean())
    tot = q.sum()
    top = float(q.max() / tot) if tot > 0 else 1.0
    return share, top


def neighbors(g):
    out = []
    a = active(g)
    for k in SENS_GENES:
        if k in a and k in CHOICES and a[k] in CHOICES[k]:
            i = CHOICES[k].index(a[k])
            for j in (i - 1, i + 1):
                if 0 <= j < len(CHOICES[k]):
                    n = dict(g); n[k] = CHOICES[k][j]
                    if n["fast"] < n["slow"] or "fast" not in a: out.append(n)
    return out


def random_null(g, m, a, b, n_sims, seed=0):
    ent, ex, _ = build_signals(g, m)
    p = float((ent[a:b] != 0).mean()); rng = np.random.default_rng(seed)
    n = len(m.o); sh = []
    prm = Params(capital=1000.0, risk_frac=0.01, max_bars=g["max_bars"], tp_mult=g["tp"])
    for _ in range(n_sims):
        mask = rng.random(n) < p
        d = 1 if g["side"] == "long" else -1 if g["side"] == "short" else rng.choice([-1, 1], n)
        e = np.where(mask, d, 0).astype(np.int8)
        sd = stop_distance(g, m, e)
        x = e if g["exit_opp"] else np.zeros(n, np.int8)
        r = run(m.o[a:b], m.h[a:b], m.l[a:b], m.c[a:b], e[a:b], sd[a:b], prm, exit_sig=x[a:b], funding=m.funding[a:b])
        sh.append(summarize(r, m.tf)["sharpe"])
    return np.array(sh)


def analyze(args):
    key, aj, fit_train = args
    g = rebuild(aj); tf = g["tf"]; m = MK[tf]
    a0, b0 = rng_of(tf, "train"); av, bv = rng_of(tf, "validation"); ap, bp = pre_blind(tf)
    out = {"key": key, "tf": tf, "genome": aj, "fit_train": fit_train}
    tr = evaluate(g, m, a0, b0); va = evaluate(g, m, av, bv); pb = evaluate(g, m, ap, bp)
    out.update({f"train_{k}": v for k, v in tr.items() if k != "_res"})
    out.update({f"val_{k}": v for k, v in va.items() if k != "_res"})
    out.update({f"pre_{k}": v for k, v in pb.items() if k != "_res"})
    rv = va["_res"]
    # T2 validación (fuera de muestra)
    G = GATES["validation"]
    out["p_val"] = bool(va["trades"] >= G["min_trades_" + tf] and va["sharpe"] >= G["min_sharpe"] and
                        va["maxdd"] <= G["max_dd"] and va["pf"] >= G["min_pf"] and va["exp_r"] > 0)
    # T3 bloques trimestrales (solo validación)
    share, top = blocks_test(rv, m, av)
    out.update(blocks_pos=share, blocks_top=top)
    out["p_blocks"] = bool(share >= GATES["blocks"]["min_profitable_share"] and top <= GATES["blocks"]["max_top_share"])
    # T4 Monte Carlo sobre operaciones de validación
    fr = trade_frac(rv); fr = fr[np.isfinite(fr)]
    if len(fr) >= 20:
        p5, dd95, ploss = monte_carlo(fr, GATES["mc"]["sims"])
        p5s, _, _ = monte_carlo(fr, GATES["mc"]["sims"], seed=1, skip=0.10)
    else:
        p5, dd95, ploss, p5s = -1.0, 1.0, 1.0, -1.0
    out.update(mc_p5=p5, mc_dd95=dd95, mc_ploss=ploss, mc_p5_skip=p5s)
    out["p_mc"] = bool(p5 > 0 and dd95 <= GATES["mc"]["max_dd95"] and p5s > 0)
    # T5 sensibilidad de parámetros (validación)
    nb = neighbors(g); pos = []; shs = []
    for n in nb:
        r = evaluate(n, m, av, bv); pos.append(r["exp_r"] > 0 and r["ret"] > 0); shs.append(r["sharpe"])
    out["sens_n"] = len(nb)
    out["sens_pos"] = float(np.mean(pos)) if nb else 1.0
    out["sens_med_ratio"] = float(np.median(shs) / va["sharpe"]) if nb and va["sharpe"] > 0 else 0.0
    out["p_sens"] = bool(out["sens_pos"] >= GATES["sens"]["min_pos_share"] and
                         out["sens_med_ratio"] >= GATES["sens"]["min_median_ratio"])
    # T6 estrés de costes (validación)
    stress = evaluate(g, m, av, bv, Params(capital=1000.0, risk_frac=0.01, **STRESS))
    out.update(stress_ret=stress["ret"], stress_sharpe=stress["sharpe"])
    out["p_cost"] = bool(stress["ret"] > 0 and stress["exp_r"] > 0)
    # T7 frente a entradas aleatorias
    null = random_null(g, m, av, bv, GATES["random"]["sims"])
    out["null_p95"] = float(np.percentile(null, 95)); out["null_med"] = float(np.median(null))
    out["p_random"] = bool(va["sharpe"] > out["null_p95"])
    # retornos diarios para DSR y PBO (guardar como listas)
    out["_daily_val"] = daily(va["_res"], m, av, bv)
    out["_daily_pre"] = daily(pb["_res"], m, ap, bp)
    return out


def _init(markets):
    global MK; MK = markets


def select_candidates():
    files = sorted((ROOT / "data" / "mining").glob("trials_seed*.parquet"))
    df = pd.concat([pd.read_parquet(f) for f in files]).sort_values("fitness", ascending=False)
    n_total = df["key"].nunique()
    df = df.drop_duplicates("key")
    df = df[df.fitness > 0]
    return df, n_total


def run_funnel(k_max=150, corr_max=0.8, procs=4):
    global MK
    MK = {"1h": Market("1h"), "4h": Market("4h")}
    df, n_total = select_candidates()
    # 1) dedupe por correlación de retornos diarios en TRAIN (solo tramo de entrenamiento)
    kept, series = [], []
    for _, r in df.head(1200).iterrows():
        g = rebuild(r.genome); m = MK[g["tf"]]; a, b = rng_of(g["tf"], "train")
        res = evaluate(g, m, a, b)["_res"]
        d = daily(res, m, a, b)
        if len(d) < 200: continue
        if all(abs(d.corr(s)) < corr_max for s in series if s is not None and len(s) > 0):
            kept.append((r.key, r.genome, float(r.fitness))); series.append(d)
        if len(kept) >= k_max: break
    print(f"candidatas tras dedupe (|corr|<{corr_max}): {len(kept)} de {len(df)} con fitness>0; pruebas únicas totales: {n_total}", flush=True)
    ctx = mp.get_context("fork")
    with ctx.Pool(procs, initializer=_init, initargs=(MK,)) as pool:
        rows = pool.map(analyze, kept, chunksize=2)
    # DSR con K candidatas evaluadas en validación
    K = len(rows)
    val_sr = np.array([sharpe_pp(r["_daily_val"].to_numpy()) if len(r["_daily_val"]) > 30 else 0.0 for r in rows])
    var_sr = float(val_sr.var(ddof=1))
    for r, s in zip(rows, val_sr):
        r["dsr_val"] = deflated_sharpe(r["_daily_val"].to_numpy(), K, var_sr) if len(r["_daily_val"]) > 30 else 0.0
        r["p_dsr"] = bool(r["dsr_val"] >= GATES["dsr"]["min"])
    # PBO global sobre retornos diarios pre-ciego
    idx = sorted(set().union(*[set(r["_daily_pre"].index) for r in rows]))
    M = np.column_stack([r["_daily_pre"].reindex(idx).fillna(0.0).to_numpy() for r in rows])
    pbo_pre = pbo_cscv(M, s=16)                      # informativo: sesgado por la preselección
    iv = sorted(set().union(*[set(r["_daily_val"].index) for r in rows]))
    Mv = np.column_stack([r["_daily_val"].reindex(iv).fillna(0.0).to_numpy() for r in rows])
    pbo = pbo_cscv(Mv, s=8)                          # el que se usa: solo fuera de muestra
    for r in rows:
        r["p_pbo"] = bool(pbo <= GATES["pbo"]["max"])
        r.pop("_daily_val"); r.pop("_daily_pre")
    res = pd.DataFrame(rows)
    flags = [c for c in res.columns if c.startswith("p_")]
    res["n_pass"] = res[flags].sum(axis=1); res["survivor"] = res[flags].all(axis=1)
    out = ROOT / "reports" / "funnel_results.parquet"
    res.to_parquet(out, index=False)
    summary = {"pruebas_unicas_totales": int(n_total), "candidatas_analizadas": int(K),
               "pbo_validacion": pbo, "pbo_pre_ciego_informativo": pbo_pre, "var_sr_val": var_sr,
               "pasan_por_prueba": {c: int(res[c].sum()) for c in flags},
               "supervivientes": int(res.survivor.sum())}
    (ROOT / "reports" / "funnel_summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1), flush=True)
    return res, summary


if __name__ == "__main__":
    run_funnel()
