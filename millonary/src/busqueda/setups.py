"""Búsqueda v2: acción de precio A FAVOR de la tendencia en 15 min, 1 h, 4 h y diario (prerregistro: config/busqueda_v2_prerregistrada.md).

Señal al CIERRE de la vela i; el motor entra en la apertura de i+1. Todo es causal (prueba de truncamiento en tests/test_busqueda.py).
Rejilla: 6 setups × 2 modos (ambos lados / solo largos) × 4 stops × 4 salidas = 192 variantes por temporalidad.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr
from ..intraday.setups import Spec, _i8

STOPS = ("1ATR", "2ATR", "3ATR", "estructura")
SALIDAS = ("TP2", "TP3", "TP5", "dejar_correr")
MODOS = ("ambos", "solo_largos")
MAX_BARS = {"15m": 96, "1h": 72, "4h": 42, "1d": 20}          # salida por tiempo con TP fijo (≈ 1 día, 3 días, 7 días, 20 días)


def _ctx(df):
    c = df["close"]; e20, e50, e200 = ema(c, 20), ema(c, 50), ema(c, 200)
    up = (c > e200) & (e50 > e200); dn = (c < e200) & (e50 < e200)
    return c, e20, e50, e200, up, dn, atr(df, 14)


def s1_ruptura(df):
    c, e20, e50, e200, up, dn, a = _ctx(df)
    hi, lo = df["high"].shift(1).rolling(20).max(), df["low"].shift(1).rolling(20).min()
    return (c > hi) & up, (c < lo) & dn


def s2_retroceso_ema20(df):
    c, e20, e50, e200, up, dn, a = _ctx(df); o, h, l = df["open"], df["high"], df["low"]
    return up & (l <= e20) & (c > e20) & (c > o), dn & (h >= e20) & (c < e20) & (c < o)


def s3_barra_interior(df):
    c, e20, e50, e200, up, dn, a = _ctx(df); h, l = df["high"], df["low"]
    inside = (h.shift(1) < h.shift(2)) & (l.shift(1) > l.shift(2))
    return inside & (c > h.shift(1)) & up, inside & (c < l.shift(1)) & dn


def s4_envolvente(df):
    c, e20, e50, e200, up, dn, a = _ctx(df); o, h, l = df["open"], df["high"], df["low"]
    bull = (c > o) & (c.shift(1) < o.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1)) & (l <= e20 + a)
    bear = (c < o) & (c.shift(1) > o.shift(1)) & (c <= o.shift(1)) & (o >= c.shift(1)) & (h >= e20 - a)
    return bull & up, bear & dn


def s5_pin_bar(df):
    c, e20, e50, e200, up, dn, a = _ctx(df); o, h, l = df["open"], df["high"], df["low"]
    rng = (h - l).replace(0, np.nan); body = (c - o).abs(); lw, uw = np.minimum(o, c) - l, h - np.maximum(o, c)
    ham = (lw >= 2 * body) & (lw >= 0.6 * rng) & (l <= e20 + 0.5 * a)
    star = (uw >= 2 * body) & (uw >= 0.6 * rng) & (h >= e20 - 0.5 * a)
    return ham & up, star & dn


def s6_cruce_ema(df):
    c, e20, e50, e200, up, dn, a = _ctx(df); e9, e21 = ema(c, 9), ema(c, 21)
    x_up = (e9 > e21) & (e9.shift(1) <= e21.shift(1)); x_dn = (e9 < e21) & (e9.shift(1) >= e21.shift(1))
    return x_up & (c > e200), x_dn & (c < e200)


SETUPS = {"S1 Ruptura 20 velas": s1_ruptura, "S2 Retroceso a EMA20": s2_retroceso_ema20, "S3 Barra interior": s3_barra_interior,
          "S4 Envolvente en retroceso": s4_envolvente, "S5 Pin bar en retroceso": s5_pin_bar, "S6 Cruce EMA 9/21": s6_cruce_ema}


def _stop(df, kind, d):
    a = atr(df, 14); c = df["close"]
    if kind.endswith("ATR"):
        return (float(kind[0]) * a).to_numpy()
    lo, hi = df["low"].rolling(10).min(), df["high"].rolling(10).max()              # mínimo/máximo de las 10 últimas velas (incluida la de señal)
    dist = np.where(d > 0, c - lo, np.where(d < 0, hi - c, np.nan)) + 0.1 * a.to_numpy()
    return np.clip(np.nan_to_num(dist, nan=2 * a.to_numpy()), 0.5 * a.to_numpy(), 4 * a.to_numpy())


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    c = df["close"]; e50 = ema(c, 50); out = {}
    trail = _i8(np.where(c < e50, -1, np.where(c > e50, 1, 0)))                     # «dejar correr»: sale al cerrar al otro lado de la EMA50
    for name, fn in SETUPS.items():
        L, S = fn(df)
        for modo in MODOS:
            d = np.where(L.fillna(False), 1, np.where(S.fillna(False) & (modo == "ambos"), -1, 0))
            for st in STOPS:
                stop = _stop(df, st, d)
                for sal in SALIDAS:
                    tp = 0.0 if sal == "dejar_correr" else float(sal[2:])
                    out[f"{tf} | {name} | {modo} | {st} | {sal}"] = Spec(_i8(d), stop, exit=trail if sal == "dejar_correr" else None,
                                                                         tp_mult=tp, max_bars=0 if sal == "dejar_correr" else MAX_BARS[tf])
    return out
