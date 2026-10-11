"""Fase 2, lote 2: entrada maker en las 40 traders base de las mesas (config/maker_prerregistrada.md). Ejecución única.

  python -m src.maker.evaluar      → reports/maker_resultados.{json,md}
"""
from __future__ import annotations
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.engine import Params, run as run_taker
from src.maker.engine import run as run_maker
from src.intraday.evaluate import summarize, stress, load as load_intradia, PERIODS as P_INT, WARM
from src.intraday.setups import all_specs as specs_int
from src.desk15.setups import all_specs as specs_15
from src.desk1h.setups import all_specs as specs_1h
from src.desk1h.data import to_1h
from src.desk15.evaluate import PERIODS as P_15
from src.incubator.factors import holm

ROOT = Path(__file__).resolve().parents[2]; N_PRIOR = 269


def desks() -> dict:
    h = pd.read_parquet(ROOT / "paper_state" / "mesa15" / "hist.parquet"); h = h[h.index < pd.Timestamp("2026-09-29", tz="UTC")]
    b15, f15 = h[["open", "high", "low", "close", "volume"]], h["f"].to_numpy()
    b1h, f1h = to_1h(b15, f15); di, fi = load_intradia()
    return {"intradia": (di, fi, specs_int, P_INT), "mesa15": (b15, f15, specs_15, P_15), "mesa1h": (b1h, f1h, specs_1h, P_15)}


def run_period(engine, df, f, spec, start, end, params: Params) -> dict:
    s0, e0 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    i0 = int(df.index.searchsorted(s0)); i1 = int(df.index.searchsorted(e0)); a = max(0, i0 - WARM)
    sl = slice(a, i1); idx = df.index[sl]; live = np.asarray(idx >= s0)
    ent = np.where(live, spec.entry[sl], 0).astype(np.int8); ex = None if spec.exit is None else np.where(live, spec.exit[sl], 0).astype(np.int8)
    p = replace(params, tp_mult=spec.tp_mult, max_bars=spec.max_bars); o = df.iloc[sl]
    r = engine(o["open"], o["high"], o["low"], o["close"], ent, np.nan_to_num(spec.stop[sl], nan=0.0), p, exit_sig=ex, funding=f[sl])
    return {"r": r, "idx": idx, "start_i": int(np.argmax(live))}


def _days(a, b):
    return (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days


def evaluate(write: bool = True) -> dict:
    rows = {}
    for desk, (df, f, sp_fn, PER) in desks().items():
        for k, sp in sp_fn(df).items():
            name = f"{desk} · {k}"; r = rows[name] = {"mesa": desk, "periodos": {}}
            for per, (a, b) in PER.items():
                t = summarize(run_period(run_taker, df, f, sp, a, b, Params()), _days(a, b))
                mres = run_period(run_maker, df, f, sp, a, b, Params()); m = summarize(mres, _days(a, b))
                m["llenado"] = m["n"] / max(m["n"] + mres["r"]["missed"], 1)
                r["periodos"][per] = {"taker": t, "maker": m}
            a, b = PER["examen"]
            r["maker_costes_x2"] = summarize(run_period(run_maker, df, f, sp, a, b, stress(2.0)), _days(a, b))
    names = list(rows); ph = holm(np.array([rows[k]["periodos"]["examen"]["maker"]["p_1s"] for k in names]))
    for i, k in enumerate(names):
        r = rows[k]; v, e = r["periodos"]["validacion"]["maker"], r["periodos"]["examen"]["maker"]; r["p_holm"] = float(ph[i])
        g = {"M1 R>0 validación y examen": v["R_media"] > 0 and e["R_media"] > 0, "M2 p Holm<0,10 (examen)": r["p_holm"] < 0.10,
             "M3 R>0 con costes ×2": r["maker_costes_x2"]["R_media"] > 0, "M4 ≥0,3 ops/día": e["por_dia"] >= 0.3,
             "M5 sin liquidación y caída<40 %": (not e["liquidado"]) and e["caida_max"] < 0.40}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
        r["maker_mejora"] = all(r["periodos"][p]["maker"]["R_media"] > r["periodos"][p]["taker"]["R_media"] for p in ("validacion", "examen"))
    agg = {p: {"R_taker": float(np.mean([rows[k]["periodos"][p]["taker"]["R_media"] for k in names])),
               "R_maker": float(np.mean([rows[k]["periodos"][p]["maker"]["R_media"] for k in names])),
               "llenado": float(np.mean([rows[k]["periodos"][p]["maker"]["llenado"] for k in names])),
               "positivas_taker": int(sum(rows[k]["periodos"][p]["taker"]["R_media"] > 0 for k in names)),
               "positivas_maker": int(sum(rows[k]["periodos"][p]["maker"]["R_media"] > 0 for k in names))} for p in ("construccion", "validacion", "examen")}
    out = {"n_pruebas": N_PRIOR + len(names), "traders": rows, "certificadas": [k for k in names if rows[k]["certificada"]],
           "maker_mejora_en_valid_y_examen": [k for k in names if rows[k]["maker_mejora"]], "agregado": agg}
    if write:
        (ROOT / "reports" / "maker_resultados.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False))
        (ROOT / "reports" / "maker_resultados.md").write_text(md(out))
    return out


def md(o: dict) -> str:
    a = o["agregado"]
    L = ["# Fase 2 · lote 2 · entrada maker (orden límite) en las 40 traders base · resultados históricos", "",
         f"Certificadas: **{len(o['certificadas'])}/{len(o['traders'])}** · maker mejora R en validación Y examen: **{len(o['maker_mejora_en_valid_y_examen'])}/{len(o['traders'])}** · pruebas acumuladas {o['n_pruebas']}", "",
         "| Periodo | R medio taker | R medio maker | llenado | traders con R>0 taker → maker |", "|---|---|---|---|---|"]
    for p, x in a.items():
        L.append(f"| {p} | {x['R_taker']:+.3f} | {x['R_maker']:+.3f} | {x['llenado']:.0%} | {x['positivas_taker']} → {x['positivas_maker']} |")
    L += ["", "| Trader | llenado ex. | R valid. taker → maker | R examen taker → maker | ops/día ex. maker | R ×2 costes | p Holm | Puertas | Cert. |", "|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["traders"].items():
        v, e = r["periodos"]["validacion"], r["periodos"]["examen"]
        L.append(f"| {k} | {e['maker']['llenado']:.0%} | {v['taker']['R_media']:+.3f} → {v['maker']['R_media']:+.3f} | {e['taker']['R_media']:+.3f} → {e['maker']['R_media']:+.3f} | "
                 f"{e['maker']['por_dia']:.2f} | {r['maker_costes_x2']['R_media']:+.3f} | {r['p_holm']:.2f} | {sum(r['puertas'].values())}/5 | {'✔' if r['certificada'] else '—'} |")
    L += ["", "Periodos propios de cada mesa (intradía: examen 2025-07→2026-09; 15 min y 1 h: examen 2025-10→2026-09). Los exámenes ya se habían abierto: es una segunda mirada."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
