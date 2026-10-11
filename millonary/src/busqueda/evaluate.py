"""Búsqueda v2 (config/busqueda_v2_prerregistrada.md). Ejecución única:  python -m src.busqueda.evaluate
1) Construcción y validación para las 768 variantes. 2) Finalistas: R>0 en construcción y validación, ≥30 ops en validación; las 20 con mayor t en validación.
3) Examen SOLO para las finalistas. Puertas G1-G5. Salida: reports/busqueda_v2_resultados.{json,md}"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from ..backtest.engine import Params
from ..backtest.funding import align_funding
from ..incubator.factors import holm
from ..intraday.evaluate import summarize, run_period, stress
from ..robustness.stats import deflated_sharpe, sharpe_pp
from ..desk15.data import ROOT
from .setups import variants

END = "2026-09-28"
PER = {"15m": {"construccion": ("2022-07-01", "2024-07-01"), "validacion": ("2024-07-01", "2025-07-01"), "examen": ("2025-07-01", END)},
       **{tf: {"construccion": ("2020-03-01", "2024-01-01"), "validacion": ("2024-01-01", "2025-07-01"), "examen": ("2025-07-01", END)} for tf in ("1h", "4h", "1d")}}
N_FINAL = 20


def load(tf: str):
    if tf == "15m":
        d = pd.read_parquet(ROOT / "data" / "cache" / "deribit_15m.parquet"); f = pd.read_parquet(ROOT / "data" / "cache" / "deribit_15m_funding.parquet")["f"].to_numpy()
        m = d.index < pd.Timestamp(END, tz="UTC"); return d[m][["open", "high", "low", "close", "volume"]], f[m]
    src = "4h" if tf == "4h" else "1h"
    d = pd.read_parquet(ROOT / "data" / "raw" / f"perp_BTCUSDT_{src}.parquet").set_index("time")[["open", "high", "low", "close", "volume"]]
    d = d[d.index < pd.Timestamp(END, tz="UTC")]
    if tf == "1d":
        g = d.resample("1D"); d = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})[g["close"].count() == 24].dropna()
    ev = pd.read_parquet(ROOT / "data" / "raw" / "perp_BTCUSDT_funding.parquet"); ev = ev[ev["time"] < pd.Timestamp(END, tz="UTC")]
    return d, align_funding(d.index, pd.Timedelta({"1h": "1h", "4h": "4h", "1d": "1D"}[tf]), ev[["time", "funding_rate"]])


def _days(a, b):
    return (pd.Timestamp(b) - pd.Timestamp(a)).days


def _daily(res):
    r = res["r"]; eq = pd.Series(r["equity"], index=res["idx"]).iloc[res["start_i"]:]
    return eq.resample("1D").last().pct_change().dropna().to_numpy()


def evaluate(write=True, tfs=("15m", "1h", "4h", "1d"), loader=load) -> dict:
    rows, specs, data = {}, {}, {}
    for tf in tfs:
        df, f = loader(tf); data[tf] = (df, f)
        for k, sp in variants(df, tf).items():
            specs[k] = sp; r = rows[k] = {"tf": tf}
            for per in ("construccion", "validacion"):
                a, b = PER[tf][per]; r[per] = summarize(run_period(df, f, sp, a, b, Params()), _days(a, b))
    elig = [k for k, r in rows.items() if r["construccion"]["R_media"] > 0 and r["validacion"]["R_media"] > 0 and r["validacion"]["n"] >= 30]
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
    out = {"n_variantes": len(rows), "elegibles": len(elig), "finalistas": final, "certificadas": [k for k in final if rows[k]["certificada"]],
           "marginales": marginals(rows), "variantes": rows}
    if write:
        (ROOT / "reports" / "busqueda_v2_resultados.json").write_text(json.dumps(out, indent=1, default=float)); (ROOT / "reports" / "busqueda_v2_resultados.md").write_text(md(out))
    return out


def marginals(rows) -> dict:
    """R media en VALIDACIÓN por dimensión (temporalidad, setup, modo, stop, salida): responde «dónde va el stop / el TP / qué temporalidad»."""
    df = pd.DataFrame([dict(zip(["tf", "setup", "modo", "stop", "salida"], k.split(" | ")), R=r["validacion"]["R_media"], Rc=r["construccion"]["R_media"],
                            n=r["validacion"]["n"]) for k, r in rows.items()])
    return {dim: df.groupby(dim)[["Rc", "R", "n"]].mean().round(3).to_dict(orient="index") for dim in ["tf", "setup", "modo", "stop", "salida"]}


def md(o: dict) -> str:
    L = ["# Búsqueda v2 · acción de precio a favor de tendencia (15 min · 1 h · 4 h · diario)", "",
         f"Variantes: **{o['n_variantes']}** · elegibles (R>0 en construcción y validación, ≥30 ops): **{o['elegibles']}** · finalistas al examen: **{len(o['finalistas'])}** · certificadas: **{len(o['certificadas'])}**", "",
         "## Qué funciona mejor de media (R por operación; construcción / validación)", ""]
    for dim, t in o["marginales"].items():
        L.append(f"**{dim}**: " + " · ".join(f"{k} {v['Rc']:+.3f} / {v['R']:+.3f}" for k, v in t.items())); L.append("")
    L += ["## Finalistas (examen 2025-07 → 2026-09)", "", "| Variante | Ops/día | Acierto | R constr. | R valid. | R examen | R ×2 costes | Caída | p Holm | DSR | Puertas | Cert. |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in o["finalistas"]:
        r = o["variantes"][k]; e = r["examen"]
        L.append(f"| {k} | {e['por_dia']:.2f} | {e['acierto']:.0%} | {r['construccion']['R_media']:+.3f} | {r['validacion']['R_media']:+.3f} | {e['R_media']:+.3f} | {r['examen_x2']['R_media']:+.3f} | "
                 f"{e['caida_max']:.0%} | {r['p_holm']:.2f} | {r['dsr']:.2f} | {sum(r['puertas'].values())}/5 | {'✔' if r['certificada'] else '—'} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    print(md(evaluate()))
