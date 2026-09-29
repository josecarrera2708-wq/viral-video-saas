"""Mercado + almacén de indicadores con caché. Todo causal."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..backtest.data import load_perp
from ..data.extra_features import build_extra
from ..signals import indicators as I, candles as C

BARS_PER_DAY = {"1h": 24, "4h": 6, "1d": 1}

CANDLE_COLS = ["marubozu", "hammer", "hanging_man", "inv_hammer", "shooting_star", "engulfing",
               "harami", "tweezers", "stars", "soldiers_crows", "pin_bar"]


class Market:
    def __init__(self, tf: str = "1h", df: pd.DataFrame | None = None, funding: np.ndarray | None = None,
                 extra: pd.DataFrame | None = None, load_extra: bool = False):
        if df is None:
            df, funding = load_perp(tf)
            if load_extra:
                extra = build_extra(df.index)
        self.tf, self.df, self.extra = tf, df, extra
        self.bpd = BARS_PER_DAY[tf]
        self.funding = funding if funding is not None else np.zeros(len(df))
        self.o = df["open"].to_numpy(); self.h = df["high"].to_numpy()
        self.l = df["low"].to_numpy(); self.c = df["close"].to_numpy()
        self.n = len(df)
        self._cache: dict = {}

    def truncate(self, end: str | None) -> "Market":
        """Copia del mercado cortada en `end` (exclusivo). Los indicadores son causales, así que
        los valores previos son idénticos; pero es físicamente imposible ver el futuro."""
        if end is None:
            return self
        b = int(self.df.index.searchsorted(pd.Timestamp(end, tz="UTC")))
        return Market(self.tf, df=self.df.iloc[:b], funding=self.funding[:b],
                      extra=None if self.extra is None else self.extra.iloc[:b])

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

    # ---------------- series exógenas (causales; ya alineadas en extra_features) ----------------
    def ex(self, col: str) -> pd.Series:
        if self.extra is None:
            return pd.Series(np.nan, index=self.df.index)
        return self.extra[col]

    def ex_rank(self, col: str, days: int) -> pd.Series:
        w = max(20, days * self.bpd)
        return self._get(("exr", col, days), lambda: self.ex(col).rolling(w, min_periods=w // 2).rank(pct=True))

    def ex_chg(self, col: str, days: int) -> pd.Series:
        n = max(1, days * self.bpd)
        return self._get(("exc", col, days), lambda: self.ex(col) / self.ex(col).shift(n) - 1)

    # ---------------- marco temporal superior ----------------
    def htf_sma(self, n: int) -> pd.Series:
        """SMA de n cierres DIARIOS (días completos ya cerrados) mapeada a cada vela."""
        def f():
            daily = self.df["close"].resample("1D").last()
            sm = daily.rolling(n, min_periods=n).mean().shift(1)          # solo días ya cerrados
            return sm.reindex(self.df.index, method="ffill")
        return self._get(("htf", n), f)

    def structure(self, k: int) -> pd.DataFrame:
        """Estado de estructura: +1 (HH y HL), -1 (LH y LL), 0 (mixto). Pivotes confirmados (causal)."""
        def f():
            sw = self.swings(k)
            def prev(series):
                ch = series != series.shift(1)
                vals = series[ch]
                pv = vals.shift(1).reindex(series.index).ffill()
                return pv
            ph, pl = prev(sw.last_high), prev(sw.last_low)
            up = (sw.last_high > ph) & (sw.last_low > pl)
            dn = (sw.last_high < ph) & (sw.last_low < pl)
            return pd.DataFrame({"up": up, "dn": dn})
        return self._get(("struct", k), f)
