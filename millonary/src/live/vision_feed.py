"""Fuente de datos SIN exchange en vivo: archivos públicos de Binance Vision (con ≤ 1 día de retraso).

Sirve para validar en papel sin VPS: el sistema decide cada 4 h y opera pocas veces, así que evaluar
con retraso da el mismo resultado que en vivo (solo se retrasa la ejecución simulada).

Seguridad (igual que el descargador de datos): solo https://data.binance.vision, sin redirecciones,
cada zip verificado contra su .CHECKSUM (SHA-256) oficial, 1 único miembro con el nombre esperado,
lectura en memoria, contenido interpretado solo como CSV numérico.
"""
from __future__ import annotations
import hashlib, io, zipfile
from typing import Callable
import numpy as np
import pandas as pd
import requests

HOST = "data.binance.vision"
BASE = f"https://{HOST}/data/futures/um"
SPOT = f"https://{HOST}/data/spot"
COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore"]
H4 = pd.Timedelta("4h")


def default_bytes(url: str) -> bytes | None:
    if not url.startswith(f"https://{HOST}/"):
        raise ValueError("URL no permitida: " + url)
    r = requests.get(url, timeout=60, allow_redirects=False)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} en {url}")
    if len(r.content) > 60 * 1024 * 1024:
        raise RuntimeError("archivo demasiado grande")
    return r.content


def _verified_csv(get: Callable, zip_url: str, csv_name: str) -> bytes | None:
    blob = get(zip_url)
    if blob is None:
        return None
    chk = get(zip_url + ".CHECKSUM")
    if chk is None:
        raise RuntimeError("sin checksum: " + zip_url)
    if hashlib.sha256(blob).hexdigest() != chk.decode().split()[0].lower():
        raise RuntimeError("CHECKSUM NO COINCIDE en " + zip_url)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        infos = z.infolist()
        if len(infos) != 1 or infos[0].filename != csv_name or infos[0].file_size > 200 * 1024 * 1024:
            raise RuntimeError("contenido inesperado en " + zip_url)
        return z.read(infos[0])


def _ts(s: pd.Series) -> pd.DatetimeIndex:
    """Binance pasó a microsegundos en 2025: se detecta por magnitud."""
    v = pd.to_numeric(s, errors="raise").astype("int64")
    v = v.where(v < 10**14, v // 1000)
    return pd.DatetimeIndex(pd.to_datetime(v, unit="ms", utc=True))


def _parse_klines(raw: bytes) -> pd.DataFrame:
    first = raw[:100].decode("ascii", errors="strict").split("\n")[0].split(",")[0].strip().lower()
    df = pd.read_csv(io.BytesIO(raw), header=0 if first.startswith("open") else None, names=COLS, dtype=str)
    out = pd.DataFrame({"open": pd.to_numeric(df["open"]), "high": pd.to_numeric(df["high"]),
                        "low": pd.to_numeric(df["low"]), "close": pd.to_numeric(df["close"]),
                        "volume": pd.to_numeric(df["volume"])})
    out.index = _ts(df["open_time"]); out.index.name = "time"
    return out


class VisionFeed:
    name = "vision"

    def __init__(self, symbol="BTCUSDT", interval="4h", get_bytes: Callable = default_bytes, base: str = BASE):
        self.symbol, self.interval, self.get, self.base = symbol, interval, get_bytes, base     # base=SPOT: velas del contado

    def _month(self, y, m):
        n = f"{self.symbol}-{self.interval}-{y}-{m:02d}"
        raw = _verified_csv(self.get, f"{self.base}/monthly/klines/{self.symbol}/{self.interval}/{n}.zip", n + ".csv")
        return None if raw is None else _parse_klines(raw)

    def _day(self, d: pd.Timestamp):
        n = f"{self.symbol}-{self.interval}-{d:%Y-%m-%d}"
        raw = _verified_csv(self.get, f"{self.base}/daily/klines/{self.symbol}/{self.interval}/{n}.zip", n + ".csv")
        return None if raw is None else _parse_klines(raw)

    def bars(self, n: int, now: pd.Timestamp) -> pd.DataFrame:
        """Últimas n velas CERRADAS disponibles. Mensual si existe; si no, día a día hasta ayer."""
        first = (now - (n + 60) * H4).floor("D")
        frames = []
        month = pd.Timestamp(first.year, first.month, 1, tz="UTC")
        while month <= now:
            mdf = self._month(month.year, month.month) if (month + pd.offsets.MonthBegin(1)) <= now.floor("D") else None
            if mdf is None:
                d = max(month, first)
                end = min(month + pd.offsets.MonthEnd(0), now.floor("D") - pd.Timedelta(days=1))
                while d <= end:
                    ddf = self._day(d)
                    if ddf is not None: frames.append(ddf)
                    d += pd.Timedelta(days=1)
            else:
                frames.append(mdf)
            month = month + pd.offsets.MonthBegin(1)
        if not frames:
            raise RuntimeError("Binance Vision no devolvió datos")
        df = pd.concat(frames).sort_index()
        df = df[~df.index.duplicated()]
        close_time = df.index + H4
        df = df[close_time <= now]                                   # solo velas ya cerradas
        return df.iloc[-n:]

    def funding(self, since: pd.Timestamp, now: pd.Timestamp) -> pd.DataFrame:
        """Funding real de los meses completos (Vision) + sintético 0,01 %/8h para el mes en curso.
        La columna 'synthetic' marca lo estimado; se corrige al publicarse el mes."""
        rows = []; month = pd.Timestamp(since.year, since.month, 1, tz="UTC")
        while month <= now:
            complete = (month + pd.offsets.MonthBegin(1)) <= now.floor("D")
            raw = None
            if complete:
                n = f"{self.symbol}-fundingRate-{month.year}-{month.month:02d}"
                raw = _verified_csv(self.get, f"{BASE}/monthly/fundingRate/{self.symbol}/{n}.zip", n + ".csv")
            if raw is not None:
                d = pd.read_csv(io.BytesIO(raw), dtype=str)
                d.columns = ["calc_time", "interval", "rate"][: len(d.columns)]
                rows.append(pd.DataFrame({"time": _ts(d["calc_time"]).round("min"), "funding_rate": pd.to_numeric(d["rate"]),
                                          "synthetic": False}))
            else:
                t = pd.date_range(month, min(month + pd.offsets.MonthEnd(0) + pd.Timedelta(days=1), now), freq="8h", tz="UTC")
                rows.append(pd.DataFrame({"time": t, "funding_rate": 0.0001, "synthetic": True}))
            month = month + pd.offsets.MonthBegin(1)
        f = pd.concat(rows).drop_duplicates("time").sort_values("time").reset_index(drop=True)
        return f[(f["time"] > since) & (f["time"] <= now)].reset_index(drop=True)
