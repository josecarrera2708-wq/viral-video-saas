"""Fase 2 en SOMBRA (papel, informativo): `python -m src.primas.forward` → paper_state/primas/resumen.json.

Ninguna certificó (reports/primas_resultados.md: B01, B02 y V01 pasan 4/5 y fallan solo el Deflated Sharpe con n = 269). Se siguen hacia
delante en sombra, como el ciclo de mejora, para acumular evidencia; no entran en la cartera ni en ninguna decisión. Recálculo completo con la
regla del histórico; cada cuenta arranca con 1.000 USDT en la fecha de inicio con la posición que la regla tenga ese día. Sin dinero real.
"""
from __future__ import annotations
import json
import pandas as pd
from src.primas.evaluar import inputs, run_all, NAMES, ROOT

D = ROOT / "paper_state" / "primas"
START = pd.Timestamp("2026-10-03", tz="UTC"); CAP = 1000.0
SOMBRA = [NAMES["B01"], NAMES["B02"], NAMES["V01"]]


def run(now: pd.Timestamp | None = None) -> dict:
    x = inputs(now); res = run_all(x)
    hist = json.loads((ROOT / "reports" / "primas_resultados.json").read_text())["estrategias"]
    out = {}
    for k in SOMBRA:
        v = res[k]; r = v["ret"][v["ret"].index >= START]; eq = CAP * (1 + r).cumprod()
        o = {"dias": int(len(r)), "equity": float(eq.iloc[-1]) if len(r) else CAP, "retorno": float(eq.iloc[-1] / CAP - 1) if len(r) else 0.0,
             "hist": {a: hist[k][a] for a in ("sharpe", "cagr", "caida_max", "mes_sobre_1000")} | {"puertas": f"{sum(hist[k]['puertas'].values())}/5"}}
        if "trades" in v:
            tr = v["trades"]; last = tr.iloc[-1] if len(tr) else None
            o["posicion"] = (None if last is None or last["motivo"] != "abierta" else
                             {"contrato": last["contrato"], "desde": str(last["entrada"])[:10], "basis_anual_entrada": float(last["basis_anual"])})
            o["operaciones"] = [{a: str(b) for a, b in t.items()} for _, t in tr[tr["entrada"] >= START - pd.Timedelta("120D")].iterrows()]
        else:
            o["en_posicion"] = bool(v["on"].iloc[-1]) if len(v["on"]) else False
            o["dvol_ultimo"] = float(x["dvol"].iloc[-1])
        out[k] = o
    return {"generado": str(x["now"]), "inicio": str(START.date()), "ultimo_dia": str(x["days"][-1].date()), "estado": "SOMBRA (no certificadas)",
            "estrategias": out, "nota": "Papel en sombra. 1.000 USDT por estrategia. No entran en la cartera. Sin dinero real."}


def main(now: pd.Timestamp | None = None) -> dict:
    D.mkdir(parents=True, exist_ok=True); o = run(now)
    (D / "resumen.json").write_text(json.dumps(o, indent=1, default=str, ensure_ascii=False)); return o


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, ensure_ascii=False)[:1500])
