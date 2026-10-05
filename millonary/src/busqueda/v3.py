"""Búsqueda v3 (config/busqueda_v3_prerregistrada.md): lo que publican fondos, investigadores y traders conocidos y que AÚN no habíamos probado.
11 familias, 28 variantes, en 1 h / 4 h / diario. Señales AL CIERRE de la vela i (el motor entra en la apertura de i+1); todo causal
(prueba de truncamiento en tests/test_busqueda_v3.py). Horas en UTC; el índice es la hora de APERTURA de la vela.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr, rsi
from ..intraday.setups import Spec, _i8


def _a(df, n=14):
    return atr(df, n)


# ---------------------------------------------------------------- 1 h
def n1_ruido(df, k=1.0, solo_largos=False):
    """Zona de ruido (Zarattini-Aziz-Barbon 2024, adaptado a BTC 24/7): apertura del día UTC ± k × media de 14 días del movimiento absoluto
    desde la apertura a esa misma hora. Cierre fuera de la zona = tendencia del día. Salida: cierre al otro lado del VWAP del día."""
    o, c, v = df["open"], df["close"], df["volume"]; day = df.index.floor("1D"); hr = df.index.hour
    d_open = o.groupby(day).transform("first"); mv = (c / d_open - 1).abs()
    sig = pd.DataFrame({"mv": mv.to_numpy(), "hr": hr, "day": day}, index=df.index)
    piv = sig.pivot_table(index="day", columns="hr", values="mv")                      # días × horas
    sm = piv.rolling(14, min_periods=14).mean().shift(1)                               # solo días ANTERIORES
    s = pd.Series(sm.stack().reindex(pd.MultiIndex.from_arrays([day, hr])).to_numpy(), index=df.index)
    up, lo = d_open * (1 + k * s), d_open * (1 - k * s)
    tp_ = (df["high"] + df["low"] + c) / 3; vw = (tp_ * v).groupby(day).cumsum() / v.groupby(day).cumsum()
    long_ = (c > up) & (c > vw); short = (c < lo) & (c < vw) & (not solo_largos)
    ex = _i8(np.where(c < vw, -1, np.where(c > vw, 1, 0)))
    return Spec(_i8(np.where(long_, 1, np.where(short, -1, 0))), (2.0 * _a(df)).to_numpy(), exit=ex, tp_mult=0.0, max_bars=24)


def n2_lunes_asia(df, hold):
    """Efecto apertura de Asia del lunes (Concretum 2025): largo desde el domingo 23:00 UTC (≈19:00 Nueva York, abre Tokio)."""
    m = (df.index.dayofweek == 6) & (df.index.hour == 22)
    return Spec(_i8(np.where(m, 1, 0)), (6.0 * _a(df)).to_numpy(), tp_mult=0.0, max_bars=hold)


def n3_noche_wall_street(df, dias, filtro_max):
    """Noche de Wall Street (Quantpedia 2024): BTC sube sobre todo con la bolsa CERRADA. Largo al cierre de NYSE (20:00 UTC) y fuera
    a la apertura (14:00 UTC, 18 h). Opcional: solo si el cierre diario de ayer fue máximo de 10 días (MAX(10))."""
    dow, hr = df.index.dayofweek, df.index.hour; m = np.isin(dow, dias) & (hr == 19)
    if filtro_max:
        dc = df["close"].resample("1D").last(); atmax = (dc >= dc.rolling(10).max()).shift(1)      # día ANTERIOR completo
        m = m & atmax.reindex(df.index.floor("1D")).fillna(False).to_numpy()
    return Spec(_i8(np.where(m, 1, 0)), (6.0 * _a(df)).to_numpy(), tp_mult=0.0, max_bars=18)


def n4_ventana_21_23(df, solo_laborables):
    """Ventana 21:00-23:59 UTC (estudios de estacionalidad horaria: la franja más rentable y significativa tras el cierre de las bolsas)."""
    m = df.index.hour == 20
    if solo_laborables:
        m = m & (df.index.dayofweek < 5)
    return Spec(_i8(np.where(m, 1, 0)), (3.0 * _a(df)).to_numpy(), tp_mult=0.0, max_bars=3)


# ---------------------------------------------------------------- 4 h / diario
def n11_conjunto_tendencias(df, solo_largos):
    """Conjunto de tendencias tipo CTA (AHL/Winton/Clenow): voto de 3 cruces EMA 8/32, 16/64, 32/128. Entra cuando votan los 3; sale cuando la mayoría gira."""
    c = df["close"]; sc = sum(np.sign(ema(c, f) - ema(c, 4 * f)) for f in (8, 16, 32)) / 3
    long_ = (sc == 1) & (sc.shift(1) < 1); short = (sc == -1) & (sc.shift(1) > -1) & (not solo_largos)
    ex = _i8(np.where(sc <= -1 / 3, -1, np.where(sc >= 1 / 3, 1, 0)))
    return Spec(_i8(np.where(long_, 1, np.where(short, -1, 0))), (3.0 * _a(df)).to_numpy(), exit=ex, tp_mult=0.0, max_bars=0)


# ---------------------------------------------------------------- diario
def n5_max(df, n):
    """MAX(n) (Quantpedia): comprar cuando el cierre es máximo de n días; mantener mientras siga en máximos."""
    c = df["close"]; at = c >= c.rolling(n).max()
    return Spec(_i8(np.where(at, 1, 0)), (2.0 * _a(df)).to_numpy(), exit=_i8(np.where(~at, -1, 0)), tp_mult=0.0, max_bars=0)


def n6_min(df, n):
    """MIN(n) (Quantpedia): comprar el cierre en mínimo de n días (reversión); vender cuando deja de marcar mínimos."""
    c = df["close"]; at = c <= c.rolling(n).min()
    return Spec(_i8(np.where(at, 1, 0)), (2.0 * _a(df)).to_numpy(), exit=_i8(np.where(~at, -1, 0)), tp_mult=0.0, max_bars=0)


def n7_connors_rsi2(df, umbral):
    """RSI(2) de Larry Connors: sobre la media de 200 días, comprar con RSI(2) < umbral; vender al cerrar sobre la media de 5."""
    c = df["close"]; r2 = rsi(c, 2); m200 = c.rolling(200).mean(); m5 = c.rolling(5).mean()
    return Spec(_i8(np.where((c > m200) & (r2 < umbral), 1, 0)), (3.0 * _a(df)).to_numpy(), exit=_i8(np.where(c > m5, -1, 0)), tp_mult=0.0, max_bars=10)


def n8_ibs(df, filtro_tendencia):
    """IBS (fuerza interna de la vela, literatura de reversión diaria): cierre en el 20 % bajo del rango → comprar 1 día."""
    c, h, l = df["close"], df["high"], df["low"]; ibs = (c - l) / (h - l).replace(0, np.nan); m = ibs < 0.2
    if filtro_tendencia:
        m = m & (c > c.rolling(200).mean())
    return Spec(_i8(np.where(m, 1, 0)), (3.0 * _a(df)).to_numpy(), tp_mult=0.0, max_bars=1)


def n9_weinstein(df, n_ma):
    """Etapa 2 de Stan Weinstein: precio sobre una media larga ASCENDENTE y ruptura del máximo de 50 días; se deja correr hasta cerrar bajo la media."""
    c = df["close"]; m = c.rolling(n_ma).mean(); hh = df["high"].shift(1).rolling(50).max()
    ent = (c > m) & (m > m.shift(20)) & (c > hh)
    return Spec(_i8(np.where(ent, 1, 0)), (3.0 * _a(df)).to_numpy(), exit=_i8(np.where(c < m, -1, 0)), tp_mult=0.0, max_bars=0)


def n10_maximo_anual(df, mult):
    """Máximos de 52 semanas (George-Hwang; Minervini/Darvas): cierre en máximo de 365 días; salida chandelier (máx. 22 días − mult × ATR 22)."""
    c = df["close"]; ent = c >= c.rolling(365).max(); ch = df["high"].rolling(22).max() - mult * _a(df, 22)
    return Spec(_i8(np.where(ent, 1, 0)), (mult * _a(df, 22)).to_numpy(), exit=_i8(np.where(c < ch, -1, 0)), tp_mult=0.0, max_bars=0)


FAMILIAS = {
    "N01 Zona de ruido (Zarattini)": "1h", "N02 Apertura de Asia del lunes (Concretum)": "1h", "N03 Noche de Wall Street (Quantpedia)": "1h",
    "N04 Ventana 21-23 UTC": "1h", "N05 MAX de n días (Quantpedia)": "1d", "N06 MIN de n días (Quantpedia)": "1d", "N07 RSI(2) de Connors": "1d",
    "N08 IBS": "1d", "N09 Etapa 2 de Weinstein": "1d", "N10 Máximo anual + chandelier": "1d", "N11 Conjunto de tendencias CTA": "4h/1d"}


def variants(df: pd.DataFrame, tf: str) -> dict[str, Spec]:
    """Clave «tf | familia | variante». 28 variantes en total (12 en 1 h, 2 en 4 h, 14 en diario)."""
    v: dict[str, Spec] = {}
    if tf == "1h":
        for k in (1.0, 1.5):
            for sl in (False, True):
                v[f"1h | N01 Zona de ruido (Zarattini) | k={k} {'solo_largos' if sl else 'ambos'}"] = n1_ruido(df, k, sl)
        for hd in (8, 16, 24):
            v[f"1h | N02 Apertura de Asia del lunes (Concretum) | {hd} h"] = n2_lunes_asia(df, hd)
        v["1h | N03 Noche de Wall Street (Quantpedia) | lun-jue"] = n3_noche_wall_street(df, [0, 1, 2, 3], False)
        v["1h | N03 Noche de Wall Street (Quantpedia) | lun-mar"] = n3_noche_wall_street(df, [0, 1], False)
        v["1h | N03 Noche de Wall Street (Quantpedia) | lun-mar + MAX10"] = n3_noche_wall_street(df, [0, 1], True)
        v["1h | N04 Ventana 21-23 UTC | todos los días"] = n4_ventana_21_23(df, False)
        v["1h | N04 Ventana 21-23 UTC | laborables"] = n4_ventana_21_23(df, True)
    if tf == "4h":
        for sl in (False, True):
            v[f"4h | N11 Conjunto de tendencias CTA | {'solo_largos' if sl else 'ambos'}"] = n11_conjunto_tendencias(df, sl)
    if tf == "1d":
        for n in (10, 20):
            v[f"1d | N05 MAX de n días (Quantpedia) | n={n}"] = n5_max(df, n)
            v[f"1d | N06 MIN de n días (Quantpedia) | n={n}"] = n6_min(df, n)
        for u in (10, 5):
            v[f"1d | N07 RSI(2) de Connors | RSI2<{u}"] = n7_connors_rsi2(df, u)
        for ft in (False, True):
            v[f"1d | N08 IBS | {'sobre media 200' if ft else 'sin filtro'}"] = n8_ibs(df, ft)
        for m in (150, 100):
            v[f"1d | N09 Etapa 2 de Weinstein | media {m}"] = n9_weinstein(df, m)
        for m in (3.0, 4.0):
            v[f"1d | N10 Máximo anual + chandelier | {m:.0f} ATR"] = n10_maximo_anual(df, m)
        for sl in (False, True):
            v[f"1d | N11 Conjunto de tendencias CTA | {'solo_largos' if sl else 'ambos'}"] = n11_conjunto_tendencias(df, sl)
    return v
