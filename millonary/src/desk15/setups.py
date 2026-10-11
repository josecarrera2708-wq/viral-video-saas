"""Mesa de 15 min: 13 traders de acción de precio y fórmulas cuantitativas (prerregistro: config/mesa15_prerregistrada.md).

Cada setup devuelve las señales AL CIERRE de la vela i (el motor entra en la apertura de i+1). Ventanas en velas de 15 min.
Todos los indicadores son causales: ninguna señal en i usa datos posteriores (prueba de truncamiento en tests/test_desk15.py).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8

N = 96                      # 24 h
TREND = 384                 # 96 h


def _atr(df):
    return atr(df, 14)


def _clip_stop(dist: pd.Series, a: pd.Series, lo=0.5, hi=3.0) -> np.ndarray:
    return dist.where(dist.notna(), 1.5 * a).clip(lower=lo * a, upper=hi * a).to_numpy()


def _support_resistance(df, n):
    return df["low"].shift(1).rolling(n).min(), df["high"].shift(1).rolling(n).max()


def p01_envolvente(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]; a = _atr(df); sup, res = _support_resistance(df, N)
    bull = (c > o) & (c.shift(1) < o.shift(1)) & (c >= o.shift(1)) & (o <= c.shift(1)) & (l <= sup + 0.5 * a)
    bear = (c < o) & (c.shift(1) > o.shift(1)) & (c <= o.shift(1)) & (o >= c.shift(1)) & (h >= res - 0.5 * a)
    st = np.where(bull, c - np.minimum(l, l.shift(1)) + 0.25 * a, np.where(bear, np.maximum(h, h.shift(1)) - c + 0.25 * a, np.nan))
    return Spec(_i8(np.where(bull, 1, np.where(bear, -1, 0))), _clip_stop(pd.Series(st, index=df.index), a), tp_mult=2.0, max_bars=32)


def p02_pin_bar(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]; a = _atr(df); rng = (h - l).replace(0, np.nan); body = (c - o).abs()
    sup, res = df["low"].shift(1).rolling(48).min(), df["high"].shift(1).rolling(48).max()
    low_w, up_w = np.minimum(o, c) - l, h - np.maximum(o, c)
    hammer = (low_w >= 2 * body) & (low_w >= 0.6 * rng) & (c >= l + 0.6 * rng) & (l <= sup + 0.25 * a)
    star = (up_w >= 2 * body) & (up_w >= 0.6 * rng) & (c <= h - 0.6 * rng) & (h >= res - 0.25 * a)
    st = np.where(hammer, c - l + 0.25 * a, np.where(star, h - c + 0.25 * a, np.nan))
    return Spec(_i8(np.where(hammer, 1, np.where(star, -1, 0))), _clip_stop(pd.Series(st, index=df.index), a), tp_mult=2.0, max_bars=32)


def p03_barrido(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]; a = _atr(df); sup, res = _support_resistance(df, N); mid = (h + l) / 2
    long_ = (l < sup) & (c > sup) & (c > mid); short = (h > res) & (c < res) & (c < mid)
    st = np.where(long_, c - l + 0.2 * a, np.where(short, h - c + 0.2 * a, np.nan))
    return Spec(_i8(np.where(long_, 1, np.where(short, -1, 0))), _clip_stop(pd.Series(st, index=df.index), a), tp_mult=2.0, max_bars=32)


def p04_fvg(df):
    """Fair Value Gap: hueco entre la máx. de i-2 y la mín. de i (alcista) con vela central impulsiva. Entrada cuando el precio vuelve al hueco y lo respeta."""
    h, l, c, o = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(), df["open"].to_numpy(); a = _atr(df).to_numpy(); n = len(df)
    sig = np.zeros(n, np.int8); stop = np.full(n, np.nan); zone = None                              # (dir, lo, hi, creado, usado)
    for i in range(2, n):
        if np.isnan(a[i]):
            continue
        if l[i] - h[i - 2] > 0.3 * a[i] and c[i - 1] > o[i - 1]:
            zone = [1, h[i - 2], l[i], i]
        elif l[i - 2] - h[i] > 0.3 * a[i] and c[i - 1] < o[i - 1]:
            zone = [-1, h[i], l[i - 2], i]
        elif zone is not None and i - zone[3] <= 48 and i > zone[3]:
            d, glo, ghi, _ = zone
            if d == 1 and l[i] <= ghi and c[i] > glo and c[i] > o[i]:
                sig[i] = 1; stop[i] = c[i] - glo + 0.2 * a[i]; zone = None
            elif d == -1 and h[i] >= glo and c[i] < ghi and c[i] < o[i]:
                sig[i] = -1; stop[i] = ghi - c[i] + 0.2 * a[i]; zone = None
            elif (d == 1 and c[i] < glo) or (d == -1 and c[i] > ghi):
                zone = None                                                                          # hueco invalidado
        elif zone is not None and i - zone[3] > 48:
            zone = None
    aa = pd.Series(a, index=df.index)
    return Spec(sig, _clip_stop(pd.Series(stop, index=df.index), aa), tp_mult=2.0, max_bars=48)


def p05_barra_interior(df):
    h, l, c = df["high"], df["low"], df["close"]; a = _atr(df); trend = ema(c, TREND)
    inside = (h.shift(1) < h.shift(2)) & (l.shift(1) > l.shift(2)); mh, ml = h.shift(2), l.shift(2)
    long_ = inside & (c > mh) & (c > trend); short = inside & (c < ml) & (c < trend)
    st = np.where(long_, c - ml, np.where(short, mh - c, np.nan))
    return Spec(_i8(np.where(long_, 1, np.where(short, -1, 0))), _clip_stop(pd.Series(st, index=df.index), a), tp_mult=2.0, max_bars=24)


def p06_estrella(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]; a = _atr(df); sup, res = _support_resistance(df, N)
    b0, b1, b2 = c.shift(2) - o.shift(2), c.shift(1) - o.shift(1), c - o
    morning = (b0 < -0.8 * a) & (b1.abs() < 0.3 * a) & (b2 > 0) & (c > (o.shift(2) + c.shift(2)) / 2) & (l.rolling(3).min() <= sup + a)
    evening = (b0 > 0.8 * a) & (b1.abs() < 0.3 * a) & (b2 < 0) & (c < (o.shift(2) + c.shift(2)) / 2) & (h.rolling(3).max() >= res - a)
    st = np.where(morning, c - l.rolling(3).min() + 0.2 * a, np.where(evening, h.rolling(3).max() - c + 0.2 * a, np.nan))
    return Spec(_i8(np.where(morning, 1, np.where(evening, -1, 0))), _clip_stop(pd.Series(st, index=df.index), a), tp_mult=2.0, max_bars=32)


def p07_doble_techo_suelo(df, k=6):
    """Pivotes confirmados con k velas de retraso (causales). Doble suelo: dos pivotes ≤ 0,3 ATR entre sí en 96 velas; entrada al romper el máximo intermedio."""
    h, l, c = df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(); a = _atr(df).to_numpy(); n = len(df)
    hs, ls = pd.Series(h), pd.Series(l)
    piv_lo = (ls.shift(k) == ls.rolling(2 * k + 1).min()).to_numpy(); piv_hi = (hs.shift(k) == hs.rolling(2 * k + 1).max()).to_numpy()   # el pivote está en i-k, confirmado en i
    sig = np.zeros(n, np.int8); stop = np.full(n, np.nan); lows = []; highs = []; arm_l = arm_h = None
    for i in range(2 * k + 1, n):
        if np.isnan(a[i]):
            continue
        j = i - k
        if piv_lo[i]:
            if lows and j - lows[-1][0] <= N and abs(l[j] - lows[-1][1]) <= 0.3 * a[i]:
                neck = h[lows[-1][0]:j + 1].max(); arm_l = (neck, min(l[j], lows[-1][1]), i)
            lows.append((j, l[j]))
        if piv_hi[i]:
            if highs and j - highs[-1][0] <= N and abs(h[j] - highs[-1][1]) <= 0.3 * a[i]:
                neck = l[highs[-1][0]:j + 1].min(); arm_h = (neck, max(h[j], highs[-1][1]), i)
            highs.append((j, h[j]))
        if arm_l is not None:
            if i - arm_l[2] > 48 or c[i] < arm_l[1]:
                arm_l = None
            elif c[i] > arm_l[0]:
                sig[i] = 1; stop[i] = c[i] - arm_l[1] + 0.2 * a[i]; arm_l = None
        if arm_h is not None and sig[i] == 0:
            if i - arm_h[2] > 48 or c[i] > arm_h[1]:
                arm_h = None
            elif c[i] < arm_h[0]:
                sig[i] = -1; stop[i] = arm_h[1] - c[i] + 0.2 * a[i]; arm_h = None
    aa = pd.Series(a, index=df.index)
    return Spec(sig, _clip_stop(pd.Series(stop, index=df.index), aa), tp_mult=2.0, max_bars=48)


def q01_tsmom(df):
    c = df["close"]; a = _atr(df); r = np.log(c / c.shift(N)); vol = np.log(c / c.shift(1)).rolling(N * 4).std() * np.sqrt(N)
    z = r / vol; wk = np.log(c / c.shift(7 * N))
    up = (z > 1) & (z.shift(1) <= 1) & (wk > 0); dn = (z < -1) & (z.shift(1) >= -1) & (wk < 0)
    return Spec(_i8(np.where(up, 1, np.where(dn, -1, 0))), (2.0 * a).to_numpy(), tp_mult=3.0, max_bars=96)


def q02_ou(df):
    c = df["close"]; a = _atr(df); lc = np.log(c); z = (lc - lc.rolling(N).mean()) / lc.rolling(N).std()
    return Spec(_i8(np.where((z < -2.5) & (z > z.shift(1)), 1, np.where((z > 2.5) & (z < z.shift(1)), -1, 0))), (2.0 * a).to_numpy(), tp_mult=1.0, max_bars=24)


def q03_regimen_vr(df):
    c = df["close"]; a = _atr(df); lc = np.log(c); r1 = lc.diff(); r4 = lc.diff(4); W = 384
    vr = r4.rolling(W).var() / (4 * r1.rolling(W).var())
    hh = df["high"].shift(1).rolling(48).max(); ll = df["low"].shift(1).rolling(48).min(); z = (lc - lc.rolling(N).mean()) / lc.rolling(N).std()
    trend_up = (vr > 1.15) & (c > hh)
    rev_up = (vr < 0.85) & (z < -2); rev_dn = (vr < 0.85) & (z > 2)
    sig = np.where(trend_up | rev_up, 1, np.where(((vr > 1.15) & (c < ll)) | rev_dn, -1, 0))
    return Spec(_i8(sig), (2.0 * a).to_numpy(), tp_mult=2.0, max_bars=48)


def q04_garman_klass(df):
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]; a = _atr(df)
    gk = 0.5 * np.log(h / l) ** 2 - (2 * np.log(2) - 1) * np.log(c / o) ** 2
    ratio = np.sqrt(gk.rolling(16).mean()) / np.sqrt(gk.rolling(192).mean())
    hh = h.shift(1).rolling(24).max(); ll = l.shift(1).rolling(24).min()
    return Spec(_i8(np.where((ratio > 1.5) & (c > hh), 1, np.where((ratio > 1.5) & (c < ll), -1, 0))), (1.5 * a).to_numpy(), tp_mult=2.0, max_bars=24)


def q05_flujo(df):
    o, h, l, c, v = df["open"], df["high"], df["low"], df["close"], df["volume"]; a = _atr(df); rng = (h - l).replace(0, np.nan)
    delta = ((c - l) - (h - c)) / rng * v; cum = delta.rolling(32).sum(); z = (cum - cum.rolling(384).mean()) / cum.rolling(384).std()
    hh = h.shift(1).rolling(24).max(); ll = l.shift(1).rolling(24).min()
    return Spec(_i8(np.where((z > 2) & (c > hh), 1, np.where((z < -2) & (c < ll), -1, 0))), (1.5 * a).to_numpy(), tp_mult=2.0, max_bars=24)


def _adx(df, n=14):
    h, l = df["high"], df["low"]; up, dn = h.diff(), -l.diff(); pdm = np.where((up > dn) & (up > 0), up, 0.0); mdm = np.where((dn > up) & (dn > 0), dn, 0.0)
    a = atr(df, n); pdi = 100 * pd.Series(pdm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / a; mdi = 100 * pd.Series(mdm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def q06_cta(df):
    c = df["close"]; a = _atr(df); f, s = ema(c, 96), ema(c, 384); adx = _adx(df)
    up = (f > s) & (f.shift(1) <= s.shift(1)) & (adx > 25); dn = (f < s) & (f.shift(1) >= s.shift(1)) & (adx > 25)
    ent = _i8(np.where(up, 1, np.where(dn, -1, 0)))
    ex = _i8(np.where((f > s) & (f.shift(1) <= s.shift(1)), 1, np.where((f < s) & (f.shift(1) >= s.shift(1)), -1, 0)))
    return Spec(ent, (2.0 * a).to_numpy(), exit=ex, tp_mult=0.0, max_bars=192)


SETUPS = {"P01 Envolvente en soporte/resistencia": p01_envolvente, "P02 Pin bar en techo/suelo": p02_pin_bar, "P03 Barrido de liquidez": p03_barrido,
          "P04 Ineficiencia (Fair Value Gap)": p04_fvg, "P05 Barra interior + tendencia": p05_barra_interior, "P06 Estrella de mañana/tarde": p06_estrella,
          "P07 Doble techo/suelo": p07_doble_techo_suelo, "Q01 Momentum de series temporales": q01_tsmom, "Q02 Reversión Ornstein-Uhlenbeck": q02_ou,
          "Q03 Régimen por razón de varianzas": q03_regimen_vr, "Q04 Expansión de volatilidad Garman-Klass": q04_garman_klass,
          "Q05 Desequilibrio de flujo": q05_flujo, "Q06 CTA EMA 96/384 + ADX": q06_cta}


def all_specs(df: pd.DataFrame) -> dict:
    return {k: f(df) for k, f in SETUPS.items()}
