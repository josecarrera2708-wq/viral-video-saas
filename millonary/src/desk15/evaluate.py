"""Evaluación histórica de la mesa de 15 min (una sola ejecución; prerregistro en config/mesa15_prerregistrada.md).

  python -m src.desk15.evaluate
Para cada trader: base (B), aprendiz individual (A) y aprendiz colectivo (C), en construcción / validación / examen sellado.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from ..backtest.engine import Params, run
from ..intraday.evaluate import summarize, stress, mc_band, run_period
from ..incubator.factors import holm
from .data import ROOT, load_history
from .setups import all_specs
from .learner import context15, base_trades, gate, N_MIN

PERIODS = {"construccion": ("2022-06-01", "2024-07-01"), "validacion": ("2024-07-01", "2025-10-01"), "examen": ("2025-10-01", "2026-09-29")}


def _days(a, b):
    return (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days


def build_variants(df: pd.DataFrame, f: np.ndarray, specs: dict | None = None, specs_fn=all_specs, ctx_fn=context15) -> tuple[dict, dict]:
    """Base + aprendices A y C de cada trader sobre TODO el histórico (causales). Devuelve (specs_por_variante, trades_base)."""
    specs = specs or specs_fn(df); ctx = ctx_fn(df); p = Params(); tb = {}
    for k, sp in specs.items():
        r = run(df["open"], df["high"], df["low"], df["close"], sp.entry, np.nan_to_num(sp.stop, nan=0.0), Params(tp_mult=sp.tp_mult, max_bars=sp.max_bars),
                exit_sig=sp.exit, funding=f)
        tb[k] = base_trades(r, df, ctx)
    pooled = [t for v in tb.values() for t in v]
    out = {}
    for k, sp in specs.items():
        out[f"{k}"] = sp
        out[f"{k} · A"], _ = gate(sp, df, ctx, tb[k], N_MIN["A"])
        out[f"{k} · C"], _ = gate(sp, df, ctx, pooled, N_MIN["C"])
    return out, tb


def truncation_ok(df: pd.DataFrame, cut: int = 60000, specs_fn=all_specs) -> dict:
    d2 = df.copy(); cols = d2.columns.get_indexer(["open", "high", "low", "close"]); d2.iloc[cut + 1:, cols] *= 1.37
    a, b = specs_fn(df), specs_fn(d2)
    return {k: bool(np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]) and np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True)) for k in a}


def evaluate(write: bool = True, desk: dict | None = None) -> dict:
    dk = {"name": "mesa15", "titulo": "Mesa de 15 min", "specs": all_specs, "ctx": context15, "load": load_history, "cut": 60000} | (desk or {})
    df, f = dk["load"](); df = df[df.index < pd.Timestamp("2026-09-29", tz="UTC")]; f = f[: len(df)]
    variants, _ = build_variants(df, f, specs_fn=dk["specs"], ctx_fn=dk["ctx"]); trunc = truncation_ok(df, dk["cut"], dk["specs"]); rows = {}
    for name, sp in variants.items():
        base = name.split(" · ")[0]; r = rows[name] = {"periodos": {}, "costes": {}, "truncamiento_ok": trunc[base]}
        for per, (a, b) in PERIODS.items():
            r["periodos"][per] = summarize(run_period(df, f, sp, a, b, Params()), _days(a, b))
        a, b = PERIODS["examen"]
        for m in (1.5, 2.0, 3.0):
            r["costes"][f"x{m}"] = summarize(run_period(df, f, sp, a, b, stress(m)), _days(a, b))
        rx = run_period(df, f, sp, a, b, Params())["r"]; r["montecarlo_examen"] = mc_band(np.asarray(rx["r"], float)[: int(rx["n_trades"])])
    names = [k for k in rows if " · " not in k]; p = np.array([rows[k]["periodos"]["examen"]["p_1s"] for k in names]); ph = holm(p)
    for i, k in enumerate(names):
        r = rows[k]; ex, va, c2 = r["periodos"]["examen"], r["periodos"]["validacion"], r["costes"]["x2.0"]; r["p_holm"] = float(ph[i])
        g = {"Q1 ≥0,3 ops/día": ex["por_dia"] >= 0.3, "Q2 R>0 validación y examen": va["R_media"] > 0 and ex["R_media"] > 0, "Q3 p Holm<0,10 (examen)": r["p_holm"] < 0.10,
             "Q4 R>0 con costes ×2": c2["R_media"] > 0, "Q5 truncamiento": r["truncamiento_ok"], "Q6 sin liquidación y caída<40 %": (not ex["liquidado"]) and ex["caida_max"] < 0.40, "Q7 Sharpe<6": ex["sharpe"] < 6}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
        for tag in ("A", "C"):
            v = rows[f"{k} · {tag}"]; va2, ex2 = v["periodos"]["validacion"], v["periodos"]["examen"]
            v["mejora_a_base"] = bool(va2["n"] >= 30 and ex2["n"] >= 30 and va2["R_media"] > va["R_media"] and ex2["R_media"] > ex["R_media"])
    out = {"periodos": PERIODS, "n_setups": len(names), "certificadas": [k for k in names if rows[k]["certificada"]], "aprendices_que_mejoran": [k for k in rows if rows[k].get("mejora_a_base")], "setups": rows}
    if write:
        (ROOT / "reports" / f"{dk['name']}_resultados.json").write_text(json.dumps(out, indent=1, default=float)); (ROOT / "reports" / f"{dk['name']}_resultados.md").write_text(md(out, dk["titulo"]))
    return out


def md(o: dict, titulo: str = "Mesa de 15 min") -> str:
    L = [f"# {titulo} · Resultados históricos (examen sellado 2025-10 → 2026-09, ejecución única)", "",
         f"Certificadas: **{len(o['certificadas'])}/{o['n_setups']}** · Aprendices que mejoran a su base (validación y examen, ≥30 ops): **{len(o['aprendices_que_mejoran'])}** · Costes reales del motor, 1.000 USDT por trader, riesgo 0,5 %.", "",
         "| Variante | Ops/día | Acierto | R constr. | R valid. | R examen | t | Retorno examen | Caída | R ×2 costes | p Holm | Puertas | Cert. / Mejora |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["setups"].items():
        c, v, e = r["periodos"]["construccion"], r["periodos"]["validacion"], r["periodos"]["examen"]; base = " · " not in k
        L.append(f"| {k} | {e['por_dia']:.2f} | {e['acierto']:.0%} | {c['R_media']:+.3f} | {v['R_media']:+.3f} | {e['R_media']:+.3f} | {e['t_R']:.1f} | {e['retorno']:+.1%} | {e['caida_max']:.0%} | {r['costes']['x2.0']['R_media']:+.3f} | "
                 + (f"{r['p_holm']:.2f} | {sum(r['puertas'].values())}/7 | {'✔' if r['certificada'] else '—'} |" if base else f"— | — | {'mejora' if r.get('mejora_a_base') else '—'} |"))
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    print(md(evaluate()))
