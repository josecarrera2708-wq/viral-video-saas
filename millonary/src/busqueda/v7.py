"""Búsqueda v7 (config/busqueda_v7_prerregistrada.md): más combinaciones sobre doble suelo, triple suelo/techo y bandera (1 h y 4 h).
Combinaciones nuevas: Q1 tendencia + volumen + funding (triple), Q2 funding + volumen, Q3 «patrón dentro de patrón» (el patrón de 1 h coincide con
un patrón de 4 h en la misma dirección en las últimas 24 h; solo 1 h), Q4 ruptura en horario de Wall Street (13-21 UTC), Q5 RSI(14) no extremo
(<70 largos, >30 cortos). Salidas: TP 3R, dejar correr (EMA50) y dejar correr rápido (EMA20). Patrones idénticos a v4-v6. Todo causal.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8
from .v4 import _base
from .v6 import _giro_meta, _bandera_meta, _filters

MAX_BARS = {"1h": 72, "4h": 42}
SALIDAS = ("TP3", "dejar_correr", "dejar_correr_rapido")
GRUPOS = {"E01 Doble suelo": ("giro", "doble_suelo"), "E02 Triple suelo/techo": ("giro", "triple"), "E03 Bandera / banderín": ("bandera", None)}
COMB = ["Q1 tendencia + volumen + funding", "Q2 funding + volumen", "Q3 patrón dentro de patrón (4 h)", "Q4 ruptura en horario de Wall Street",
        "Q5 RSI no extremo"]


def _patron(df, kind, sub):
    return _giro_meta(df, sub) if kind == "giro" else _bandera_meta(df)


def _q3_mask(df):
    """Para 1 h: dirección de los patrones de 4 h (doble suelo, triple, bandera) disponibles (vela de 4 h CERRADA) en las últimas 24 h."""
    cols = ["open", "high", "low", "close", "volume"]
    g = df[cols].resample("4h", label="left", closed="left")
    d4 = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})[g["close"].count() == 4].dropna()
    sig = np.zeros(len(d4), np.int8)
    for kind, sub in GRUPOS.values():
        r, _ = _patron(d4, kind, sub); sig = np.where(sig == 0, r.d, sig).astype(np.int8)
    avail = d4.index + pd.Timedelta("4h"); close_t = df.index + pd.Timedelta("1h"); out = {}
    for s in (1, -1):
        t = avail[sig == s].values
        if len(t) == 0: out[s] = np.zeros(len(df), bool); continue
        k = np.searchsorted(t, close_t.values, side="right") - 1
        last = np.where(k >= 0, t[np.clip(k, 0, None)], np.datetime64("NaT"))
        out[s] = (k >= 0) & ((close_t.values - last) <= np.timedelta64(24, "h"))
    return out


def _apply(df, tf, base, conf, q3=None):
    F = _filters(df, tf); n = len(df); o, h, l, c, a = _base(df); r14 = rsi(df["close"], 14).to_numpy(); hr = df.index.hour.to_numpy()
    ok = np.zeros(n, bool)
    for s in (1, -1):
        m = base == s
        if conf.startswith("Q1"): m = m & F["T"](s) & F["V"](s) & F["F"](s)
        elif conf.startswith("Q2"): m = m & F["V"](s) & F["F"](s)
        elif conf.startswith("Q3"): m = m & q3[s]
        elif conf.startswith("Q4"):
            close_hr = (hr + (1 if tf == "1h" else 4)) % 24
            m = m & (close_hr >= 13) & (close_hr <= 21) if tf == "1h" else m & np.isin(hr, [12, 16])
        elif conf.startswith("Q5"): m = m & ((r14 < 70) if s == 1 else (r14 > 30))
        ok |= np.nan_to_num(m, nan=0).astype(bool)
    return np.where(ok, base, 0).astype(np.int8)


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | grupo | combinación | salida». 1 h: 3 × 5 × 3 = 45; 4 h: 3 × 4 × 3 = 36. Total 81."""
    c = df["close"]; a = atr(df, 14).to_numpy(); out = {}
    trail = {"dejar_correr": _i8(np.where(c < ema(c, 50), -1, np.where(c > ema(c, 50), 1, 0))),
             "dejar_correr_rapido": _i8(np.where(c < ema(c, 20), -1, np.where(c > ema(c, 20), 1, 0)))}
    q3 = _q3_mask(df) if tf == "1h" else None
    for name, (kind, sub) in GRUPOS.items():
        r, _ = _patron(df, kind, sub); base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for conf in COMB:
            if conf.startswith("Q3") and tf != "1h": continue
            d = _apply(df, tf, base, conf, q3)
            for sal in SALIDAS:
                tp = float(sal[2:]) if sal.startswith("TP") else 0.0
                out[f"{tf} | {name} | {conf} | {sal}"] = Spec(_i8(d), st, exit=trail.get(sal), tp_mult=tp, max_bars=MAX_BARS[tf] if tp else 0)
    return out
