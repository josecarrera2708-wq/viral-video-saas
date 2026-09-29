"""Mercado + almacén de indicadores con caché. Todo causal."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..backtest.data import load_perp
from ..signals import indicators as I, candles as C

CANDLE_COLS = ["marubozu", "hammer", "hanging_man", "inv_hammer", "shooting_star", "engulfing",
               "harami", "tweezers", "stars", "soldiers_crows", "pin_bar"]


class Market:
    def __init__(self, tf: str = "1h", df: pd.DataFrame | None = None, funding: np.ndarray | None = None):
        if df is None:
            df, funding = load_perp(tf)
        self.tf, self.df = tf, df
        self.funding = funding if funding is not None else np.zeros(len(df))
        self.o = df["open"].to_numpy(); self.h = df["high"].to_numpy()
        self.l = df["low"].to_numpy(); self.c = df["close"].to_numpy()
        self.n = len(df)
        self._cache: dict = {}

    def _get(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def sma(self, n): return self._get(("sma", n), lambda: I.sma(self.df.close, n))
    def ema(self, n): return self._get(("ema", n), lambda: I.ema(self.df.close, n))
    def atr(self, n): return self._get(("atr", n), lambda: I.atr(self.df, n))
    def rsi(self, n): return self._get(("rsi", n), lambda: I.rsi(self.df.close, n))
    def mfi(self, n): return self._get(("mfi", n), lambda: I.mfi(self.df, n))
    def macd(self, f, s, g): return self._get(("macd", f, s, g), lambda: I.macd(self.df.close, f, s, g))
    def boll(self, n, k): return self._get(("boll", n, k), lambda: I.bollinger(self.df.close, n, k))
    def donch(self, n): return self._get(("don", n), lambda: I.donchian(self.df, n))
    def swings(self, k): return self._get(("sw", k), lambda: I.swings(self.df, k))
    def sbreak(self, k): return self._get(("sb", k), lambda: I.structure_break(self.df, k))
    def volpct(self): return self._get(("vp",), lambda: I.vol_percentile(self.df, 14, 500))
    def relvol(self, n): return self._get(("rv", n), lambda: I.rel_volume(self.df, n))
    def candles(self): return self._get(("cd",), lambda: C.all_candles(self.df))

    def index_range(self, start: str | None, end: str | None):
        idx = self.df.index
        a = 0 if start is None else int(idx.searchsorted(pd.Timestamp(start, tz="UTC")))
        b = self.n if end is None else int(idx.searchsorted(pd.Timestamp(end, tz="UTC")))
        return a, b
