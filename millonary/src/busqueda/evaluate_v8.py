"""Búsqueda v8 (config/busqueda_v8_prerregistrada.md). Ejecución única:  python -m src.busqueda.evaluate_v8
Mismos periodos, motor, costes y puertas G1-G5 que la v2; DSR con n_trials = 44 (las variantes de esta búsqueda).
Elegible: R>0 en construcción y validación con ≥30 ops en validación (≥10 en diario). Examen para las elegibles (máx. 20, por t de validación)."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from ..backtest.engine import Params
from ..incubator.factors import holm
from ..intraday.evaluate import summarize, run_period, stress
from ..robustness.stats import deflated_sharpe
from ..desk15.data import ROOT
from .evaluate import PER, load, _days, _daily
from .v8 import variants

N_FINAL = 20
N_MIN_VAL = {"1h": 30, "4h": 30, "1d": 10}


def evaluate(write=True, tfs=("1h", "4h"), loader=load) -> dict:
    rows, specs, data = {}, {}, {}
    for tf in tfs:
        df, f = loader(tf); df = df.assign(f=f); data[tf] = (df, f)                  # la v8 usa el funding (P6, P7)
        for k, sp in variants(df, tf).items():
            specs[k] = sp; r = rows[k] = {"tf": tf}
            for per in ("construccion", "validacion"):
                a, b = PER[tf][per]; r[per] = summarize(run_period(df, f, sp, a, b, Params()), _days(a, b))
    elig = [k for k, r in rows.items() if r["construccion"]["R_media"] > 0 and r["validacion"]["R_media"] > 0 and r["validacion"]["n"] >= N_MIN_VAL[r["tf"]]]
    final = sorted(elig, key=lambda k: -rows[k]["validacion"]["t_R"])[:N_FINAL]
    var_sr = float(np.var([rows[k]["validacion"]["sharpe"] / np.sqrt(365) for k in rows])) if rows else 0.0
    for k in final:
        tf = rows[k]["tf"]; df, f = data[tf]; r = rows[k]; a, b = PER[tf]["examen"]
        r["examen"] = summarize(run_period(df, f, specs[k], a, b, Params()), _days(a, b))
        r["examen_x2"] = summarize(run_period(df, f, specs[k], a, b, stress(2.0)), _days(a, b))
        a0, b0 = PER[tf]["construccion"][0], PER[tf]["validacion"][1]
        r["dsr"] = deflated_sharpe(_daily(run_period(df, f, specs[k], a0, b0, Params())), len(rows), var_sr)
    ph = holm(np.array([rows[k]["examen"]["p_1s"] for k in final])) if final else []
    for i, k in enumerate(final):
        r = rows[k]; ex = r["examen"]; r["p_holm"] = float(ph[i])
        g = {"G1 R>0 examen (≥20 ops)": ex["R_media"] > 0 and ex["n"] >= 20, "G2 p Holm<0,10": r["p_holm"] < 0.10, "G3 R>0 costes ×2": r["examen_x2"]["R_media"] > 0,
             "G4 caída examen<30 %": ex["caida_max"] < 0.30 and not ex["liquidado"], "G5 DSR≥0,80": r["dsr"] >= 0.80}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
    fam = {}
    for k in elig:                                                                   # regla de la mesa: mejor elegible por grupo y temporalidad que GANE en el examen
        if k not in final or rows[k]["examen"]["R_media"] <= 0: continue
        f_ = " | ".join(k.split(" | ")[:2])
        if f_ not in fam or rows[k]["validacion"]["t_R"] > rows[fam[f_]]["validacion"]["t_R"]:
            fam[f_] = k
    fam = dict(sorted(fam.items(), key=lambda kv: -rows[kv[1]]["validacion"]["t_R"])[:3])   # como mucho 3 traders nuevos
    out = {"n_variantes": len(rows), "elegibles": len(elig), "finalistas": final, "certificadas": [k for k in final if rows[k]["certificada"]],
           "mesa_v8": sorted(fam.values()), "marginales": marginals(rows), "variantes": rows}
    if write:
        (ROOT / "reports" / "busqueda_v8_resultados.json").write_text(json.dumps(out, indent=1, default=float)); (ROOT / "reports" / "busqueda_v8_resultados.md").write_text(md(out))
    return out


def marginals(rows) -> dict:
    """R media y acierto en construcción y validación por dimensión (temporalidad, familia, filtro, salida)."""
    df = pd.DataFrame([dict(zip(["tf", "familia", "combinacion", "salida"], k.split(" | ")), Rc=r["construccion"]["R_media"], R=r["validacion"]["R_media"],
                            acierto=r["validacion"]["acierto"], n=r["validacion"]["n"]) for k, r in rows.items()])
    return {dim: df.groupby(dim)[["Rc", "R", "acierto", "n"]].mean().round(3).to_dict(orient="index") for dim in ["tf", "familia", "combinacion", "salida"]}


def md(o) -> str:
    L = [f"# Búsqueda v8 · combinaciones de las mejores confirmaciones", "",
         f"Variantes: **{o['n_variantes']}** · elegibles: **{o['elegibles']}** · al examen: **{len(o['finalistas'])}** · certificadas: **{len(o['certificadas'])}**", "",
         "## Medias por dimensión (R por operación; construcción / validación; acierto en validación)", ""]
    for dim, d in o["marginales"].items():
        L.append(f"**{dim}**: " + " · ".join(f"{k} {v['Rc']:+.3f} / {v['R']:+.3f} ({v['acierto']:.0%})" for k, v in d.items())); L.append("")
    L += ["## Todas las variantes (R por operación)", "", "| Variante | Ops constr. | R constr. | Ops valid. | R valid. | Acierto valid. | t valid. | Elegible |", "|---|---|---|---|---|---|---|---|"]
    for k, r in o["variantes"].items():
        c, v = r["construccion"], r["validacion"]
        L.append(f"| {k} | {c['n']} | {c['R_media']:+.3f} | {v['n']} | {v['R_media']:+.3f} | {v['acierto']:.0%} | {v['t_R']:+.2f} | {'sí' if k in o['finalistas'] else '—'} |")
    L += ["", "## Examen (2025-07 → 2026-09)", "", "| Variante | Ops | Acierto | R examen | R ×2 costes | Retorno | Caída | p Holm | DSR | Puertas | Cert. |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in o["finalistas"]:
        r = o["variantes"][k]; e = r["examen"]
        L.append(f"| {k} | {e['n']} | {e['acierto']:.0%} | {e['R_media']:+.3f} | {r['examen_x2']['R_media']:+.3f} | {e['retorno']:+.1%} | {e['caida_max']:.0%} | {r['p_holm']:.2f} | {r['dsr']:.2f} | "
                 f"{sum(r['puertas'].values())}/5 | {'SÍ' if r['certificada'] else '—'} |")
    L += ["", "## Seleccionadas para la mesa (mejor elegible por familia)", ""] + [f"- {k}" for k in o["mesa_v8"]]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
