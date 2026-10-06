"""Búsqueda v10 (config/busqueda_v10_prerregistrada.md): CONFLUENCIA de dos patrones distintos en la misma temporalidad. Un patrón de la mesa
(doble suelo, triple suelo/techo, bandera) entra solo si OTRO de esos patrones dio señal en la misma dirección en las últimas 24 h (1 h: 24 velas;
4 h: 6 velas), sin contar la vela actual. Confirmaciones extra: tendencia (EMA 50 días), funding a contrapié, compresión. Todo causal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr
from ..intraday.setups import Spec, _i8
from .v6 import _filters
from .v7 import _patron, GRUPOS as G7
from .v8 import GRUPOS, MAX_BARS

VENTANA = {"1h": 24, "4h": 6}
COMB = {"B1 confluencia": "", "B2 confluencia + tendencia": "T", "B3 confluencia + funding": "F", "B4 confluencia + compresión": "C"}
SALIDAS = ("TP3", "dejar_correr")


def _reciente(sig: np.ndarray, s: int, w: int) -> np.ndarray:
    """True si hubo señal s en alguna de las w velas ANTERIORES (excluye la actual)."""
    x = pd.Series((sig == s).astype(float)).shift(1).rolling(w, min_periods=1).max().fillna(0).to_numpy()
    return x > 0


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | grupo | combinación | salida». 1 h: 3 × 4 × 2 = 24; 4 h: bandera × 4 × 2 = 8. Total 32."""
    c = df["close"]; a = atr(df, 14).to_numpy(); out = {}; F = _filters(df, tf)
    trail = _i8(np.where(c < ema(c, 50), -1, np.where(c > ema(c, 50), 1, 0)))
    pats = {name: _patron(df, kind, sub)[0] for name, (kind, sub) in G7.items()}
    for name in G7:
        if (tf, name) not in GRUPOS: continue
        r = pats[name]; base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        otros = [p.d.astype(np.int8) for n2, p in pats.items() if n2 != name]
        for comb, code in COMB.items():
            ok = np.zeros(len(df), bool)
            for s in (1, -1):
                m = (base == s) & np.any([_reciente(o, s, VENTANA[tf]) for o in otros], axis=0)
                for ch in code: m &= np.nan_to_num(F[ch](s), nan=0).astype(bool)
                ok |= m
            d = _i8(np.where(ok, base, 0))
            for sal in SALIDAS:
                tp = 3.0 if sal == "TP3" else 0.0
                out[f"{tf} | {name} | {comb} | {sal}"] = Spec(d, st, exit=None if tp else trail, tp_mult=tp, max_bars=MAX_BARS[tf] if tp else 0)
    return out
