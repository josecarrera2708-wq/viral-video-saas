"""Búsqueda v8 (config/busqueda_v8_prerregistrada.md): combinaciones de las confirmaciones que mejor salieron en v5-v7, sobre los patrones de la
mesa (doble suelo, triple suelo/techo y bandera en 1 h; bandera en 4 h). Patrones y filtros idénticos a v6/v7. Todo causal.
R1 patrón dentro de patrón + funding · R2 patrón dentro de patrón + volumen · R3 horario de Wall Street + RSI no extremo ·
R4 tendencia + compresión + volumen · R5 triple confirmación + RSI no extremo · R6 horario de Wall Street + funding.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8
from .v4 import _base
from .v6 import _filters
from .v7 import _patron, _q3_mask, GRUPOS as G7

MAX_BARS = {"1h": 72, "4h": 42}
SALIDAS = ("TP3", "dejar_correr")
COMB = {"R1 patrón dentro de patrón + funding": "3F", "R2 patrón dentro de patrón + volumen": "3V", "R3 horario Wall Street + RSI no extremo": "HR",
        "R4 tendencia + compresión + volumen": "TCV", "R5 triple confirmación + RSI no extremo": "TVFR", "R6 horario Wall Street + funding": "HF"}
GRUPOS = {("1h", "E01 Doble suelo"), ("1h", "E02 Triple suelo/techo"), ("1h", "E03 Bandera / banderín"), ("4h", "E03 Bandera / banderín")}


def _mask(df, tf, s, code, q3):
    F = _filters(df, tf); hr = df.index.hour.to_numpy(); r14 = rsi(df["close"], 14).to_numpy(); m = np.ones(len(df), bool)
    for ch in code:
        if ch == "3": m &= q3[s]
        elif ch == "H":
            m &= (((hr + 1) % 24 >= 13) & ((hr + 1) % 24 <= 21)) if tf == "1h" else np.isin(hr, [12, 16])
        elif ch == "R": m &= (r14 < 70) if s == 1 else (r14 > 30)
        else: m &= np.nan_to_num(F[ch](s), nan=0).astype(bool)
    return m


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | grupo | combinación | salida». 1 h: 3 grupos × 6 × 2 = 36; 4 h: bandera × 4 × 2 = 8. Total 44."""
    c = df["close"]; a = atr(df, 14).to_numpy(); out = {}
    trail = _i8(np.where(c < ema(c, 50), -1, np.where(c > ema(c, 50), 1, 0)))
    q3 = _q3_mask(df) if tf == "1h" else None
    for name, (kind, sub) in G7.items():
        if (tf, name) not in GRUPOS: continue
        r, _ = _patron(df, kind, sub); base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for comb, code in COMB.items():
            if "3" in code and tf != "1h": continue
            ok = np.zeros(len(df), bool)
            for s in (1, -1): ok |= (base == s) & _mask(df, tf, s, code, q3)
            d = np.where(ok, base, 0).astype(np.int8)
            for sal in SALIDAS:
                tp = 3.0 if sal == "TP3" else 0.0
                out[f"{tf} | {name} | {comb} | {sal}"] = Spec(_i8(d), st, exit=None if tp else trail, tp_mult=tp, max_bars=MAX_BARS[tf] if tp else 0)
    return out
