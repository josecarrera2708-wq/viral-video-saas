"""Mesa de fondos hacia delante (papel). Rutina horaria: `python -m src.fondos.forward` → paper_state/fondos/.

Histórico congelado (paper_state/fondos/hist.parquet) + días nuevos de Binance Vision. Se recalcula TODO en cada ejecución (idempotente):
las 9 estrategias operan desde el inicio (config/fondos_start.json) con 1.000 USDT cada una; la información anterior (canales, N, volatilidad,
regla de salto de las Tortugas, pesos de la cartera) sí se usa, las posiciones no. Prerregistro: config/fondos_prerregistrada.md.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from .data import D, ROOT, load
from . import estrategias as E

CAP = 1000.0


def run(now: pd.Timestamp | None = None, d: pd.DataFrame | None = None, start: str | None = None) -> dict:
    cfg = json.loads((ROOT / "config" / "fondos_start.json").read_text()); start = pd.Timestamp(start or cfg["start"])
    now = now or pd.Timestamp.now(tz="UTC"); d = load(now) if d is None else d
    t0 = int(np.searchsorted(d.index, start))
    ref = {k: fn(d) for k, fn in E.ESTRATEGIAS.items()}                                   # sin restricción: para los pesos de la cartera
    live = {k: fn(d, t0=t0) for k, fn in E.ESTRATEGIAS.items()}
    live[E.MULTI] = E.multi(live, ref=ref, t0=t0)
    hist = json.loads((ROOT / "reports" / "fondos_resultados.json").read_text()) if (ROOT / "reports" / "fondos_resultados.json").exists() else {"estrategias": {}}
    summ, ops = {}, []
    for k, v in live.items():
        r = v["ret"].iloc[t0:]; eq = CAP * (1 + r).cumprod() if len(r) else pd.Series([CAP])
        dd = float((1 - eq / eq.cummax()).max()) if len(r) else 0.0
        tr = v["trades"]; tr = tr[tr["entrada"] >= start] if len(tr) else tr
        rj = v.get("reajustes"); rj = rj[rj["dia"] >= start] if rj is not None and len(rj) else pd.DataFrame()
        h = hist["estrategias"].get(k, {})
        summ[k] = {"dias": int(len(r)), "equity": float(eq.iloc[-1]), "retorno": float(eq.iloc[-1] / CAP - 1), "caida_max": dd,
                   "operaciones": int(len(tr)), "reajustes": int(len(rj)), "ganan": int((tr["ret"] > 0).sum()) if len(tr) else 0, "pierden": int((tr["ret"] <= 0).sum()) if len(tr) else 0,
                   "exposicion": float(v["expo"].iloc[-1]) if len(d) else 0.0, "nocional_usdt": float(v["nocional"].iloc[-1] * eq.iloc[-1]) if len(d) else 0.0,
                   "sharpe": (float(r.mean() / r.std(ddof=1) * np.sqrt(365)) if len(r) >= 10 and r.std(ddof=1) > 0 else None),
                   "hist": {"sharpe": h.get("sharpe"), "certificada": h.get("certificada"), "puertas": f"{sum(h['puertas'].values())}/5" if h.get("puertas") else None,
                            "caida_max": h.get("caida_max"), "cagr": h.get("cagr")}}
        if k == E.MULTI:
            summ[k]["pesos"] = {a: float(b) for a, b in v["pesos"].iloc[-1].items()} if len(d) else {}
        for _, t in tr.iterrows():
            ops.append({"estrategia": k, "entrada": str(t["entrada"])[:10], "salida": str(t["salida"])[:10], "lado": t["lado"], "px_entrada": float(t["px_entrada"]),
                        "px_salida": float(t["px_salida"]), "unidades": int(t["unidades"]), "ret_pct": float(t["ret"]), "pnl_usdt": float(t["ret"]) * CAP,
                        "R": None if pd.isna(t["R"]) else float(t["R"]), "motivo": t["motivo"]})
        for _, t in rj.iterrows():
            ops.append({"estrategia": k, "entrada": str(t["dia"])[:10], "salida": str(t["dia"])[:10], "lado": "REAJUSTE", "px_entrada": float(t["precio"]),
                        "px_salida": float(t["precio"]), "unidades": 0, "ret_pct": None, "pnl_usdt": None, "R": None,
                        "motivo": f"{t['motivo']}: exposición {t['de']:+.2f}× → {t['a']:+.2f}×"})
    ops.sort(key=lambda x: x["salida"], reverse=True)
    last = d.index[-1]
    return {"generado": str(now), "inicio": str(start), "ultimo_dia_cerrado": str(last.date()), "precio": float(d["close"].iloc[-1]),
            "funding_dia": float(d["f"].iloc[-1]), "funding_7d_anual": float(d["f"].iloc[-7:].mean() * 365),
            "fuente": "Binance Vision (contado y perpetuo BTCUSDT, velas diarias UTC; ≤ 1 día de retraso)", "estrategias": summ, "operaciones": ops[:300],
            "certificadas_hist": hist.get("certificadas", []), "nota": "Papel. 1.000 USDT por estrategia. Sin dinero real."}


def main(now: pd.Timestamp | None = None) -> dict:
    D.mkdir(parents=True, exist_ok=True); o = run(now)
    (D / "resumen.json").write_text(json.dumps(o, indent=1, default=str, ensure_ascii=False))
    pd.DataFrame(o["operaciones"]).to_csv(D / "operaciones.csv", index=False)
    return o


if __name__ == "__main__":
    o = main()
    print({k: v for k, v in o.items() if k not in ("estrategias", "operaciones")})
    for k, v in o["estrategias"].items():
        print(f"{k:50s} días {v['dias']:3d} ret {v['retorno']:+.2%} ops {v['operaciones']:3d} reajustes {v['reajustes']:3d} expo {v['exposicion']:+.2f}")
