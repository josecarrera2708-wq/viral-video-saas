"""Evaluación de la incubadora (config/incubadora_prerregistrada.md). Ejecución del EXAMEN: una sola vez.

Salida: reports/incubadora_resultados.json y reports/incubadora_resultados.md
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.funding import align_funding
from src.core.evaluate_nucleo import load_spot, funding_events, DELTA
from src.core.nucleo import CoreParams, run_core
from src.robustness.stats import deflated_sharpe, pbo_cscv, sharpe_pp
from src.incubator.setups import all_states
from src.incubator.sim import simulate, trades, daily
from src.incubator.factors import trend_factor, regress, holm, benjamini_hochberg

ROOT = Path(__file__).resolve().parents[2]
START = pd.Timestamp("2020-01-01", tz="UTC"); TRAIN_END = pd.Timestamp("2024-01-01", tz="UTC")
N_PRIOR = 23; N_NEW = 15


def ann_sharpe(d: pd.Series) -> float:
    sd = d.std(ddof=1)
    return float(d.mean() / sd * np.sqrt(365)) if len(d) > 5 and sd > 0 else 0.0


def build(df: pd.DataFrame, funding: np.ndarray):
    S = all_states(df); res = {}
    for k in S:
        res[k] = simulate(df, S[k].to_numpy(), funding)
    return S, res


def run(write: bool = True) -> dict:
    df, _ = load_spot()
    df = df[df.index >= pd.Timestamp("2019-01-01", tz="UTC")]           # calentamiento de indicadores
    f = align_funding(df.index, DELTA, funding_events(df.index))
    S, res = build(df, f)
    S2, res2 = {}, {}
    for k in S:
        res2[k] = simulate(df, S[k].to_numpy(), f, cost=0.0014)         # costes x2
    btc_d = df["close"].resample("1D").last(); btc_r = btc_d.pct_change(); tf = trend_factor(btc_d)
    ds = {k: daily(v["ret"]) for k, v in res.items()}
    ds2 = {k: daily(v["ret"]) for k, v in res2.items()}
    tr = lambda s: s[(s.index >= START) & (s.index < TRAIN_END)]
    ex = lambda s: s[s.index >= TRAIN_END]
    full = lambda s: s[s.index >= START]
    rows = {}
    for k in S:
        t = trades(res[k]); t_full = t[t["open"] >= START]
        reg = regress(ex(ds[k]), ex(btc_r), ex(tf)); reg_tr = regress(tr(ds[k]), tr(btc_r), tr(tf))
        rows[k] = {"sharpe_train": ann_sharpe(tr(ds[k])), "sharpe_exam": ann_sharpe(ex(ds[k])),
                   "sharpe_exam_cost2x": ann_sharpe(ex(ds2[k])), "sharpe_full": ann_sharpe(full(ds[k])),
                   "retorno_anual_full": float(full(ds[k]).mean() * 365), "caida_max_exam": float((1 - (1 + ex(ds[k])).cumprod() / (1 + ex(ds[k])).cumprod().cummax()).max()),
                   "n_ops": int(len(t_full)), "win_rate": float((t_full["ret"] > 0).mean()) if len(t_full) else float("nan"),
                   "exam": reg, "train": reg_tr, "expo_media": float(res[k]["pos"].abs().mean()),
                   "rotacion_anual": float(res[k]["turn"].sum() / ((df.index[-1] - df.index[0]).days / 365.25))}
    names = list(rows)
    p = np.array([rows[k]["exam"]["p_alpha_1s"] for k in names]); p = np.where(np.isnan(p), 1.0, p)
    ph, pb = holm(p), benjamini_hochberg(p)
    Rfull = pd.concat([full(ds[k]).rename(k) for k in names], axis=1).dropna()
    pbo = pbo_cscv(Rfull.to_numpy(), s=16)
    var_sr = float(np.var([sharpe_pp(Rfull[k].to_numpy()) for k in names], ddof=1))
    for i, k in enumerate(names):
        r = rows[k]; r["p_holm"] = float(ph[i]); r["p_bh"] = float(pb[i])
        r["dsr"] = float(deflated_sharpe(full(ds[k]).to_numpy(), N_PRIOR + N_NEW, var_sr))
        gates = {"P1 train Sharpe>0": r["sharpe_train"] > 0, "P2 exam Sharpe>0": r["sharpe_exam"] > 0,
                 "P3 alfa exam Holm<0.10": r["p_holm"] < 0.10, "P4 DSR>=0.80": r["dsr"] >= 0.80,
                 "P5 >=30 ops": r["n_ops"] >= 30, "P6 exam Sharpe>0 costes x2": r["sharpe_exam_cost2x"] > 0,
                 "P7 PBO<0.5": bool(pbo < 0.5)}
        r["puertas"] = {a: bool(b) for a, b in gates.items()}; r["certificada"] = all(gates.values())
    # referencia: núcleo v1 en el mismo examen (no compite; se muestra para contexto)
    core = run_core(df, f, CoreParams()); ce = daily(core["equity"].pct_change().fillna(0))
    ref = {"sharpe_train": ann_sharpe(tr(ce)), "sharpe_exam": ann_sharpe(ex(ce)), "sharpe_full": ann_sharpe(full(ce))}
    bh = {"sharpe_exam": ann_sharpe(ex(btc_r.dropna())), "sharpe_full": ann_sharpe(full(btc_r.dropna()))}
    out = {"periodos": {"train": ["2020-01-01", "2023-12-31"], "exam": ["2024-01-01", "2025-06-30"]},
           "pbo_conjunto": float(pbo), "n_setups": len(names), "referencia_nucleo": ref, "referencia_buy_hold": bh,
           "setups": rows, "certificadas": [k for k in names if rows[k]["certificada"]]}
    if write:
        (ROOT / "reports" / "incubadora_resultados.json").write_text(json.dumps(out, indent=1, default=float))
        (ROOT / "reports" / "incubadora_resultados.md").write_text(_md(out))
    return out


def _md(o: dict) -> str:
    L = ["# Incubadora de traders · Resultados (ejecución única del examen 2024-01 → 2025-06)", "",
         f"PBO del conjunto (CSCV, 15 series): **{o['pbo_conjunto']:.2f}** · Certificadas: **{len(o['certificadas'])}/{o['n_setups']}**",
         f"Referencia núcleo v1: Sharpe train {o['referencia_nucleo']['sharpe_train']:.2f} / exam {o['referencia_nucleo']['sharpe_exam']:.2f}; buy&hold exam {o['referencia_buy_hold']['sharpe_exam']:.2f}", "",
         "| Trader | Sh train | Sh exam | Sh exam ×2 coste | α exam (anual) | t | β BTC | β tend | p Holm | DSR | ops | Puertas | Cert. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["setups"].items():
        e = r["exam"]; ok = sum(r["puertas"].values())
        L.append(f"| {k} | {r['sharpe_train']:.2f} | {r['sharpe_exam']:.2f} | {r['sharpe_exam_cost2x']:.2f} | {100*e['alpha_anual']:.0f}% | {e['t_alpha']:.2f} | {e['beta_btc']:.2f} | {e['beta_tend']:.2f} | {r['p_holm']:.2f} | {r['dsr']:.2f} | {r['n_ops']} | {ok}/7 | {'✔' if r['certificada'] else '—'} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = run()
    print(_md(o))
