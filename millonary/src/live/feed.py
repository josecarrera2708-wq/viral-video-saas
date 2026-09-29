"""Fuente de datos de mercado (solo endpoints PÚBLICOS: no hacen falta claves).

Principal: Binance USDⓈ-M (fapi). Respaldo: Bybit v5. Solo se devuelven velas YA CERRADAS.
`http_get` es inyectable para poder probar sin red. Nada de lo descargado se ejecuta: solo se
interpreta como JSON numérico y se valida (ver risk.validate_bars).
"""
from __future__ import annotations
import time
from typing import Callable
import numpy as np
import pandas as pd
import requests

BINANCE = "https://fapi.binance.com"
BYBIT = "https://api.bybit.com"
INTERVAL_MS = {"4h": 4 * 3600 * 1000}
BYBIT_INTERVAL = {"4h": "240"}


def default_get(url: str, params: dict | None = None, retries: int = 3, timeout: int = 15):
    last = None
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout, headers={"User-Agent": "millonary-paper/1.0"})
            if r.status_code == 200:
                return r.json()
            last = RuntimeError(f"HTTP {r.status_code} en {url}")
            if r.status_code in (403, 451):       # bloqueo regional: no tiene sentido reintentar
                raise last
        except requests.RequestException as e:
            last = e
        time.sleep(2 ** i)
    raise last


def _ms(index: pd.DatetimeIndex) -> np.ndarray:
    """Milisegundos desde la época, INDEPENDIENTE de la resolución interna del índice (pandas 3)."""
    return ((index - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy()


def _to_frame(rows) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["t", "open", "high", "low", "close", "volume"])
    df["time"] = pd.to_datetime(df["t"].astype("int64"), unit="ms", utc=True)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="raise")
    return df.drop(columns="t").set_index("time").sort_index()


MAX_SKEW_MS = 30_000


class BinanceFeed:
    name = "binance"

    def __init__(self, symbol="BTCUSDT", interval="4h", http_get: Callable = default_get):
        self.symbol, self.interval, self.get = symbol, interval, http_get

    def bars(self, n: int, now: pd.Timestamp) -> pd.DataFrame:
        step = INTERVAL_MS[self.interval]
        now_ms = int(now.timestamp() * 1000)
        server_ms = int(self.get(f"{BINANCE}/fapi/v1/time")["serverTime"])
        if abs(server_ms - now_ms) > MAX_SKEW_MS:
            raise RuntimeError(f"reloj local desincronizado {abs(server_ms - now_ms) / 1000:.0f}s respecto al exchange")
        end = server_ms; frames = []; have = 0; pages = 0
        while have < n + 2 and pages < 8:
            rows = self.get(f"{BINANCE}/fapi/v1/klines", {"symbol": self.symbol, "interval": self.interval,
                                                          "limit": min(1500, n - have + 5), "endTime": end})
            if not rows: break
            frames.append(_to_frame([[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows]))
            have = len(pd.concat(frames).index.unique()); pages += 1
            end = int(rows[0][0]) - 1
            if len(rows) < 2: break
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated()]
        df = df[(_ms(df.index) + step) <= server_ms]                       # cerradas según el reloj del EXCHANGE
        return df.iloc[-n:]

    def funding(self, since: pd.Timestamp, now: pd.Timestamp) -> pd.DataFrame:
        rows = self.get(f"{BINANCE}/fapi/v1/fundingRate", {"symbol": self.symbol, "limit": 1000,
                                                           "startTime": int(since.timestamp() * 1000)})
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["time", "funding_rate"])
        out = pd.DataFrame({"time": pd.to_datetime(df["fundingTime"].astype("int64"), unit="ms", utc=True).dt.round("min"),
                            "funding_rate": pd.to_numeric(df["fundingRate"])})
        return out[out["time"] <= now].reset_index(drop=True)


class BybitFeed:
    name = "bybit"

    def __init__(self, symbol="BTCUSDT", interval="4h", http_get: Callable = default_get):
        self.symbol, self.interval, self.get = symbol, interval, http_get

    @staticmethod
    def _check(j):
        if j.get("retCode", 0) != 0:
            raise RuntimeError(f"Bybit retCode={j.get('retCode')} {j.get('retMsg')}")
        return j

    def bars(self, n: int, now: pd.Timestamp) -> pd.DataFrame:
        step = INTERVAL_MS[self.interval]; now_ms = int(now.timestamp() * 1000)
        t = self._check(self.get(f"{BYBIT}/v5/market/time"))
        server_ms = int(t["result"]["timeSecond"]) * 1000
        if abs(server_ms - now_ms) > MAX_SKEW_MS + 1000:
            raise RuntimeError(f"reloj local desincronizado {abs(server_ms - now_ms) / 1000:.0f}s respecto al exchange")
        end = server_ms; frames = []; have = 0; pages = 0
        while have < n + 2 and pages < 8:
            j = self._check(self.get(f"{BYBIT}/v5/market/kline", {"category": "linear", "symbol": self.symbol,
                                                                  "interval": BYBIT_INTERVAL[self.interval],
                                                                  "limit": min(1000, n - have + 5), "end": end}))
            rows = j.get("result", {}).get("list", [])
            if not rows: break
            frames.append(_to_frame([[r[0], r[1], r[2], r[3], r[4], r[5]] for r in rows]))
            have = len(pd.concat(frames).index.unique()); pages += 1
            end = int(min(int(r[0]) for r in rows)) - 1
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated()]
        df = df[(_ms(df.index) + step) <= server_ms]
        return df.iloc[-n:]

    def funding(self, since: pd.Timestamp, now: pd.Timestamp) -> pd.DataFrame:
        j = self._check(self.get(f"{BYBIT}/v5/market/funding/history", {"category": "linear", "symbol": self.symbol,
                                                                        "startTime": int(since.timestamp() * 1000),
                                                                        "endTime": int(now.timestamp() * 1000), "limit": 200}))
        rows = j.get("result", {}).get("list", [])
        if not rows:
            return pd.DataFrame(columns=["time", "funding_rate"])
        return pd.DataFrame({"time": pd.to_datetime([int(r["fundingRateTimestamp"]) for r in rows], unit="ms", utc=True).round("min"),
                             "funding_rate": [float(r["fundingRate"]) for r in rows]}).sort_values("time").reset_index(drop=True)


class FeedRouter:
    """Prueba las fuentes en orden; si dos responden, comprueba que el último cierre coincide (< 0,5 %)."""

    def __init__(self, feeds):
        self.feeds = feeds; self.last_source = None; self.notes = []

    def bars(self, n, now):
        self.notes = []; results = []
        for f in self.feeds:
            try:
                results.append((f, f.bars(n, now)))
            except Exception as e:                                  # noqa: BLE001
                self.notes.append(f"{f.name}: {e}")
        if not results:
            raise RuntimeError("ninguna fuente de datos disponible: " + " | ".join(self.notes))
        f0, d0 = results[0]; self.last_source = f0.name
        if len(results) > 1:
            f1, d1 = results[1]
            common = d0.index.intersection(d1.index)
            if len(common):
                diff = abs(d0.loc[common[-1], "close"] / d1.loc[common[-1], "close"] - 1)
                if diff > 0.005:
                    raise RuntimeError(f"las fuentes discrepan un {diff:.2%} en el último cierre común")
        return d0

    def funding(self, since, now):
        errs = []
        for f in self.feeds:
            try:
                return f.funding(since, now)
            except Exception as e:                                  # noqa: BLE001
                errs.append(f"{f.name}: {e}")
        raise RuntimeError("funding no disponible: " + " | ".join(errs))
