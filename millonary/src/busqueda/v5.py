"""Búsqueda v5 (config/busqueda_v5_prerregistrada.md): patrones que funcionaron en la v4 LIGADOS a una confirmación clásica, más cuñas.
Patrones: doble suelo, doble techo, triple suelo/techo (giro) y bandera/banderín (continuación) en 1 h y 4 h; cuña (nueva).
Confirmaciones (condición Y en la vela de ruptura): K0 ninguna (control), K1 divergencia RSI(14) entre los extremos del patrón, K2 volumen de ruptura
≥1,5× la media de 20, K3 tendencia de temporalidad superior (EMA de 50 días), K4 barrido de liquidez (el último extremo supera al anterior),
K5 ineficiencia (FVG) creada por la ruptura, K6 volatilidad comprimida antes de la ruptura (ATR14/ATR100 < 0,9). K1 y K4 solo en patrones de giro.
Todo causal (pivotes conocidos K velas después; prueba de truncamiento en tests/test_busqueda_v5.py).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8
from .v4 import _base, _pivots, _Out, _lines, p_bandera

MAX_BARS = {"1h": 72, "4h": 42}
BARS_DAY = {"1h": 24, "4h": 6}
SALIDAS = ("TP2", "TP3", "dejar_correr")
CONF = {"K0 ninguna": None, "K1 divergencia RSI": "giro", "K2 volumen de ruptura": "all", "K3 tendencia superior (EMA 50 días)": "all",
        "K4 barrido de liquidez": "giro", "K5 FVG en la ruptura": "all", "K6 volatilidad comprimida": "all"}


def _extremos(df, kind):
    """Como v4 (doble/triple suelo/techo) pero guarda los índices de los extremos del patrón: meta[i] = (j_primero, j_último)."""
    o, h, l, c, a = _base(df); ph, pl = _pivots(h, l); n = len(c); out = _Out(n); meta = [None] * n; H, L = [], []
    m = 3 if kind.startswith("triple") else 2
    for i in range(n):
        if ph[i]: H.append(ph[i])
        if pl[i]: L.append(pl[i])
        if i == 0 or not np.isfinite(a[i]): continue
        if kind in ("doble_suelo", "triple") and len(L) >= m:
            P = L[-m:]; js = [p[0] for p in P]; ps = [p[1] for p in P]
            if max(ps) - min(ps) <= a[i] and min(np.diff(js)) >= 5 and i - js[-1] <= 40:
                neck = h[js[0]:js[-1] + 1].max()
                if c[i] > neck >= c[i - 1] and neck - min(ps) > a[i]:
                    out.set(i, 1, c[i] - min(ps), a[i]); meta[i] = (js[0], js[-1], ps[0], ps[-1], min(ps[:-1]))
        if kind in ("doble_techo", "triple") and len(H) >= m and out.d[i] == 0:
            P = H[-m:]; js = [p[0] for p in P]; ps = [p[1] for p in P]
            if max(ps) - min(ps) <= a[i] and min(np.diff(js)) >= 5 and i - js[-1] <= 40:
                neck = l[js[0]:js[-1] + 1].min()
                if c[i] < neck <= c[i - 1] and max(ps) - neck > a[i]:
                    out.set(i, -1, max(ps) - c[i], a[i]); meta[i] = (js[0], js[-1], ps[0], ps[-1], max(ps[:-1]))
    return out, meta


def p_cuna(df):
    """Cuña (Bulkowski): 2 últimos pivotes altos y bajos (≤60 velas) con las DOS líneas en la misma dirección y convergiendo. Cuña descendente →
    ruptura alcista de la línea superior (largo); cuña ascendente → ruptura bajista de la inferior (corto). Stop al otro lado."""
    o, h, l, c, a = _base(df); ph, pl = _pivots(h, l); n = len(c); out = _Out(n); H, L = [], []
    for i in range(n):
        if ph[i]: H.append(ph[i])
        if pl[i]: L.append(pl[i])
        if i == 0 or not np.isfinite(a[i]): continue
        z = _lines(H, L, i)
        if z is None: continue
        up, dn, h1, h2, l1, l2 = z
        if up - dn < 0.5 * a[i]: continue
        falling = h2 < h1 - 0.5 * a[i] and l2 < l1 and (h1 - h2) > (l1 - l2)
        rising = l2 > l1 + 0.5 * a[i] and h2 > h1 and (l2 - l1) > (h2 - h1)
        if falling and c[i] > up >= c[i - 1]: out.set(i, 1, c[i] - dn, a[i])
        elif rising and c[i] < dn <= c[i - 1]: out.set(i, -1, up - c[i], a[i])
    return out


def _confirm(df, tf, d, meta, conf):
    if conf == "K0 ninguna": return d
    o, h, l, c, a = _base(df); v = df["volume"].to_numpy(); n = len(c); r = rsi(df["close"], 14).to_numpy()
    e = ema(df["close"], 50 * BARS_DAY[tf]).to_numpy(); a100 = atr(df, 100).to_numpy(); vm = pd.Series(v).shift(1).rolling(20).mean().to_numpy()
    ok = np.zeros(n, bool)
    for i in np.flatnonzero(d):
        s = d[i]
        if conf.startswith("K1"):
            if meta is None or meta[i] is None: continue
            j1, j2 = meta[i][0], meta[i][1]; ok[i] = (r[j2] > r[j1]) if s == 1 else (r[j2] < r[j1])
        elif conf.startswith("K2"): ok[i] = v[i] >= 1.5 * vm[i]
        elif conf.startswith("K3"): ok[i] = (c[i] > e[i]) if s == 1 else (c[i] < e[i])
        elif conf.startswith("K4"):
            if meta is None or meta[i] is None: continue
            last, prev = meta[i][3], meta[i][4]; ok[i] = (last < prev) if s == 1 else (last > prev)
        elif conf.startswith("K5"): ok[i] = (l[i] > h[i - 2]) if s == 1 else (h[i] < l[i - 2])
        elif conf.startswith("K6"): ok[i] = a[i - 1] < 0.9 * a100[i - 1]
    return np.where(ok, d, 0).astype(np.int8)


PATRONES = {"C01 Doble suelo": "doble_suelo", "C02 Doble techo": "doble_techo", "C03 Triple suelo/techo": "triple", "C04 Bandera / banderín": "bandera",
            "C05 Cuña": "cuna"}


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | patrón | confirmación | salida». Por temporalidad: 3 giros × 7 × 3 + bandera × 5 × 3 + cuña × 2 (K0, K3) × 3 = 84 (168 en total)."""
    c = df["close"]; e50 = ema(c, 50); a = atr(df, 14).to_numpy()
    trail = _i8(np.where(c < e50, -1, np.where(c > e50, 1, 0))); out = {}
    for name, kind in PATRONES.items():
        if kind == "bandera": r, meta = p_bandera(df), None
        elif kind == "cuna": r, meta = p_cuna(df), None
        else: r, meta = _extremos(df, kind)
        base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for conf, scope in CONF.items():
            if scope == "giro" and meta is None: continue
            if kind == "cuna" and conf not in ("K0 ninguna", "K3 tendencia superior (EMA 50 días)"): continue
            d = _confirm(df, tf, base, meta, conf)
            for sal in SALIDAS:
                tp = 0.0 if sal == "dejar_correr" else float(sal[2:])
                out[f"{tf} | {name} | {conf} | {sal}"] = Spec(_i8(d), st, exit=trail if sal == "dejar_correr" else None, tp_mult=tp,
                                                              max_bars=0 if sal == "dejar_correr" else MAX_BARS[tf])
    return out
