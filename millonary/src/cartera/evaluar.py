"""Evaluación histórica del gestor de cartera (config/cartera_prerregistrada.md). Se ejecuta UNA vez tras el commit del prerregistro.

  python -m src.cartera.evaluar      → reports/cartera_resultados.{json,md}
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.fondos.data import build_history, _splice_spot, RAW, ROOT
from src.fondos import estrategias as E
from src.robustness.stats import deflated_sharpe, pbo_cscv
from src.incubator.factors import holm
from src.cartera import gestor as G

N_PRIOR, N_NEW = 261, 4
EVAL0 = pd.Timestamp("2020-01-01", tz="UTC")
PER = {"B 2020-01→2023-12": ("2020-01-01", "2024-01-01"), "C 2024-01→hoy": ("2024-01-01", None)}
NUC, CAR = "N Núcleo v1", "F06 Carry de funding (cash-and-carry)"


def _ts(x):
    t = pd.Timestamp(x); return t.tz_localize("UTC") if t.tzinfo is None else t


def cut(r, a, b=None):
    r = r[r.index >= _ts(a)]; return r[r.index < _ts(b)] if b else r


def core_daily(d: pd.DataFrame, cm: float = 1.0) -> pd.Series:
    """Igual que src.fondos.evaluar.core_daily (núcleo v1 sin tocar) pero con el coste por rotación × cm."""
    from src.core.nucleo import CoreParams, run_core
    from src.backtest.funding import align_funding
    from src.fondos.data import _append_vision
    from src.live.vision_feed import VisionFeed, SPOT
    now = d.index[-1] + pd.Timedelta("1D")
    s4 = pd.read_parquet(RAW / "spot_BTCUSDT_4h.parquet").set_index("time")[["open", "high", "low", "close"]]
    s4 = _splice_spot(_append_vision(s4, VisionFeed(base=SPOT), now)); s4 = s4[s4.index + pd.Timedelta("4h") <= now]
    fr = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")[["time", "funding_rate"]]; fr["time"] = pd.DatetimeIndex(fr["time"]).round("min")
    ev = pd.concat([fr, VisionFeed().funding(fr["time"].max(), now)[["time", "funding_rate"]]]).drop_duplicates("time", keep="last")
    closes = s4.index + pd.Timedelta("4h")
    syn = closes[(closes.hour % 8 == 0) & (closes < EVAL0)]
    ev = pd.concat([pd.DataFrame({"time": syn, "funding_rate": 0.0001}), ev[ev["time"] >= EVAL0]]).sort_values("time")
    ev = ev[(ev["time"] > s4.index[0]) & (ev["time"] <= s4.index[-1] + pd.Timedelta("4h"))]
    from dataclasses import replace
    p = replace(CoreParams(), cost=CoreParams().cost * cm)
    eq = run_core(s4, align_funding(s4.index, pd.Timedelta("4h"), ev), p)["equity"]
    return eq.resample("1D").last().pct_change().dropna()


def sleeves(d: pd.DataFrame, cm: float = 1.0) -> pd.DataFrame:
    res = {k: fn(d, cm=cm) for k, fn in E.ESTRATEGIAS.items()}
    R = pd.DataFrame({k: v["ret"] for k, v in res.items()})
    R.insert(0, NUC, core_daily(d, cm).reindex(R.index))
    return R.fillna(0.0)


def portfolios(R: pd.DataFrame, cm: float = 1.0) -> dict:
    two = R[[NUC, CAR]]
    k1, t1 = G.combine(two, G.schedule(two, "iv"), cm)
    W2 = G.schedule(R, "hrp"); k2, t2 = G.combine(R, W2, cm)
    k5, _ = G.combine(two, G.schedule(two, "fixed", fixed={NUC: 0.5, CAR: 0.5}), cm)
    k3, m3 = G.dd_overlay(k5, cm=cm); k4, m4 = G.dd_overlay(k2, cm=cm)
    return {"K1 Paridad de riesgo núcleo+carry": k1, "K2 HRP de los 10 bolsillos": k2,
            "K3 50/50 núcleo+carry + control de caída": k3, "K4 HRP 10 bolsillos + control de caída": k4,
            "_ref 50/50 núcleo+carry (lo que corre en papel)": k5, "_W2": W2, "_m3": m3, "_m4": m4}


def stats(r: pd.Series) -> dict:
    r = cut(r, EVAL0)
    return {"sharpe": G.sharpe(r), "cagr": G.cagr(r), "mes_sobre_1000": 1000 * ((1 + G.cagr(r)) ** (1 / 12) - 1), "vol_anual": float(r.std(ddof=1) * np.sqrt(365)),
            "caida_max": G.max_dd(r), "cvar95_diario": G.cvar(r), "calmar": G.cagr(r) / max(G.max_dd(r), 1e-9),
            "por_periodo": {p: G.sharpe(cut(r, a, b)) for p, (a, b) in PER.items()},
            "por_anio": {str(y): float((1 + g).prod() - 1) for y, g in r.groupby(r.index.year)}}


def evaluate(write: bool = True, d: pd.DataFrame | None = None) -> dict:
    d = build_history() if d is None else d
    R, R2 = sleeves(d), sleeves(d, 2.0)
    P, P2 = portfolios(R), portfolios(R2, 2.0)
    names = [k for k in P if k.startswith("K")]
    nuc = cut(R[NUC], EVAL0)
    rows = {k: stats(P[k]) for k in names}; ns = stats(R[NUC])
    p = [G.boot_sharpe_diff(cut(P[k], EVAL0), nuc) for k in names]; ph = holm(np.array(p))
    for i, k in enumerate(names):
        r = rows[k]; x = cut(P[k], EVAL0).to_numpy()
        r["p_vs_nucleo"], r["p_holm"] = float(p[i]), float(ph[i])
        r["sharpe_costes_x2"] = G.sharpe(cut(P2[k], EVAL0))
        r["dsr"] = float(deflated_sharpe(x, N_PRIOR + N_NEW, 1.0 / len(x)))
        g = {"G1 Sharpe > núcleo (p Holm < 0,10)": r["sharpe"] > ns["sharpe"] and r["p_holm"] < 0.10,
             "G2 Sharpe > núcleo en B y en C": all(r["por_periodo"][q] > ns["por_periodo"][q] for q in PER),
             "G3 caída ≤ núcleo": r["caida_max"] <= ns["caida_max"],
             "G4 Sharpe > 0 con costes ×2": r["sharpe_costes_x2"] > 0, "G5 DSR ≥ 0,80": r["dsr"] >= 0.80}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["aprobada"] = all(g.values())
    W2 = P["_W2"]; last = W2.iloc[-1]
    M = pd.concat([nuc] + [cut(P[k], EVAL0) for k in names], axis=1).to_numpy()
    F = cut(R[[c for c in R.columns if c != NUC and c != CAR]], pd.Timestamp("2018-09-01", tz="UTC")).to_numpy()
    out = {"datos": [str(d.index[0].date()), str(d.index[-1].date())], "evaluacion_desde": str(EVAL0.date()), "n_pruebas": N_PRIOR + N_NEW,
           "referencias": {"N Núcleo v1": stats(R[NUC]), "F06 carry solo": stats(R[CAR]),
                           "50/50 núcleo+carry (papel actual)": stats(P["_ref 50/50 núcleo+carry (lo que corre en papel)"])},
           "carteras": rows, "aprobadas": [k for k in names if rows[k]["aprobada"]],
           "pesos_hrp_actuales": {k: float(v) for k, v in last.items() if v > 0},
           "pesos_hrp_medios": {k: float(v) for k, v in cut(W2, EVAL0).mean().items()},
           "dias_con_control_reducido": {"K3": float((cut(P["_m3"], EVAL0) < 1).mean()), "K4": float((cut(P["_m4"], EVAL0) < 1).mean())},
           "pbo": {"familia_K_mas_nucleo (CSCV s=16)": float(pbo_cscv(M, s=16)),
                   "fondos_F01-F09_sin_carry (CSCV s=16, diagnóstico)": float(pbo_cscv(F, s=16))}}
    if write:
        (ROOT / "reports" / "cartera_resultados.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False))
        (ROOT / "reports" / "cartera_resultados.md").write_text(md(out))
    return out


def md(o: dict) -> str:
    L = [f"# Gestor de cartera (Fase 1) · resultados históricos ({o['evaluacion_desde']} → {o['datos'][1]})", "",
         f"Aprobadas para papel: **{len(o['aprobadas'])}/{len(o['carteras'])}** · pruebas acumuladas: {o['n_pruebas']}", "",
         "| Cartera | Sharpe | B | C | ×2 costes | CAGR | €/mes sobre 1.000 | caída | CVaR95 día | Calmar | p Holm | DSR | Puertas | Aprob. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in {**{f"(ref) {a}": b for a, b in o["referencias"].items()}, **o["carteras"]}.items():
        pp = list(r["por_periodo"].values())
        ex = (f"{r['sharpe_costes_x2']:.2f} | " if "puertas" in r else "— | ")
        tail = (f"{r['p_holm']:.3f} | {r['dsr']:.2f} | {sum(r['puertas'].values())}/5 | {'✔' if r['aprobada'] else '—'} |" if "puertas" in r else "— | — | — | — |")
        L.append(f"| {k} | {r['sharpe']:.2f} | {pp[0]:.2f} | {pp[1]:.2f} | {ex}{r['cagr']:+.1%} | {r['mes_sobre_1000']:+.1f} | {r['caida_max']:.0%} | {r['cvar95_diario']:.2%} | {r['calmar']:.2f} | {tail}")
    L += ["", "Por año (retorno):", "", "| Cartera | " + " | ".join(next(iter(o["carteras"].values()))["por_anio"]) + " |",
          "|---|" + "---|" * len(next(iter(o["carteras"].values()))["por_anio"])]
    for k, r in {**o["referencias"], **o["carteras"]}.items():
        L.append(f"| {k} | " + " | ".join(f"{v:+.0%}" for v in r["por_anio"].values()) + " |")
    L += ["", "Pesos HRP actuales: " + ", ".join(f"{k.split(' ')[0]} {v:.0%}" for k, v in sorted(o["pesos_hrp_actuales"].items(), key=lambda x: -x[1])),
          "Pesos HRP medios: " + ", ".join(f"{k.split(' ')[0]} {v:.0%}" for k, v in sorted(o["pesos_hrp_medios"].items(), key=lambda x: -x[1])),
          f"Días con exposición reducida por el control de caída: K3 {o['dias_con_control_reducido']['K3']:.0%}, K4 {o['dias_con_control_reducido']['K4']:.0%}",
          "PBO: " + "; ".join(f"{k} = {v:.2f}" for k, v in o["pbo"].items()),
          "", "€/mes = equivalente mensual compuesto del CAGR sobre 1.000 USDT (USDT, no euros). Periodos: B 2020-01→2023-12 · C 2024-01→hoy."]
    return "\n".join(L).replace("€/mes", "USDT/mes") + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
