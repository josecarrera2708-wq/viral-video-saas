"""Sensibilidad de la implementación en SPOT (España): sin funding, tope 1x y comisiones de plataformas spot.

NO cambia la estrategia ni sus parámetros: solo el modelo de ejecución (costes y funding). Datos < 2025-07-01.
Salida: reports/sensibilidad_spot.json y una tabla por pantalla.
"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.funding import align_funding
from src.core.evaluate_nucleo import load_spot, funding_events, stats, subperiods, DELTA
from src.core.nucleo import CoreParams, run_core

ROOT = Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    df, _ = load_spot()
    f = align_funding(df.index, DELTA, funding_events(df.index)); z = np.zeros(len(df))
    casos = {
        "A) Perpetuo (prerregistrado): 7 pb + funding": (CoreParams(), f),
        "B) SPOT, tope 1x, sin funding, 7 pb": (CoreParams(cap=1.0), z),
        "C) SPOT, tope 1x, 15 pb (~0,1 % comisión + spread)": (CoreParams(cap=1.0, cost=0.0015), z),
        "D) SPOT, tope 1x, 30 pb (~0,26 % comisión + spread)": (CoreParams(cap=1.0, cost=0.0030), z),
        "E) SPOT, tope 1x, 50 pb (peor caso)": (CoreParams(cap=1.0, cost=0.0050), z),
    }
    out = {}
    for name, (p, fund) in casos.items():
        r = run_core(df, fund, p); s = stats(r["equity"]); sp = subperiods(r["equity"])
        out[name] = {**s, "expo_max": float(r["expo"].max()), "expo_media": float(r["expo"].mean()),
                     "rotacion_anual": float(r["turn"].sum() / ((df.index[-1] - df.index[0]).days / 365.25)),
                     "subperiodos_sharpe": {k: v["sharpe"] for k, v in sp.items()}}
        print(f"{name:54s} Sharpe {s['sharpe']:.2f} | CAGR {100*s['cagr']:.1f}% | DD {100*s['maxdd']:.1f}% | "
              f"expo máx {r['expo'].max():.2f}x | subper. {[round(v['sharpe'], 2) for v in sp.values()]}")
    (ROOT / "reports" / "sensibilidad_spot.json").write_text(json.dumps(out, indent=1))
