"""Cartera K4 (HRP de los 10 bolsillos + control de caída) en papel: `python -m src.cartera.forward` → paper_state/cartera/resumen.json.

Aprobada 5/5 en reports/cartera_resultados.md (prerregistro config/cartera_prerregistrada.md). Recálculo completo en cada ejecución con la
misma regla que el histórico (bolsillos, pesos y control de caída sobre toda la historia, causales); la cuenta de papel arranca con 1.000 USDT
el día de inicio. Sin dinero real.
"""
from __future__ import annotations
import json
import pandas as pd
from src.fondos.data import load, ROOT
from src.cartera import gestor as G
from src.cartera.evaluar import sleeves, portfolios

D = ROOT / "paper_state" / "cartera"
START = pd.Timestamp("2026-10-03", tz="UTC"); CAP = 1000.0
K4 = "K4 HRP 10 bolsillos + control de caída"


def run(now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC"); d = load(now)
    R = sleeves(d); P = portfolios(R)
    r = P[K4][P[K4].index >= START]; eq = CAP * (1 + r).cumprod()
    W = P["_W2"].iloc[-1]; m = float(P["_m4"].iloc[-1])
    hist = json.loads((ROOT / "reports" / "cartera_resultados.json").read_text())["carteras"][K4]
    return {"generado": str(now), "inicio": str(START.date()), "ultimo_dia_cerrado": str(d.index[-1].date()), "dias": int(len(r)),
            "equity": float(eq.iloc[-1]) if len(r) else CAP, "retorno": float(eq.iloc[-1] / CAP - 1) if len(r) else 0.0,
            "caida_max": G.max_dd(r) if len(r) else 0.0, "multiplicador_caida": m,
            "pesos": {k: round(float(v) * m, 4) for k, v in W.items() if v > 0}, "en_usdt_sin_usar": round(1 - m, 4),
            "hist": {k: hist[k] for k in ("sharpe", "cagr", "caida_max", "mes_sobre_1000")},
            "nota": "Papel. 1.000 USDT. Pesos de capital × multiplicador de caída; el resto queda en USDT. Sin dinero real."}


def main(now: pd.Timestamp | None = None) -> dict:
    D.mkdir(parents=True, exist_ok=True); o = run(now)
    (D / "resumen.json").write_text(json.dumps(o, indent=1, default=str, ensure_ascii=False)); return o


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, ensure_ascii=False))
