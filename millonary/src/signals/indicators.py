"""Indicadores CAUSALES: el valor en la vela t solo usa datos de las velas <= t."""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(),
                      (df["low"] - pc).abs()], axis=1).max(axis=1, skipna=False)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    out = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    return out.where(dn != 0, 100.0).where(up.notna())


def mfi(df: pd.DataFrame, n: int = 14) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    raw = tp * df["volume"]
    pos = raw.where(tp > tp.shift(1), 0.0).rolling(n, min_periods=n).sum()
    neg = raw.where(tp < tp.shift(1), 0.0).rolling(n, min_periods=n).sum()
    out = 100 - 100 / (1 + pos / neg.replace(0, np.nan))
    return out.where(neg != 0, 100.0).where(pos.notna())


def macd(s: pd.Series, fast: int = 12, slow: int = 26, sig: int = 9) -> pd.DataFrame:
    line = ema(s, fast) - ema(s, slow)
    signal = line.ewm(span=sig, adjust=False, min_periods=sig).mean()
    return pd.DataFrame({"macd": line, "signal": signal, "hist": line - signal})


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    m = sma(s, n); sd = s.rolling(n, min_periods=n).std(ddof=0)
    return pd.DataFrame({"mid": m, "up": m + k * sd, "lo": m - k * sd,
                         "pctb": (s - (m - k * sd)) / (2 * k * sd).replace(0, np.nan)})


def donchian(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Máximo/mínimo de las n velas ANTERIORES (excluye la actual, para poder medir rupturas)."""
    return pd.DataFrame({"hh": df["high"].shift(1).rolling(n, min_periods=n).max(),
                         "ll": df["low"].shift(1).rolling(n, min_periods=n).min()})


def rel_volume(df: pd.DataFrame, n: int = 20) -> pd.Series:
    return df["volume"] / df["volume"].rolling(n, min_periods=n).mean()


def vol_percentile(df: pd.DataFrame, n_atr: int = 14, window: int = 500) -> pd.Series:
    """Percentil (0-1) del ATR% actual frente a las últimas `window` velas."""
    a = atr(df, n_atr) / df["close"]
    return a.rolling(window, min_periods=window // 2).rank(pct=True)


def slope(s: pd.Series, n: int = 5) -> pd.Series:
    """Cambio relativo en n velas (pendiente normalizada)."""
    return s / s.shift(n) - 1


def swings(df: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """Pivotes de k velas a cada lado. Un pivote en t-k solo se CONFIRMA en t (sin look-ahead).
    Devuelve el último máximo/mínimo confirmado, ya disponible en cada vela."""
    h, l = df["high"], df["low"]
    ph = pd.Series(np.nan, index=df.index); pl = ph.copy()
    win = 2 * k + 1
    is_hi = h.rolling(win, min_periods=win).apply(lambda x: float(x[k] == x.max() and
                                                                    (x[k] > x[:k]).all() and
                                                                    (x[k] >= x[k + 1:]).all()),
                                                  raw=True)
    is_lo = l.rolling(win, min_periods=win).apply(lambda x: float(x[k] == x.min() and
                                                                    (x[k] < x[:k]).all() and
                                                                    (x[k] <= x[k + 1:]).all()),
                                                  raw=True)
    # is_hi[t]==1 significa que la vela t-k es pivote, confirmado en t
    ph = h.shift(k).where(is_hi == 1)
    pl = l.shift(k).where(is_lo == 1)
    return pd.DataFrame({"last_high": ph.ffill(), "last_low": pl.ffill()})


def structure_break(df: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """+1 cuando el cierre rompe el último máximo confirmado, -1 cuando rompe el último mínimo."""
    sw = swings(df, k)
    up = ((df["close"] > sw["last_high"]) & (df["close"].shift(1) <= sw["last_high"].shift(1)))
    dn = ((df["close"] < sw["last_low"]) & (df["close"].shift(1) >= sw["last_low"].shift(1)))
    return pd.DataFrame({"break_up": up.astype("int8"), "break_dn": dn.astype("int8")})


def dist_to_level_atr(df: pd.DataFrame, level: pd.Series, n: int = 14) -> pd.Series:
    return (df["close"] - level) / atr(df, n)
