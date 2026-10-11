"""¿Qué riesgo por operación haría falta para un 30 % mensual? Medición, no cambia ninguna regla.  python -m src.busqueda.objetivo_mensual
Junta las operaciones del examen (2025-07 → 2026-09, Binance) de los 16 traders de la mesa en una sola cuenta y simula riesgo fijo por operación."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..backtest.engine import Params
from ..intraday.evaluate import run_period
from ..desk15.data import ROOT
from ..mesanueva.patrones import TRADERS
from .evaluate import PER, load

RIESGOS = (0.005, 0.01, 0.02, 0.03, 0.05, 0.10)


def trades() -> pd.DataFrame:
    rows, data = [], {}
    for name, (tf, key, mod, *_) in TRADERS.items():
        if tf not in data:
            df, f = load(tf); data[tf] = (df.assign(f=f), f)
        df, f = data[tf]; a, b = PER[tf]["examen"]
        res = run_period(df, f, mod.variants(df, tf)[key], a, b, Params()); r = res["r"]
        for xi, R in zip(r["exit_idx"], r["r"]):
            rows.append({"trader": name[:3], "salida": res["idx"][int(xi)], "R": float(R)})
    return pd.DataFrame(rows).sort_values("salida")


def simula(t: pd.DataFrame, f: float) -> dict:
    eq = pd.Series(np.cumprod(1 + f * t["R"].to_numpy()), index=t["salida"]).clip(lower=0)
    m = eq.resample("ME").last().ffill(); m = pd.concat([pd.Series([1.0], index=[m.index[0] - pd.offsets.MonthEnd()]), m]).pct_change().dropna()
    return {"riesgo": f, "mes_medio": float((eq.iloc[-1]) ** (1 / len(m)) - 1), "peor_mes": float(m.min()), "mejor_mes": float(m.max()),
            "meses_en_perdida": int((m < 0).sum()), "meses": len(m), "caida_max": float((1 - eq / eq.cummax()).max()), "total": float(eq.iloc[-1] - 1)}


def main() -> str:
    t = trades(); n = len(t); months = (t["salida"].max() - t["salida"].min()).days / 30.44
    L = ["# Objetivo 30 % mensual · medición con la mesa actual (examen 2025-07 → 2026-09)", "",
         f"Operaciones: **{n}** de 16 traders · {n / months:.0f} al mes · R media {t['R'].mean():+.3f} · acierto {(t['R'] > 0).mean():.0%} · R al mes {t['R'].sum() / months:+.1f}", "",
         "| Riesgo por operación | Rentabilidad mensual media | Peor mes | Mejor mes | Meses en pérdida | Caída máxima | Total |", "|---|---|---|---|---|---|---|"]
    for f in RIESGOS:
        s = simula(t, f)
        L.append(f"| {f:.1%} | {s['mes_medio']:+.1%} | {s['peor_mes']:+.1%} | {s['mejor_mes']:+.1%} | {s['meses_en_perdida']}/{s['meses']} | {s['caida_max']:.0%} | {s['total']:+.0%} |")
    L += ["", "Notas: cuenta única, interés compuesto, operaciones solapadas sumadas sin límite de apalancamiento (optimista). Comisiones incluidas en R.",
          "El examen ya se usó para elegir a estos traders: los números de verdad serán peores."]
    out = "\n".join(L) + "\n"; (ROOT / "reports" / "objetivo_mensual.md").write_text(out); return out


if __name__ == "__main__":
    print(main())
