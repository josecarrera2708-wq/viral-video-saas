"""Búsqueda v11 (config/busqueda_v11_prerregistrada.md). Ejecución única:  python -m src.busqueda.evaluate_v11
6 setups × 5 gestiones = 30 variantes, ejecutadas en velas de 5 min. Construcción 2020-03→2024-01, validación 2024-01→2025-07,
examen 2025-07→2026-09 (ya muy usado: se informa, no basta) y PRE-MUESTRA limpia 2017-10→2019-12 (contado, nunca usada en intradía)."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from ..incubator.factors import holm
from ..robustness.stats import deflated_sharpe
from . import intradia5 as I
from .sim5 import Costes, simulate
from .v11 import SETUPS, GESTIONES, SD_MULT

PRE = ("2017-10-01", "2019-12-31")
N_MIN = 30
N_TRIALS = 30


def _run(b5, f5, sig, g, a, b, costes=Costes()):
    t = pd.DatetimeIndex(sig["t"]); m = (t >= pd.Timestamp(a, tz="UTC")) & (t < pd.Timestamp(b, tz="UTC"))
    return simulate(b5, f5, t[m], sig["d"][m], sig["sd"][m], g, costes)


def _res(tr, a, b):
    I.PER["_tmp"] = (a, b); out = I.resumen(tr, "_tmp"); del I.PER["_tmp"]; return out


def load_pre():
    d = pd.read_parquet(I.RAW / "spot_BTCUSDT_5m_2017_2019.parquet").set_index("time")[I.COLS]
    d.index = d.index.astype("datetime64[ns, UTC]")
    return d, np.zeros(len(d))


def evaluate(write=True) -> dict:
    b5, f5 = I.load5(); p5, pf = load_pre(); rows = {}; daily = {}
    for sname, (fn, horas, usa_oi) in SETUPS.items():
        sig = fn(b5); sig_pre = None if usa_oi else fn(p5)
        for gname, mk in GESTIONES.items():
            g = mk(horas); k = SD_MULT.get(gname, 1.0)
            s2 = dict(sig, sd=sig["sd"] * k); r = rows[f"{sname} | {gname}"] = {"setup": sname, "gestion": gname}
            for per in ("construccion", "validacion", "examen"):
                a, b = I.PER[per]; tr = _run(b5, f5, s2, g, a, b); r[per] = _res(tr, a, b)
            a, b = I.PER["examen"]; r["examen_x2"] = _res(_run(b5, f5, s2, g, a, b, Costes().x(2.0)), a, b)
            a0, b0 = I.PER["construccion"][0], I.PER["validacion"][1]
            daily[f"{sname} | {gname}"] = _res(_run(b5, f5, s2, g, a0, b0), a0, b0)["diario"]
            if sig_pre is not None:
                sp = dict(sig_pre, sd=sig_pre["sd"] * k); r["premuestra"] = _res(_run(p5, pf, sp, g, *PRE), *PRE)
    var_sr = float(np.var([np.mean(x) / np.std(x, ddof=1) for x in daily.values() if len(x) > 30 and np.std(x) > 0]))
    elig = [k for k, r in rows.items() if r["construccion"]["R_media"] > 0 and r["validacion"]["R_media"] > 0 and r["validacion"]["n"] >= N_MIN]
    ph = holm(np.array([rows[k]["examen"]["p_1s"] for k in elig])) if elig else []
    for i, k in enumerate(elig):
        r = rows[k]; ex = r["examen"]; r["p_holm"] = float(ph[i]); r["dsr"] = deflated_sharpe(daily[k], N_TRIALS, var_sr)
        g = {"G1 R>0 examen (≥20 ops)": ex["R_media"] > 0 and ex["n"] >= 20, "G2 p Holm<0,10": r["p_holm"] < 0.10,
             "G3 R>0 costes ×2": r["examen_x2"]["R_media"] > 0, "G4 caída examen<30 %": ex["caida_max"] < 0.30, "G5 DSR≥0,80": r["dsr"] >= 0.80}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
        pm = r.get("premuestra")
        r["premuestra_ok"] = bool(pm and pm["R_media"] > 0 and pm["n"] >= N_MIN)
        r["a_papel"] = bool(r["certificada"] or (ex["R_media"] > 0 and r["premuestra_ok"]))
    cand = sorted([k for k in elig if rows[k]["a_papel"]], key=lambda k: -rows[k]["validacion"]["t_R"])
    mesa, vistos = [], set()
    for k in cand:                                                     # como mucho 2 y un solo trader por setup
        if rows[k]["setup"] in vistos: continue
        mesa.append(k); vistos.add(rows[k]["setup"])
        if len(mesa) == 2: break
    for r in rows.values():
        for per in ("construccion", "validacion", "examen", "examen_x2", "premuestra"):
            if per in r: r[per].pop("diario", None)
    out = {"n_variantes": len(rows), "elegibles": elig, "mesa_v11": mesa, "proteccion": proteccion(rows), "variantes": rows}
    if write:
        (I.ROOT / "reports" / "busqueda_v11_resultados.json").write_text(json.dumps(out, indent=1, default=float))
        (I.ROOT / "reports" / "busqueda_v11_resultados.md").write_text(md(out))
    return out


def proteccion(rows) -> dict:
    """Por gestión: acierto y R media ponderados por operaciones en construcción + validación + examen (todas las variantes)."""
    out = {}
    for gname in GESTIONES:
        n = w = R = 0.0
        for r in rows.values():
            if r["gestion"] != gname: continue
            for per in ("construccion", "validacion", "examen"):
                x = r[per]; n += x["n"]; w += x["acierto"] * x["n"]; R += x["R_media"] * x["n"]
        out[gname] = {"n": int(n), "acierto": w / n if n else 0.0, "R_media": R / n if n else 0.0}
    return out


def md(o) -> str:
    L = ["# Búsqueda v11 · intradía 2R/3R en velas de 5 min, con entrada de protección", "",
         f"Variantes: **{o['n_variantes']}** · elegibles: **{len(o['elegibles'])}** · a papel: **{len(o['mesa_v11'])}**", "",
         "## Gestión de la operación (todas las variantes, construcción + validación + examen)", "", "| Gestión | Ops | Acierto | R media |", "|---|---|---|---|"]
    for g, x in o["proteccion"].items():
        L.append(f"| {g} | {x['n']} | {x['acierto']:.0%} | {x['R_media']:+.3f} |")
    L += ["", "## Todas las variantes (ops · acierto · R media)", "", "| Variante | Construcción | Validación | Examen | Pre-muestra 2017-19 |", "|---|---|---|---|---|"]
    f = lambda x: f"{x['n']} · {x['acierto']:.0%} · {x['R_media']:+.3f}" if x else "—"
    for k, r in o["variantes"].items():
        L.append(f"| {k} | {f(r['construccion'])} | {f(r['validacion'])} | {f(r['examen'])} | {f(r.get('premuestra'))} |")
    L += ["", "## Elegibles: puertas", "", "| Variante | R examen | ×2 costes | Caída | p Holm | DSR | Puertas | Pre-muestra | A papel |", "|---|---|---|---|---|---|---|---|---|"]
    for k in o["elegibles"]:
        r = o["variantes"][k]; e = r["examen"]
        L.append(f"| {k} | {e['R_media']:+.3f} | {r['examen_x2']['R_media']:+.3f} | {e['caida_max']:.0%} | {r['p_holm']:.2f} | {r['dsr']:.2f} | "
                 f"{sum(r['puertas'].values())}/5 | {'sí' if r['premuestra_ok'] else 'no'} | {'SÍ' if r['a_papel'] else '—'} |")
    L += ["", "## A papel", ""] + ([f"- {k}" for k in o["mesa_v11"]] or ["- ninguna"])
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
