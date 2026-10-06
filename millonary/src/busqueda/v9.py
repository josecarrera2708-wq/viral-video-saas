"""Búsqueda v9 (config/busqueda_v9_prerregistrada.md): ALTO ACIERTO. Mismos patrones que la v8 (doble suelo, triple suelo/techo y bandera en 1 h;
bandera en 4 h) con objetivos cortos (0,5 / 0,75 / 1 R) y stop normal o 1,5 veces más ancho. Confirmaciones: ninguna, triple confirmación
(tendencia + volumen + funding), horario de Wall Street + RSI no extremo y patrón dentro de patrón (solo 1 h). Todo causal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import atr
from ..intraday.setups import Spec, _i8
from .v7 import _patron, _q3_mask, GRUPOS as G7
from .v8 import _mask, GRUPOS, MAX_BARS

CONF = {"A0 ninguna": "", "A1 triple confirmación": "TVF", "A2 horario Wall Street + RSI no extremo": "HR", "A3 patrón dentro de patrón": "3"}
SALIDAS = {f"TP{tp:g}R stop×{k:g}": (tp, k) for k in (1.0, 1.5) for tp in (0.5, 0.75, 1.0)}


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | grupo | confirmación | salida». 1 h: 3 grupos × 4 × 6 = 72; 4 h: bandera × 3 × 6 = 18. Total 90."""
    a = atr(df, 14).to_numpy(); out = {}
    q3 = _q3_mask(df) if tf == "1h" else None
    for name, (kind, sub) in G7.items():
        if (tf, name) not in GRUPOS: continue
        r, _ = _patron(df, kind, sub); base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for conf, code in CONF.items():
            if "3" in code and tf != "1h": continue
            ok = np.zeros(len(df), bool)
            for s in (1, -1): ok |= (base == s) & _mask(df, tf, s, code, q3)
            d = _i8(np.where(ok, base, 0))
            for sal, (tp, k) in SALIDAS.items():
                out[f"{tf} | {name} | {conf} | {sal}"] = Spec(d, st * k, exit=None, tp_mult=tp, max_bars=MAX_BARS[tf])
    return out
