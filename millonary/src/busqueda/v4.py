"""Búsqueda v4 (config/busqueda_v4_prerregistrada.md): patrones chartistas (Bulkowski), velas japonesas e ineficiencias, en 1 h, 4 h y diario.
Señal al CIERRE de la vela i (el motor entra en la apertura de i+1). Pivotes «fractales» de K velas a cada lado: un pivote en j solo se CONOCE en
j+K, así que nada mira al futuro (prueba de truncamiento en tests/test_busqueda_v4.py). Stop estructural (más allá del patrón + 0,25 ATR, entre
0,5 y 6 ATR). Rejilla: 17 familias × 2 filtros (sin filtro / a favor de tendencia) × 4 salidas (TP 1R ≈ regla de la medida, 2R, 3R, dejar correr).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr
from ..intraday.setups import Spec, _i8

K = 3                                   # velas a cada lado del pivote
MAX_BARS = {"1h": 72, "4h": 42, "1d": 20}
SALIDAS = ("TP1", "TP2", "TP3", "dejar_correr")
FILTROS = ("sin_filtro", "a_favor_tendencia")


def _base(df):
    return df["open"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy(), df["close"].to_numpy(), atr(df, 14).to_numpy()


def _pivots(h, l, k=K):
    """Listas por vela de confirmación: en la vela i se conocen los pivotes j ≤ i-k. Devuelve conf_hi[i] = (j, precio) o None."""
    n = len(h); ph = [None] * n; pl = [None] * n
    for j in range(k, n - k):
        if h[j] == h[j - k:j + k + 1].max() and h[j] > h[j - k:j].max():
            ph[j + k] = (j, h[j])
        if l[j] == l[j - k:j + k + 1].min() and l[j] < l[j - k:j].min():
            pl[j + k] = (j, l[j])
    return ph, pl


class _Out:
    def __init__(self, n):
        self.d = np.zeros(n, np.int8); self.st = np.full(n, np.nan)

    def set(self, i, d, dist, a):
        if self.d[i] == 0 and np.isfinite(dist) and np.isfinite(a) and a > 0:
            self.d[i] = d; self.st[i] = float(np.clip(dist + 0.25 * a, 0.5 * a, 6 * a))


# ------------------------------------------------------------------ patrones chartistas
def _scan(df, fn):
    o, h, l, c, a = _base(df); ph, pl = _pivots(h, l); out = _Out(len(c)); H, L = [], []
    for i in range(len(c)):
        if ph[i]: H.append(ph[i])
        if pl[i]: L.append(pl[i])
        if i > 0 and np.isfinite(a[i]):
            fn(i, o, h, l, c, a, H, L, out)
    return out


def p_doble_suelo(df, triple=False):
    """Doble (o triple) suelo: 2 (3) mínimos de pivote a ±1 ATR, separados ≥5 velas; ruptura al cierre de la línea de cuello (máximo entre ellos)
    en ≤40 velas desde el último mínimo. Stop bajo el mínimo del patrón."""
    m = 3 if triple else 2
    def fn(i, o, h, l, c, a, H, L, out):
        if len(L) < m: return
        P = L[-m:]; js = [p[0] for p in P]; ps = [p[1] for p in P]
        if max(ps) - min(ps) > a[i] or min(np.diff(js)) < 5 or i - js[-1] > 40: return
        neck = h[js[0]:js[-1] + 1].max()
        if c[i] > neck >= c[i - 1] and neck - min(ps) > a[i]:
            out.set(i, 1, c[i] - min(ps), a[i])
    return _scan(df, fn)


def p_doble_techo(df, triple=False):
    m = 3 if triple else 2
    def fn(i, o, h, l, c, a, H, L, out):
        if len(H) < m: return
        P = H[-m:]; js = [p[0] for p in P]; ps = [p[1] for p in P]
        if max(ps) - min(ps) > a[i] or min(np.diff(js)) < 5 or i - js[-1] > 40: return
        neck = l[js[0]:js[-1] + 1].min()
        if c[i] < neck <= c[i - 1] and max(ps) - neck > a[i]:
            out.set(i, -1, max(ps) - c[i], a[i])
    return _scan(df, fn)


def p_triples(df):
    a1, b1 = p_doble_suelo(df, True), p_doble_techo(df, True); out = _Out(len(df))
    out.d = np.where(a1.d != 0, a1.d, b1.d).astype(np.int8); out.st = np.where(a1.d != 0, a1.st, b1.st); return out


def p_hch(df):
    """Hombro-cabeza-hombro (techo → corto) e invertido (suelo → largo): cabeza ≥0,5 ATR más allá de hombros que difieren ≤1,5 ATR;
    cuello = valle más bajo (alto) entre hombros; ruptura al cierre en ≤40 velas desde el hombro derecho. Stop más allá del hombro derecho."""
    def fn(i, o, h, l, c, a, H, L, out):
        if len(H) >= 3:
            (j1, h1), (j2, h2), (j3, h3) = H[-3:]
            if h2 > max(h1, h3) + 0.5 * a[i] and abs(h1 - h3) <= 1.5 * a[i] and i - j3 <= 40:
                neck = l[j1:j3 + 1].min()
                if c[i] < neck <= c[i - 1]:
                    out.set(i, -1, h3 - c[i], a[i])
        if len(L) >= 3:
            (j1, l1), (j2, l2), (j3, l3) = L[-3:]
            if l2 < min(l1, l3) - 0.5 * a[i] and abs(l1 - l3) <= 1.5 * a[i] and i - j3 <= 40:
                neck = h[j1:j3 + 1].max()
                if c[i] > neck >= c[i - 1]:
                    out.set(i, 1, c[i] - l3, a[i])
    return _scan(df, fn)


def _lines(H, L, i, lb=60):
    if len(H) < 2 or len(L) < 2: return None
    (jh1, h1), (jh2, h2) = H[-2:]; (jl1, l1), (jl2, l2) = L[-2:]
    if i - min(jh1, jl1) > lb: return None
    sh = (h2 - h1) / (jh2 - jh1); sl = (l2 - l1) / (jl2 - jl1)
    return h2 + sh * (i - jh2), l2 + sl * (i - jl2), h1, h2, l1, l2


def p_triangulo(df, tipo):
    """Triángulos con los 2 últimos pivotes altos y bajos (≤60 velas): ascendente (techos iguales ±0,5 ATR, suelos crecientes) → ruptura alcista;
    descendente (suelos iguales, techos decrecientes) → ruptura bajista; simétrico (techos decrecientes y suelos crecientes) → ambos lados.
    Ruptura = cierre fuera de la línea; stop al otro lado del triángulo en esa vela."""
    def fn(i, o, h, l, c, a, H, L, out):
        z = _lines(H, L, i)
        if z is None: return
        up, dn, h1, h2, l1, l2 = z
        if up - dn < 0.5 * a[i]: return
        flat_h, flat_l = abs(h2 - h1) <= 0.5 * a[i], abs(l2 - l1) <= 0.5 * a[i]
        ok = {"ascendente": flat_h and l2 > l1 + 0.5 * a[i], "descendente": flat_l and h2 < h1 - 0.5 * a[i],
              "simetrico": h2 < h1 - 0.5 * a[i] and l2 > l1 + 0.5 * a[i]}[tipo]
        if not ok: return
        if c[i] > up and c[i - 1] <= up and tipo != "descendente":
            out.set(i, 1, c[i] - dn, a[i])
        elif c[i] < dn and c[i - 1] >= dn and tipo != "ascendente":
            out.set(i, -1, up - c[i], a[i])
    return _scan(df, fn)


def p_rectangulo(df):
    """Rectángulo: 2 techos y 2 suelos de pivote iguales (±0,5 ATR) en ≤60 velas, altura ≥1,5 ATR; ruptura al cierre por cualquier lado."""
    def fn(i, o, h, l, c, a, H, L, out):
        z = _lines(H, L, i)
        if z is None: return
        _, _, h1, h2, l1, l2 = z
        if abs(h2 - h1) > 0.5 * a[i] or abs(l2 - l1) > 0.5 * a[i]: return
        top, bot = max(h1, h2), min(l1, l2)
        if top - bot < 1.5 * a[i]: return
        if c[i] > top >= c[i - 1]: out.set(i, 1, c[i] - bot, a[i])
        elif c[i] < bot <= c[i - 1]: out.set(i, -1, top - c[i], a[i])
    return _scan(df, fn)


def p_bandera(df):
    """Bandera/banderín: mástil ≥4 ATR en ≤8 velas, consolidación de 3-15 velas que retrocede ≤50 % del mástil; ruptura al cierre del rango de la
    consolidación en la dirección del mástil. Stop al otro lado de la consolidación."""
    o, h, l, c, a = _base(df); n = len(c); out = _Out(n)
    for i in range(25, n):
        if not np.isfinite(a[i]): continue
        for w in range(3, 16):                                               # consolidación = velas i-w .. i-1
            s = i - w; ch, cl = h[s:i].max(), l[s:i].min()
            base_lo, base_hi = l[s - 8:s + 1].min(), h[s - 8:s + 1].max()
            pole_up, pole_dn = h[s] - base_lo, base_hi - l[s]
            if pole_up >= 4 * a[i] and h[s] >= ch and h[s] - cl <= 0.5 * pole_up and c[i] > ch >= c[i - 1]:
                out.set(i, 1, c[i] - cl, a[i]); break
            if pole_dn >= 4 * a[i] and l[s] <= cl and ch - l[s] <= 0.5 * pole_dn and c[i] < cl <= c[i - 1]:
                out.set(i, -1, ch - c[i], a[i]); break
    return out


def p_taza(df):
    """Taza con asa (O'Neil/Bulkowski): borde izquierdo (pivote alto A), fondo ≥3 ATR por debajo, borde derecho (pivote alto C a ±1 ATR de A,
    10-120 velas después), asa = retroceso desde C de ≤50 % de la profundidad durante 2-20 velas; ruptura al cierre sobre max(A, C). Stop bajo el asa."""
    def fn(i, o, h, l, c, a, H, L, out):
        if len(H) < 2: return
        (ja, A), (jc, C) = H[-2:]
        if not (10 <= jc - ja <= 120) or abs(A - C) > a[i] or not (2 <= i - jc <= 20): return
        B = l[ja:jc + 1].min(); depth = min(A, C) - B; handle = l[jc + 1:i].min() if i > jc + 1 else C
        rim = max(A, C)
        if depth >= 3 * a[i] and C - handle <= 0.5 * depth and c[i] > rim >= c[i - 1]:
            out.set(i, 1, c[i] - handle, a[i])
    return _scan(df, fn)


# ------------------------------------------------------------------ velas japonesas (contexto: tendencia de 10 velas antes del patrón)
def _candles(df, kind):
    o, h, l, c, a = _base(df); n = len(c); out = _Out(n); body = np.abs(c - o); rng = h - l
    for i in range(14, n):
        if not np.isfinite(a[i]): continue
        down = c[i - 3] < c[i - 13]; up = c[i - 3] > c[i - 13]                                 # tendencia previa al patrón
        if kind == "envolvente":
            if down and c[i] > o[i] and c[i - 1] < o[i - 1] and c[i] >= o[i - 1] and o[i] <= c[i - 1]:
                out.set(i, 1, c[i] - min(l[i], l[i - 1]), a[i])
            elif up and c[i] < o[i] and c[i - 1] > o[i - 1] and c[i] <= o[i - 1] and o[i] >= c[i - 1]:
                out.set(i, -1, max(h[i], h[i - 1]) - c[i], a[i])
        elif kind == "estrella":
            small = body[i - 1] <= 0.3 * rng[i - 1] if rng[i - 1] > 0 else False
            if down and c[i - 2] < o[i - 2] and body[i - 2] >= 0.6 * a[i] and small and c[i] > o[i] and c[i] > (o[i - 2] + c[i - 2]) / 2:
                out.set(i, 1, c[i] - min(l[i - 2:i + 1]), a[i])
            elif up and c[i - 2] > o[i - 2] and body[i - 2] >= 0.6 * a[i] and small and c[i] < o[i] and c[i] < (o[i - 2] + c[i - 2]) / 2:
                out.set(i, -1, max(h[i - 2:i + 1]) - c[i], a[i])
        elif kind == "tres_soldados":
            w = all(c[i - k] > o[i - k] and c[i - k] > c[i - k - 1] and body[i - k] >= 0.5 * a[i] for k in range(3))
            b = all(c[i - k] < o[i - k] and c[i - k] < c[i - k - 1] and body[i - k] >= 0.5 * a[i] for k in range(3))
            if w and down: out.set(i, 1, c[i] - l[i - 2], a[i])
            elif b and up: out.set(i, -1, h[i - 2] - c[i], a[i])
        elif kind == "tres_lineas":                                                                  # «three-line strike» (Bulkowski nº 1)
            b3 = all(c[i - k] < o[i - k] and c[i - k] < c[i - k - 1] for k in (1, 2, 3))
            w3 = all(c[i - k] > o[i - k] and c[i - k] > c[i - k - 1] for k in (1, 2, 3))
            if b3 and c[i] > o[i] and c[i] > o[i - 3]: out.set(i, 1, c[i] - min(l[i - 3:i + 1]), a[i])           # 3 negras + blanca que las envuelve
            elif w3 and c[i] < o[i] and c[i] < o[i - 3]: out.set(i, -1, max(h[i - 3:i + 1]) - c[i], a[i])
        elif kind == "martillo":
            lw, uw = min(o[i], c[i]) - l[i], h[i] - max(o[i], c[i])
            if rng[i] <= 0: continue
            if down and lw >= 2 * body[i] and lw >= 0.6 * rng[i] and l[i] <= l[i - 10:i].min(): out.set(i, 1, c[i] - l[i], a[i])
            elif up and uw >= 2 * body[i] and uw >= 0.6 * rng[i] and h[i] >= h[i - 10:i].max(): out.set(i, -1, h[i] - c[i], a[i])
        elif kind == "consecutivas":                                                                 # continuación tras 4 velas seguidas del mismo color
            if all(c[i - k] > o[i - k] for k in range(4)): out.set(i, 1, c[i] - l[i - 3:i + 1].min(), a[i])
            elif all(c[i - k] < o[i - k] for k in range(4)): out.set(i, -1, h[i - 3:i + 1].max() - c[i], a[i])
    return out


def i_fvg(df):
    """Ineficiencia (fair value gap): hueco ≥0,3 ATR entre la vela i-2 y la i con vela central impulsiva; válido 20 velas; entrada cuando el precio
    vuelve al hueco y cierra respetándolo. Stop al otro lado del hueco."""
    o, h, l, c, a = _base(df); n = len(c); out = _Out(n); zones = []
    for i in range(2, n):
        if not np.isfinite(a[i]): continue
        zones = [z for z in zones if i - z[3] <= 20]
        for z in list(zones):
            d, lo, hi, t = z
            if d == 1 and l[i] <= hi and c[i] > lo and i > t:
                out.set(i, 1, c[i] - min(lo, l[i]), a[i]); zones.remove(z)
            elif d == -1 and h[i] >= lo and c[i] < hi and i > t:
                out.set(i, -1, max(hi, h[i]) - c[i], a[i]); zones.remove(z)
        if l[i] - h[i - 2] >= 0.3 * a[i] and c[i - 1] > o[i - 1]: zones.append((1, h[i - 2], l[i], i))
        if l[i - 2] - h[i] >= 0.3 * a[i] and c[i - 1] < o[i - 1]: zones.append((-1, h[i], l[i - 2], i))
    return out


FAMILIAS = {
    "B01 Doble suelo": lambda d: p_doble_suelo(d), "B02 Doble techo": lambda d: p_doble_techo(d), "B03 Triple suelo/techo": p_triples,
    "B04 Hombro-cabeza-hombro (y HCH invertido)": p_hch, "B05 Triángulo ascendente": lambda d: p_triangulo(d, "ascendente"),
    "B06 Triángulo descendente": lambda d: p_triangulo(d, "descendente"), "B07 Triángulo simétrico": lambda d: p_triangulo(d, "simetrico"),
    "B08 Rectángulo": p_rectangulo, "B09 Bandera / banderín": p_bandera, "B10 Taza con asa": p_taza,
    "V01 Envolvente de giro": lambda d: _candles(d, "envolvente"), "V02 Estrella de la mañana / tarde": lambda d: _candles(d, "estrella"),
    "V03 Tres soldados / tres cuervos": lambda d: _candles(d, "tres_soldados"), "V04 Tres líneas (three-line strike)": lambda d: _candles(d, "tres_lineas"),
    "V05 Martillo / estrella fugaz en extremo": lambda d: _candles(d, "martillo"), "V06 Cuatro velas seguidas (continuación)": lambda d: _candles(d, "consecutivas"),
    "I01 Ineficiencia (FVG) 4 h / diario": i_fvg}


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | familia | filtro | salida». 17 × 2 × 4 = 136 variantes por temporalidad (408 en total)."""
    c = df["close"]; e50, e200 = ema(c, 50), ema(c, 200); a = atr(df, 14).to_numpy()
    up = ((c > e200) & (e50 > e200)).to_numpy(); dn = ((c < e200) & (e50 < e200)).to_numpy()
    trail = _i8(np.where(c < e50, -1, np.where(c > e50, 1, 0))); out = {}
    for name, fn in FAMILIAS.items():
        r = fn(df); base = r.d.astype(np.int8); st = np.where(np.isnan(r.st), 2 * a, r.st)
        for fil in FILTROS:
            d = base if fil == "sin_filtro" else np.where((base == 1) & up, 1, np.where((base == -1) & dn, -1, 0)).astype(np.int8)
            for sal in SALIDAS:
                tp = 0.0 if sal == "dejar_correr" else float(sal[2:])
                out[f"{tf} | {name} | {fil} | {sal}"] = Spec(_i8(d), st, exit=trail if sal == "dejar_correr" else None, tp_mult=tp,
                                                             max_bars=0 if sal == "dejar_correr" else MAX_BARS[tf])
    return out
