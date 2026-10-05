"""Búsqueda v6 (config/busqueda_v6_prerregistrada.md): más combinaciones sobre los patrones que funcionan (doble suelo, triple suelo/techo,
bandera; y cuatro velas seguidas en 4 h). Nuevas confirmaciones: DOBLES (tendencia+volumen, tendencia+barrido, tendencia+compresión,
volumen+compresión, barrido+volumen), funding a contrapié, tendencia+funding, vela de ruptura fuerte y entrada en el RETESTEO de la línea de cuello.
Todo causal (prueba de truncamiento en tests/test_busqueda_v6.py). df puede traer la columna "f" (funding por vela); si falta, se toma 0.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8
from .v4 import _base, _Out, _candles
from .v5 import _extremos, BARS_DAY

MAX_BARS = {"1h": 72, "4h": 42}
SALIDAS = ("TP3", "dejar_correr")
CONF = ["P1 tendencia + volumen", "P2 tendencia + barrido", "P3 tendencia + compresión", "P4 volumen + compresión", "P5 barrido + volumen",
        "P6 funding a contrapié", "P7 tendencia + funding", "P8 vela de ruptura fuerte", "P9 entrada en el retesteo"]
GIRO_ONLY = {"P2 tendencia + barrido", "P5 barrido + volumen"}
NEED_LEVEL = {"P9 entrada en el retesteo"}


def _bandera_meta(df):
    """Bandera/banderín idéntica a la v4 + nivel de ruptura y extremo de la consolidación: meta[i] = (nivel, extremo)."""
    o, h, l, c, a = _base(df); n = len(c); out = _Out(n); meta = [None] * n
    for i in range(25, n):
        if not np.isfinite(a[i]): continue
        for w in range(3, 16):
            s = i - w; ch, cl = h[s:i].max(), l[s:i].min()
            base_lo, base_hi = l[s - 8:s + 1].min(), h[s - 8:s + 1].max()
            pole_up, pole_dn = h[s] - base_lo, base_hi - l[s]
            if pole_up >= 4 * a[i] and h[s] >= ch and h[s] - cl <= 0.5 * pole_up and c[i] > ch >= c[i - 1]:
                out.set(i, 1, c[i] - cl, a[i]); meta[i] = (ch, cl, None); break
            if pole_dn >= 4 * a[i] and l[s] <= cl and ch - l[s] <= 0.5 * pole_dn and c[i] < cl <= c[i - 1]:
                out.set(i, -1, ch - c[i], a[i]); meta[i] = (cl, ch, None); break
    return out, meta


def _giro_meta(df, kind):
    """Doble suelo / triple suelo-techo de la v5 → meta[i] = (cuello, extremo, barrido: bool)."""
    o, h, l, c, a = _base(df); r, m5 = _extremos(df, kind); meta = [None] * len(c)
    for i in np.flatnonzero(r.d):
        j0, j1, p0, plast, prev = m5[i]; s = r.d[i]
        if s == 1: meta[i] = (h[j0:j1 + 1].max(), min(p0, plast, prev), plast < prev)
        else: meta[i] = (l[j0:j1 + 1].min(), max(p0, plast, prev), plast > prev)
    return r, meta


def _filters(df, tf):
    o, h, l, c, a = _base(df); v = df["volume"].to_numpy(); bd = BARS_DAY[tf]
    e = ema(df["close"], 50 * bd).to_numpy(); a100 = atr(df, 100).to_numpy(); vm = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
    f = df["f"].to_numpy() if "f" in df else np.zeros(len(c)); f24 = pd.Series(f).rolling(bd).sum(); med = f24.rolling(30 * bd, min_periods=10 * bd).median()
    f24, med = f24.to_numpy(), med.to_numpy(); rng = h - l
    a_prev = np.r_[np.nan, a[:-1]]; a100_prev = np.r_[np.nan, a100[:-1]]
    return {"T": lambda s: (c > e) if s == 1 else (c < e), "V": lambda s: v >= 1.5 * vm, "C": lambda s: a_prev < 0.9 * a100_prev,
            "F": lambda s: (f24 <= med) if s == 1 else (f24 >= med),
            "S": lambda s: ((c - l) >= 0.75 * rng) & (c > o) if s == 1 else ((h - c) >= 0.75 * rng) & (c < o)}


def _apply(df, tf, base, st, meta, conf):
    F = _filters(df, tf); o, h, l, c, a = _base(df); n = len(c)
    if conf == "P9 entrada en el retesteo":                         # tras la ruptura, esperar ≤10 velas a que el precio vuelva al cuello y cierre del lado bueno
        d = np.zeros(n, np.int8); stp = np.full(n, np.nan)
        for i in np.flatnonzero(base):
            s = base[i]; N, X, _ = meta[i]
            for t in range(i + 1, min(i + 11, n)):
                if (s == 1 and c[t] < X) or (s == -1 and c[t] > X): break                     # invalidado: cerró más allá del extremo del patrón
                touch = (l[t] <= N + 0.2 * a[t] and c[t] > N) if s == 1 else (h[t] >= N - 0.2 * a[t] and c[t] < N)
                if touch and d[t] == 0:
                    d[t] = s; stp[t] = float(np.clip(s * (c[t] - X) + 0.25 * a[t], 0.5 * a[t], 6 * a[t])); break
        return d, np.where(np.isnan(stp), 2 * a, stp)
    req = {"P1 tendencia + volumen": "TV", "P2 tendencia + barrido": "TB", "P3 tendencia + compresión": "TC", "P4 volumen + compresión": "VC",
           "P5 barrido + volumen": "BV", "P6 funding a contrapié": "F", "P7 tendencia + funding": "TF", "P8 vela de ruptura fuerte": "S"}[conf]
    ok = np.zeros(n, bool)
    for s in (1, -1):
        m = base == s
        for k in req:
            if k == "B": m = m & np.array([bool(meta[i] and meta[i][2]) for i in range(n)])
            else: m = m & np.nan_to_num(F[k](s), nan=0).astype(bool)
        ok |= m
    return np.where(ok, base, 0).astype(np.int8), st


GRUPOS = {"D01 Doble suelo": ("giro", "doble_suelo"), "D02 Triple suelo/techo": ("giro", "triple"), "D03 Bandera / banderín": ("bandera", None),
          "D04 Cuatro velas seguidas": ("velas", None)}
TF_GRUPO = {"D01 Doble suelo": ("1h", "4h"), "D02 Triple suelo/techo": ("1h", "4h"), "D03 Bandera / banderín": ("1h", "4h"), "D04 Cuatro velas seguidas": ("4h",)}


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | grupo | combinación | salida». 1 h: (2 giros × 9 + bandera × 7) × 2 = 50; 4 h: 50 + cuatro velas × 6 × 2 = 62. Total 112."""
    c = df["close"]; e50 = ema(c, 50); a = atr(df, 14).to_numpy()
    trail = _i8(np.where(c < e50, -1, np.where(c > e50, 1, 0))); out = {}
    for name, (kind, sub) in GRUPOS.items():
        if tf not in TF_GRUPO[name]: continue
        if kind == "giro": r, meta = _giro_meta(df, sub)
        elif kind == "bandera": r, meta = _bandera_meta(df)
        else: r, meta = _candles(df, "consecutivas"), None
        base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for conf in CONF:
            if conf in GIRO_ONLY and kind != "giro": continue
            if conf in NEED_LEVEL and meta is None: continue
            d, stp = _apply(df, tf, base, st, meta, conf)
            for sal in SALIDAS:
                tp = 0.0 if sal == "dejar_correr" else float(sal[2:])
                out[f"{tf} | {name} | {conf} | {sal}"] = Spec(_i8(d), stp, exit=trail if sal == "dejar_correr" else None, tp_mult=tp,
                                                              max_bars=0 if sal == "dejar_correr" else MAX_BARS[tf])
    return out
