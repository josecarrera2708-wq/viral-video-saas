"""Evaluación histórica de la Fase 2, lote 1 (config/primas_prerregistrada.md). Se ejecuta UNA vez tras el commit del prerregistro.

  python -m src.primas.evaluar      → reports/primas_resultados.{json,md}
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.primas import data as Dt, estrategias as S
from src.fondos.evaluar import p_mean
from src.fondos.data import build_history
from src.cartera import gestor as G
from src.cartera.evaluar import sleeves, NUC, CAR
from src.robustness.stats import deflated_sharpe
from src.incubator.factors import holm

ROOT = Dt.ROOT; N_PRIOR, N_NEW = 265, 4
B0, V0 = pd.Timestamp("2021-01-01", tz="UTC"), pd.Timestamp("2021-05-01", tz="UTC")
SPLIT = pd.Timestamp("2024-01-01", tz="UTC")
NAMES = {"B01": "B01 Basis trimestral hasta vencimiento", "B02": "B02 Basis trimestral con salida anticipada",
         "V01": "V01 Prima de volatilidad (venta de varianza 30 d)", "V02": "V02 Prima de volatilidad con filtro IV > RV"}


def inputs(now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    spot, fut, dv = Dt.spot_1h(now), Dt.futures(now), Dt.dvol(now)
    last = spot.index[-1] + pd.Timedelta("1h")                                       # fin de la última vela cerrada
    days = pd.date_range(B0, last.floor("D") - pd.Timedelta("1D"), freq="1D")
    close = pd.Series({d: S._at(spot, d) for d in pd.date_range(B0 - pd.Timedelta("40D"), last.floor("D"), freq="1D")})
    return {"spot": spot, "fut": fut, "dvol": dv, "days": days, "close": close, "now": now}


def run_all(x: dict, cm: float = 1.0) -> dict:
    vd = x["days"][x["days"] >= V0]
    return {NAMES["B01"]: S.basis(x["spot"], x["fut"], x["days"], False, cm), NAMES["B02"]: S.basis(x["spot"], x["fut"], x["days"], True, cm),
            NAMES["V01"]: S.vrp(x["close"], x["dvol"], vd, False, cm), NAMES["V02"]: S.vrp(x["close"], x["dvol"], vd, True, cm)}


def evaluate(write: bool = True) -> dict:
    x = inputs(); res, res2 = run_all(x), run_all(x, 2.0)
    Rf = sleeves(build_history()); nuc, car = Rf[NUC], Rf[CAR]
    rows = {}
    for k, v in res.items():
        r = v["ret"]; r2 = res2[k]["ret"]; idx = r.index
        n_, c_ = nuc.reindex(idx).fillna(0.0), car.reindex(idx).fillna(0.0)
        base = pd.concat([n_.rename("N"), c_.rename("C")], axis=1); plus = base.assign(X=r)
        mix0, _ = G.combine(base, G.schedule(base, "iv")); mix1, _ = G.combine(plus, G.schedule(plus, "iv"))
        rows[k] = {"desde": str(idx[0].date()), "sharpe": G.sharpe(r), "sharpe_costes_x2": G.sharpe(r2),
                   "por_periodo": {"X →2023": G.sharpe(r[r.index < SPLIT]), "Y 2024→": G.sharpe(r[r.index >= SPLIT])},
                   "cagr": G.cagr(r), "mes_sobre_1000": 1000 * ((1 + G.cagr(r)) ** (1 / 12) - 1), "vol_anual": float(r.std(ddof=1) * np.sqrt(365)),
                   "caida_max": G.max_dd(r), "peor_dia": float(r.min()), "cvar95_diario": G.cvar(r), "ops": int(v["n_ops"]), "p": p_mean(r),
                   "dias_en_posicion": float(((v["pos"] != "") if "pos" in v else v["on"]).mean()),
                   "corr_nucleo": float(r.corr(n_)), "corr_carry_funding": float(r.corr(c_)),
                   "paridad_N_carry": G.sharpe(mix0), "paridad_N_carry_mas_esta": G.sharpe(mix1),
                   "por_anio": {str(y): float((1 + g).prod() - 1) for y, g in r.groupby(r.index.year)},
                   "operaciones": (v["trades"].astype(str).to_dict("records")[-8:] if "trades" in v and len(v["trades"]) else [])}
    names = list(rows); ph = holm(np.array([rows[k]["p"] for k in names]))
    for i, k in enumerate(names):
        r = rows[k]; a = res[k]["ret"].to_numpy(); r["p_holm"] = float(ph[i])
        r["dsr"] = float(deflated_sharpe(a, N_PRIOR + N_NEW, 1.0 / len(a)))
        g = {"C1 Sharpe>0 y p Holm<0,10": r["sharpe"] > 0 and r["p_holm"] < 0.10, "C2 Sharpe>0 en X e Y": all(v > 0 for v in r["por_periodo"].values()),
             "C3 Sharpe>0 con costes ×2": r["sharpe_costes_x2"] > 0, "C4 DSR≥0,80": r["dsr"] >= 0.80, "C5 ≥20 operaciones": r["ops"] >= 20}
        r["puertas"] = {a_: bool(b) for a_, b in g.items()}; r["certificada"] = all(g.values())
        r["aporta_a_la_cartera"] = r["paridad_N_carry_mas_esta"] > r["paridad_N_carry"]
    out = {"datos_hasta": str(x["days"][-1].date()), "n_pruebas": N_PRIOR + N_NEW, "estrategias": rows,
           "certificadas": [k for k in names if rows[k]["certificada"]], "aportan": [k for k in names if rows[k]["aporta_a_la_cartera"]],
           "contratos": sorted(x["fut"])}
    if write:
        (ROOT / "reports" / "primas_resultados.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False))
        (ROOT / "reports" / "primas_resultados.md").write_text(md(out))
    return out


def md(o: dict) -> str:
    L = [f"# Fase 2 · primas de riesgo, lote 1 · resultados históricos (hasta {o['datos_hasta']})", "",
         f"Certificadas: **{len(o['certificadas'])}/{len(o['estrategias'])}** · mejoran la paridad núcleo+carry: **{len(o['aportan'])}** · pruebas acumuladas {o['n_pruebas']}", "",
         "| Estrategia | desde | Sharpe | X | Y | ×2 costes | CAGR | USDT/mes s/1.000 | caída | peor día | ops | % días | p Holm | DSR | corr N | corr carry | paridad N+C → +esta | Puertas | Cert. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["estrategias"].items():
        pp = list(r["por_periodo"].values())
        L.append(f"| {k} | {r['desde']} | {r['sharpe']:.2f} | {pp[0]:.2f} | {pp[1]:.2f} | {r['sharpe_costes_x2']:.2f} | {r['cagr']:+.1%} | {r['mes_sobre_1000']:+.1f} | "
                 f"{r['caida_max']:.0%} | {r['peor_dia']:+.1%} | {r['ops']} | {r['dias_en_posicion']:.0%} | {r['p_holm']:.3f} | {r['dsr']:.2f} | {r['corr_nucleo']:+.2f} | "
                 f"{r['corr_carry_funding']:+.2f} | {r['paridad_N_carry']:.2f} → {r['paridad_N_carry_mas_esta']:.2f} | {sum(r['puertas'].values())}/5 | {'✔' if r['certificada'] else '—'} |")
    yrs = sorted({y for r in o["estrategias"].values() for y in r["por_anio"]})
    L += ["", "| Por año | " + " | ".join(yrs) + " |", "|---|" + "---|" * len(yrs)]
    for k, r in o["estrategias"].items():
        L.append(f"| {k} | " + " | ".join(f"{r['por_anio'][y]:+.1%}" if y in r["por_anio"] else "—" for y in yrs) + " |")
    L += ["", "X = inicio→2023-12 · Y = 2024-01→hoy. Paridad N+C = cartera K1 (1/σ, 180 d) del núcleo y el carry de funding; → +esta = añadiendo esta estrategia como tercer bolsillo."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
