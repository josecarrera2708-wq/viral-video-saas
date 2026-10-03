"""Patrones de velas japonesas (material de estudio + Conesa). CAUSALES.

Cada patrón devuelve +1 (alcista), -1 (bajista) o 0. Los umbrales son parámetros para que el
minero los ajuste y el embudo de robustez compruebe su sensibilidad.
Corrección respecto al documento fuente: Marubozu VERDE = compradores dominan todo el periodo
(el documento tenía los colores invertidos).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from .indicators import atr


def _parts(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    body = (c - o).abs(); rng = (h - l).replace(0, np.nan)
    upper = h - np.maximum(o, c); lower = np.minimum(o, c) - l
    return o, h, l, c, body, rng, upper, lower


def doji(df, max_body=0.1):
    o, h, l, c, body, rng, u, lo = _parts(df)
    return (body <= max_body * rng).astype("int8")          # neutro: 1 = hay doji


def marubozu(df, min_body=0.9):
    o, h, l, c, body, rng, u, lo = _parts(df)
    big = body >= min_body * rng
    return (big * np.sign(c - o)).astype("int8")


def hammer_family(df, trend_n=5, wick_ratio=2.0, opp_wick=0.15, min_wick_range=0.5):
    """Martillo (+1) y estrella fugaz (-1) según la forma; martillo invertido (+1) y hombre
    colgado (-1) según el contexto previo. Devuelve DataFrame con las cuatro columnas."""
    o, h, l, c, body, rng, u, lo = _parts(df)
    prior = c.shift(1) - c.shift(1 + trend_n)
    down, up = prior < 0, prior > 0
    b = body.replace(0, np.nan)
    # mecha larga >= wick_ratio*cuerpo y >= min_wick_range*rango; mecha contraria <= opp_wick*rango
    long_lower = (lo >= wick_ratio * b) & (lo >= min_wick_range * rng) & (u <= opp_wick * rng)
    long_upper = (u >= wick_ratio * b) & (u >= min_wick_range * rng) & (lo <= opp_wick * rng)
    return pd.DataFrame({
        "hammer": (long_lower & down).astype("int8"),               # +1 tras caída
        "hanging_man": -(long_lower & up).astype("int8"),           # -1 tras subida
        "inv_hammer": (long_upper & down).astype("int8"),           # +1 tras caída
        "shooting_star": -(long_upper & up).astype("int8"),         # -1 tras subida
    })


def engulfing(df):
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    bull = (pc < po) & (c > o) & (o <= pc) & (c >= po) & ((c - o) > (po - pc))
    bear = (pc > po) & (c < o) & (o >= pc) & (c <= po) & ((o - c) > (pc - po))
    return (bull.astype("int8") - bear.astype("int8"))


def harami(df, small=0.6):
    o, c = df["open"], df["close"]
    po, pc = o.shift(1), c.shift(1)
    pb = (po - pc).abs()
    inside = (np.maximum(o, c) < np.maximum(po, pc)) & (np.minimum(o, c) > np.minimum(po, pc))
    small_body = (c - o).abs() <= small * pb
    bull = (pc < po) & (c > o) & inside & small_body
    bear = (pc > po) & (c < o) & inside & small_body
    return (bull.astype("int8") - bear.astype("int8"))


def tweezers(df, tol_atr=0.1, n=14):
    """Pinzas: mínimos (o máximos) casi iguales en dos velas seguidas."""
    a = atr(df, n)
    o, c, h, l = df["open"], df["close"], df["high"], df["low"]
    bot = ((l - l.shift(1)).abs() <= tol_atr * a) & (c.shift(1) < o.shift(1)) & (c > o)
    top = ((h - h.shift(1)).abs() <= tol_atr * a) & (c.shift(1) > o.shift(1)) & (c < o)
    return (bot.astype("int8") - top.astype("int8"))


def stars(df, n=14):
    """Estrella de la mañana (+1) / de la tarde (-1), 3 velas."""
    o, c, h, l = df["open"], df["close"], df["high"], df["low"]
    a = atr(df, n)
    b1 = (c.shift(2) - o.shift(2)); b2 = (c.shift(1) - o.shift(1)).abs()
    mid1 = (o.shift(2) + c.shift(2)) / 2
    morning = (b1 < 0) & (b1.abs() >= 0.6 * a) & (b2 <= 0.3 * a) & (c > o) & (c > mid1)
    evening = (b1 > 0) & (b1.abs() >= 0.6 * a) & (b2 <= 0.3 * a) & (c < o) & (c < mid1)
    return (morning.astype("int8") - evening.astype("int8"))


def three_soldiers_crows(df):
    o, c = df["open"], df["close"]
    def bull(k): return c.shift(k) > o.shift(k)
    def bear(k): return c.shift(k) < o.shift(k)
    soldiers = (bull(0) & bull(1) & bull(2) & (c > c.shift(1)) & (c.shift(1) > c.shift(2)) &
                (o > o.shift(1)) & (o < c.shift(1)) & (o.shift(1) > o.shift(2)) & (o.shift(1) < c.shift(2)))
    crows = (bear(0) & bear(1) & bear(2) & (c < c.shift(1)) & (c.shift(1) < c.shift(2)) &
             (o < o.shift(1)) & (o > c.shift(1)) & (o.shift(1) < o.shift(2)) & (o.shift(1) > c.shift(2)))
    return (soldiers.astype("int8") - crows.astype("int8"))


def pin_bar(df, wick_frac=2 / 3):
    o, h, l, c, body, rng, u, lo = _parts(df)
    top_third = np.minimum(o, c) >= l + (1 - 1 / 3) * (h - l)
    bot_third = np.maximum(o, c) <= l + (1 / 3) * (h - l)
    bull = (lo >= wick_frac * rng) & top_third
    bear = (u >= wick_frac * rng) & bot_third
    return (bull.astype("int8") - bear.astype("int8"))


def all_candles(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["doji"] = doji(df); out["marubozu"] = marubozu(df)
    out = out.join(hammer_family(df))
    out["engulfing"] = engulfing(df); out["harami"] = harami(df)
    out["tweezers"] = tweezers(df); out["stars"] = stars(df)
    out["soldiers_crows"] = three_soldiers_crows(df); out["pin_bar"] = pin_bar(df)
    return out
