"""Los 15 traders de la incubadora (config/incubadora_prerregistrada.md). Parámetros FIJOS.

Cada setup recibe velas 4h (open, high, low, close, volume) y devuelve el ESTADO deseado al cierre de cada vela
(-1, 0, +1). El simulador lo aplica desde la vela siguiente. Todos los indicadores son causales.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import sma, ema, atr, rsi, macd, bollinger, donchian, true_range


def _state(enter_long, exit_long, enter_short=None, exit_short=None) -> np.ndarray:
    """Máquina de estados: entra con la señal de entrada, mantiene hasta la de salida. Entradas simultáneas: se ignora la corta."""
    n = len(enter_long); pos = np.zeros(n); cur = 0.0
    el, xl = np.asarray(enter_long, bool), np.asarray(exit_long, bool)
    es = np.zeros(n, bool) if enter_short is None else np.asarray(enter_short, bool)
    xs = np.zeros(n, bool) if exit_short is None else np.asarray(exit_short, bool)
    for i in range(n):
        if cur == 1.0 and xl[i]: cur = 0.0
        elif cur == -1.0 and xs[i]: cur = 0.0
        if cur == 0.0:
            if el[i]: cur = 1.0
            elif es[i]: cur = -1.0
        pos[i] = cur
    return pos


def _psar(df: pd.DataFrame, af0=0.02, afmax=0.2) -> np.ndarray:
    """Parabolic SAR: devuelve +1 (alcista) / -1 (bajista) al cierre de cada vela."""
    h, l = df["high"].to_numpy(), df["low"].to_numpy(); n = len(df)
    trend = np.zeros(n); up = True; sar = l[0]; ep = h[0]; af = af0; trend[0] = 1
    for i in range(1, n):
        sar = sar + af * (ep - sar)
        if up:
            sar = min(sar, l[i - 1], l[i - 2] if i > 1 else l[i - 1])
            if l[i] < sar:
                up = False; sar = ep; ep = l[i]; af = af0
            elif h[i] > ep:
                ep = h[i]; af = min(af + af0, afmax)
        else:
            sar = max(sar, h[i - 1], h[i - 2] if i > 1 else h[i - 1])
            if h[i] > sar:
                up = True; sar = ep; ep = h[i]; af = af0
            elif l[i] < ep:
                ep = l[i]; af = min(af + af0, afmax)
        trend[i] = 1 if up else -1
    return trend


def s01_psar_ema200(df):
    t = _psar(df); c = df["close"]; e = ema(c, 200)
    up = (t > 0) & (c > e); dn = (t < 0) & (c < e)
    return np.where(up, 1.0, np.where(dn, -1.0, 0.0))


def s02_ichimoku(df):
    h, l, c = df["high"], df["low"], df["close"]
    ten = (h.rolling(9).max() + l.rolling(9).min()) / 2
    kij = (h.rolling(26).max() + l.rolling(26).min()) / 2
    spa = ((ten + kij) / 2).shift(26)                      # nube proyectada 26 velas: la de hoy se calculó hace 26
    spb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    top, bot = np.maximum(spa, spb), np.minimum(spa, spb)
    up = (c > top) & (ten > kij); dn = (c < bot) & (ten < kij)
    return np.where(up, 1.0, np.where(dn, -1.0, 0.0))


def s03_boll_rsi_mr(df):
    c = df["close"]; b = bollinger(c, 20, 2.0); r = rsi(c, 14)
    el = ((c < b["lo"]) & (r < 30)).to_numpy(); es = ((c > b["up"]) & (r > 70)).to_numpy()
    xl = (c > b["mid"]).to_numpy(); xs = (c < b["mid"]).to_numpy()
    return _state(el, xl, es, xs)


def s04_keltner(df):
    c = df["close"]; m = ema(c, 20); a = atr(df, 10)
    up, lo = m + 2 * a, m - 2 * a
    return _state((c > up).to_numpy(), (c < m).to_numpy(), (c < lo).to_numpy(), (c > m).to_numpy())


def s05_rsi2_pullback(df):
    c = df["close"]; r2 = rsi(c, 2); s200 = sma(c, 200)
    return _state(((r2 < 10) & (c > s200)).to_numpy(), (r2 > 70).to_numpy())


def s06_sma_7_25(df):
    c = df["close"]; a, b = sma(c, 7), sma(c, 25)
    return np.where(a > b, 1.0, np.where(a < b, -1.0, 0.0))


def s07_sma_7_25_f200(df):
    c = df["close"]; a, b = sma(c, 7), sma(c, 25)
    return np.where((a > b) & (c > sma(c, 200)), 1.0, 0.0)


def s08_canal_tercios(df):
    hh = df["high"].rolling(20).max(); ll = df["low"].rolling(20).min()
    p = (df["close"] - ll) / (hh - ll).replace(0, np.nan)
    return np.where(p > 2 / 3, 1.0, np.where(p < 1 / 3, -1.0, 0.0))


def s09_donchian20(df):
    c = df["close"]; d20 = donchian(df, 20); d10 = donchian(df, 10)
    return _state((c > d20["hh"]).to_numpy(), (c < d10["ll"]).to_numpy(),
                  (c < d20["ll"]).to_numpy(), (c > d10["hh"]).to_numpy())


def s10_macd_ema200(df):
    c = df["close"]; m = macd(c); e = ema(c, 200)
    return np.where((m["macd"] > m["signal"]) & (c > e), 1.0, np.where((m["macd"] < m["signal"]) & (c < e), -1.0, 0.0))


def s11_supertrend(df, n=10, mult=3.0):
    a = atr(df, n).to_numpy(); hl2 = ((df["high"] + df["low"]) / 2).to_numpy(); c = df["close"].to_numpy(); m = len(df)
    ub, lb = hl2 + mult * a, hl2 - mult * a; fub, flb = ub.copy(), lb.copy(); tr = np.zeros(m); cur = 1.0
    for i in range(1, m):
        if np.isnan(a[i]):
            continue
        fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1] or np.isnan(fub[i - 1])) else fub[i - 1]
        flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1] or np.isnan(flb[i - 1])) else flb[i - 1]
        if cur == 1.0 and c[i] < flb[i]: cur = -1.0
        elif cur == -1.0 and c[i] > fub[i]: cur = 1.0
        tr[i] = cur
    tr[np.isnan(a)] = 0.0
    return tr


def s12_vol_expansion_mom(df):
    a = atr(df, 14); exp = a > sma(a, 50); mom = np.sign(df["close"] / df["close"].shift(12) - 1)
    return np.where(exp, mom, 0.0)


def s13_pullback_ema20(df):
    c, l = df["close"], df["low"]; e20, e50, e200 = ema(c, 20), ema(c, 50), ema(c, 200)
    trend = e50 > e200
    return _state((trend & (l <= e20) & (c > e20)).to_numpy(), (c < e50).to_numpy())


def s14_mom90(df):
    m = df["close"] / df["close"].shift(540) - 1
    return np.where(m > 0, 1.0, np.where(m < 0, -1.0, 0.0))


def s15_rsi14_trend(df):
    c = df["close"]; r = rsi(c, 14); e = ema(c, 200)
    return _state(((r > 55) & (c > e)).to_numpy(), (r < 45).to_numpy(), ((r < 45) & (c < e)).to_numpy(), (r > 55).to_numpy())


SETUPS = {
    "S01 Parabolic SAR + EMA200": s01_psar_ema200, "S02 Ichimoku": s02_ichimoku,
    "S03 Bollinger + RSI (reversión)": s03_boll_rsi_mr, "S04 Keltner ruptura": s04_keltner,
    "S05 RSI(2) retroceso (largo)": s05_rsi2_pullback, "S06 Cruce SMA 7-25": s06_sma_7_25,
    "S07 SMA 7-25 + filtro 200 (largo)": s07_sma_7_25_f200, "S08 Canal 20 por tercios": s08_canal_tercios,
    "S09 Donchian 20/10": s09_donchian20, "S10 MACD + EMA200": s10_macd_ema200,
    "S11 Supertrend 10/3": s11_supertrend, "S12 Expansión de volatilidad": s12_vol_expansion_mom,
    "S13 Retroceso a EMA20": s13_pullback_ema20, "S14 Momentum 90 d": s14_mom90,
    "S15 RSI14 + EMA200": s15_rsi14_trend,
}


def all_states(df: pd.DataFrame) -> pd.DataFrame:
    out = {}
    for k, f in SETUPS.items():
        s = np.nan_to_num(np.asarray(f(df), float), nan=0.0)
        out[k] = s
    return pd.DataFrame(out, index=df.index)
