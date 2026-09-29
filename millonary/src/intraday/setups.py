"""Mesa intradía: 14 traders sobre velas de 1 h con STOP por ATR/estructura, TAKE-PROFIT en múltiplos de R y salida por tiempo.

Cada setup devuelve las señales AL CIERRE de la vela i (el motor entra en la apertura de i+1). Todos los indicadores son causales.
Parámetros FIJOS (config/intradia_prerregistrada.md); solo se calibró la FRECUENCIA de señales, sin mirar resultados.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from ..signals.indicators import sma, ema, atr, rsi, bollinger
from ..incubator.setups import _psar, s11_supertrend


@dataclass
class Spec:
    entry: np.ndarray
    stop: np.ndarray
    exit: np.ndarray | None = None
    tp_mult: float = 2.0
    max_bars: int = 24


def _i8(x) -> np.ndarray:
    return np.nan_to_num(np.asarray(x, float), nan=0.0).astype(np.int8)


def _first_per_day(sig: pd.Series, idx: pd.DatetimeIndex) -> np.ndarray:
    """Solo la primera señal de cada día UTC (una operación por día como máximo)."""
    s = pd.Series(np.asarray(sig), index=idx); day = idx.floor("1D"); seen = (s != 0).groupby(day).cumsum()
    return np.where((s != 0) & (seen == 1), s, 0)


def _stop(df, k, a=None):
    a = atr(df, 14) if a is None else a
    return (k * a).to_numpy()


def i01_rango_asiatico(df):
    h, l, c = df["high"], df["low"], df["close"]; hr = df.index.hour; day = df.index.floor("1D")
    asia = (hr < 8); ah = h.where(asia).groupby(day).cummax().groupby(day).ffill(); al = l.where(asia).groupby(day).cummin().groupby(day).ffill()   # causal: solo velas ya cerradas de la sesión
    win = (hr >= 8) & (hr < 17)
    sig = pd.Series(np.where(win & (c > ah), 1, np.where(win & (c < al), -1, 0)), index=df.index)
    a = atr(df, 14); width = (ah - al).clip(lower=0.8 * a, upper=3 * a)
    return Spec(_i8(_first_per_day(sig, df.index)), width.to_numpy(), tp_mult=2.0, max_bars=12)


def i02_donchian24(df):
    c = df["close"]; hh = df["high"].shift(1).rolling(24).max(); ll = df["low"].shift(1).rolling(24).min()
    return Spec(_i8(np.where(c > hh, 1, np.where(c < ll, -1, 0))), _stop(df, 2.0), tp_mult=2.0, max_bars=24)


def i03_boll_rsi(df):
    c = df["close"]; b = bollinger(c, 20, 2.0); r = rsi(c, 14)
    return Spec(_i8(np.where((c < b["lo"]) & (r < 30), 1, np.where((c > b["up"]) & (r > 70), -1, 0))), _stop(df, 2.0), tp_mult=1.0, max_bars=12)


def i04_vwap_dia(df):
    tp = (df["high"] + df["low"] + df["close"]) / 3; day = df.index.floor("1D"); v = df["volume"]
    vwap = (tp * v).groupby(day).cumsum() / v.groupby(day).cumsum(); dev = df["close"] - vwap
    z = dev / dev.rolling(24, min_periods=12).std()
    return Spec(_i8(np.where(z < -2, 1, np.where(z > 2, -1, 0))), _stop(df, 2.0), tp_mult=1.0, max_bars=12)


def i05_ema_cross(df):
    c = df["close"]; f, s, t = ema(c, 9), ema(c, 21), ema(c, 200)
    up = (f > s) & (f.shift(1) <= s.shift(1)) & (c > t); dn = (f < s) & (f.shift(1) >= s.shift(1)) & (c < t)
    return Spec(_i8(np.where(up, 1, np.where(dn, -1, 0))), _stop(df, 1.5), tp_mult=2.0, max_bars=36)


def i06_rsi2(df):
    c = df["close"]; r2 = rsi(c, 2); t = ema(c, 200)
    return Spec(_i8(np.where((r2 < 10) & (c > t), 1, np.where((r2 > 90) & (c < t), -1, 0))), _stop(df, 2.0), tp_mult=1.0, max_bars=12)


def i07_squeeze(df):
    c = df["close"]; b = bollinger(c, 20, 2.0); m = ema(c, 20); a = atr(df, 10); ku, kl = m + 1.5 * a, m - 1.5 * a
    sq = ((b["up"] < ku) & (b["lo"] > kl)).shift(1).fillna(False)
    return Spec(_i8(np.where(sq & (c > ku), 1, np.where(sq & (c < kl), -1, 0))), _stop(df, 1.5), tp_mult=2.0, max_bars=24)


def i08_previo_dia(df):
    d = df.resample("1D").agg({"high": "max", "low": "min"}); ph = d["high"].shift(1).reindex(df.index.floor("1D")).to_numpy(); pl = d["low"].shift(1).reindex(df.index.floor("1D")).to_numpy()
    c = df["close"].to_numpy(); sig = pd.Series(np.where(c > ph, 1, np.where(c < pl, -1, 0)), index=df.index)
    return Spec(_i8(_first_per_day(sig, df.index)), _stop(df, 1.5), tp_mult=2.0, max_bars=24)


def i09_supertrend(df):
    st = pd.Series(s11_supertrend(df), index=df.index); flip = (st != st.shift(1)) & (st != 0) & (st.shift(1) != 0)
    ent = np.where(flip, st, 0)
    return Spec(_i8(ent), _stop(df, 2.5), exit=_i8(ent), tp_mult=0.0, max_bars=48)


def i10_rafaga(df):
    c, o = df["close"], df["open"]; a = atr(df, 14); body = (c - o); vol = df["volume"] > 2 * sma(df["volume"], 20)
    return Spec(_i8(np.where(vol & (body > 1.5 * a), 1, np.where(vol & (body < -1.5 * a), -1, 0))), _stop(df, 1.0, a), tp_mult=1.5, max_bars=6)


def i11_ruptura_fallida(df):
    h, l, c = df["high"], df["low"], df["close"]; hh = h.shift(1).rolling(24).max(); ll = l.shift(1).rolling(24).min(); a = atr(df, 14)
    short = (h > hh) & (c < hh); long_ = (l < ll) & (c > ll)
    st = np.where(short, (h - c) + 0.3 * a, np.where(long_, (c - l) + 0.3 * a, np.nan))
    st = pd.Series(st, index=df.index).fillna(1.5 * a).clip(lower=0.5 * a, upper=3 * a).to_numpy()
    return Spec(_i8(np.where(long_, 1, np.where(short, -1, 0))), st, tp_mult=1.5, max_bars=12)


def i12_ichimoku(df):
    h, l, c = df["high"], df["low"], df["close"]
    ten = (h.rolling(9).max() + l.rolling(9).min()) / 2; kij = (h.rolling(26).max() + l.rolling(26).min()) / 2
    spa = ((ten + kij) / 2).shift(26); spb = ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    top, bot = np.maximum(spa, spb), np.minimum(spa, spb)
    up = (ten > kij) & (ten.shift(1) <= kij.shift(1)) & (c > top); dn = (ten < kij) & (ten.shift(1) >= kij.shift(1)) & (c < bot)
    ent = _i8(np.where(up, 1, np.where(dn, -1, 0)))
    return Spec(ent, _stop(df, 2.0), exit=ent, tp_mult=2.0, max_bars=48)


def i13_psar_ema(df):
    t = pd.Series(_psar(df), index=df.index); c = df["close"]; e = ema(c, 200); flip = t != t.shift(1)
    ent = _i8(np.where(flip & (t > 0) & (c > e), 1, np.where(flip & (t < 0) & (c < e), -1, 0)))
    return Spec(ent, _stop(df, 2.0), exit=_i8(np.where(flip, t, 0)), tp_mult=0.0, max_bars=48)


def i14_apertura_ny(df):
    c, o = df["close"], df["open"]; a = atr(df, 14); body = c - o; at = (df.index.hour == 13)      # vela 13:00-14:00 UTC, cierra a las 14:00
    sig = pd.Series(np.where(at & (body > 0.5 * a), 1, np.where(at & (body < -0.5 * a), -1, 0)), index=df.index)
    return Spec(_i8(sig), _stop(df, 1.5, a), tp_mult=1.5, max_bars=6)


SETUPS = {"I01 Rango asiático → Londres/NY": i01_rango_asiatico, "I02 Ruptura Donchian 24 h": i02_donchian24,
          "I03 Bollinger + RSI (reversión)": i03_boll_rsi, "I04 Reversión a VWAP diaria": i04_vwap_dia,
          "I05 Cruce EMA 9/21 + EMA200": i05_ema_cross, "I06 RSI(2) retroceso": i06_rsi2, "I07 Ruptura tras squeeze": i07_squeeze,
          "I08 Ruptura del máx./mín. de ayer": i08_previo_dia, "I09 Supertrend 10/3": i09_supertrend,
          "I10 Ráfaga de momentum": i10_rafaga, "I11 Ruptura fallida": i11_ruptura_fallida, "I12 Ichimoku 1 h": i12_ichimoku,
          "I13 Parabolic SAR + EMA200": i13_psar_ema, "I14 Apertura de Nueva York": i14_apertura_ny}


def all_specs(df: pd.DataFrame) -> dict:
    return {k: f(df) for k, f in SETUPS.items()}
