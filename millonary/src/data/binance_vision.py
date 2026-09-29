"""Descarga segura de velas históricas de Binance Vision (datos públicos oficiales).

Salvaguardas:
- Solo el host data.binance.vision, solo HTTPS, sin redirecciones a otros hosts.
- Cada zip se verifica con su .CHECKSUM (SHA-256) oficial antes de leerlo.
- El zip se inspecciona (1 miembro, nombre esperado, sin rutas, tamaño acotado) y se lee en
  memoria; nunca se extrae a disco ni se ejecuta nada.
- El contenido se interpreta solo como CSV numérico y se valida.
"""
from __future__ import annotations

import hashlib
import io
import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

ALLOWED_HOST = "data.binance.vision"
BASE = f"https://{ALLOWED_HOST}/data"
MAX_ZIP_BYTES = 60 * 1024 * 1024
MAX_CSV_BYTES = 400 * 1024 * 1024
KLINE_COLS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
              "quote_volume", "trades", "taker_buy_base", "taker_buy_quote", "ignore"]
FUNDING_COLS = ["calc_time", "funding_interval_hours", "last_funding_rate"]


def _check_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme != "https" or u.hostname != ALLOWED_HOST:
        raise ValueError(f"URL no permitida: {url}")


def _get(url: str, retries: int = 3) -> bytes | None:
    _check_url(url)
    for i in range(retries):
        try:
            r = requests.get(url, timeout=60, allow_redirects=False, stream=True)
            if r.status_code == 404:
                return None
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            buf = io.BytesIO()
            for chunk in r.iter_content(1 << 16):
                buf.write(chunk)
                if buf.tell() > MAX_ZIP_BYTES:
                    raise RuntimeError("archivo demasiado grande")
            return buf.getvalue()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2 ** i)
    return None


def _fetch_verified_csv(zip_url: str, expected_csv: str) -> tuple[bytes, str] | None:
    """Devuelve (contenido_csv, sha256) o None si el archivo no existe. Lanza si no verifica."""
    blob = _get(zip_url)
    if blob is None:
        return None
    chk = _get(zip_url + ".CHECKSUM")
    if chk is None:
        raise RuntimeError(f"Sin checksum para {zip_url}")
    expected_hash = chk.decode().split()[0].lower()
    actual = hashlib.sha256(blob).hexdigest()
    if actual != expected_hash:
        raise RuntimeError(f"CHECKSUM NO COINCIDE en {zip_url}")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        infos = z.infolist()
        if len(infos) != 1:
            raise RuntimeError(f"El zip tiene {len(infos)} miembros: {zip_url}")
        info = infos[0]
        if info.filename != expected_csv or "/" in info.filename or ".." in info.filename:
            raise RuntimeError(f"Nombre inesperado en zip: {info.filename}")
        if info.file_size > MAX_CSV_BYTES:
            raise RuntimeError("CSV descomprimido demasiado grande")
        return z.read(info), actual


def _months(start: str, end: date):
    y, m = map(int, start.split("-"))
    while (y, m) <= (end.year, end.month):
        yield y, m
        m += 1
        if m == 13:
            y, m = y + 1, 1


def _normalize_ts(s: pd.Series) -> pd.Series:
    """Binance pasó a microsegundos en 2025; se detecta por magnitud."""
    s = pd.to_numeric(s, errors="raise").astype("int64")
    us = s > 10**14
    ms = s.where(~us, s // 1000)
    return pd.to_datetime(ms, unit="ms", utc=True)


def _parse_klines(raw: bytes) -> pd.DataFrame:
    head = raw[:200].decode("ascii", errors="strict").split("\n")[0]
    has_header = head.split(",")[0].strip().lower() in ("open_time", "open time")
    df = pd.read_csv(io.BytesIO(raw), header=0 if has_header else None, names=KLINE_COLS,
                     dtype=str)
    for c in ["open", "high", "low", "close", "volume", "quote_volume",
              "taker_buy_base", "taker_buy_quote"]:
        df[c] = pd.to_numeric(df[c], errors="raise")
    df["trades"] = pd.to_numeric(df["trades"], errors="raise").astype("int64")
    df["time"] = _normalize_ts(df["open_time"])
    return df[["time", "open", "high", "low", "close", "volume", "quote_volume",
               "trades", "taker_buy_base", "taker_buy_quote"]]


def download_klines(market: str, symbol: str, interval: str, start: str, out: Path,
                    end: date | None = None, workers: int = 6) -> dict:
    """market: 'spot' o 'futures/um'. Guarda parquet y devuelve un manifiesto."""
    end = end or date.today()
    tasks = []
    for y, m in _months(start, end):
        name = f"{symbol}-{interval}-{y}-{m:02d}"
        tasks.append((f"{BASE}/{market}/monthly/klines/{symbol}/{interval}/{name}.zip",
                      f"{name}.csv", f"{y}-{m:02d}"))

    def work(t):
        url, csv, tag = t
        r = _fetch_verified_csv(url, csv)
        if r is None:
            return tag, None, None, url
        raw, h = r
        return tag, _parse_klines(raw), h, url

    frames, manifest, missing = [], [], []
    with ThreadPoolExecutor(workers) as ex:
        for tag, df, h, url in ex.map(work, tasks):
            if df is None:
                missing.append(tag)
                continue
            frames.append(df)
            manifest.append({"month": tag, "sha256": h, "rows": len(df), "url": url})
    if not frames:
        raise RuntimeError("No se descargó nada")
    df = (pd.concat(frames).drop_duplicates("time").sort_values("time")
          .reset_index(drop=True))
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    return {"file": str(out), "rows": len(df), "first": str(df.time.iloc[0]),
            "last": str(df.time.iloc[-1]), "months_ok": len(manifest),
            "months_missing": missing, "files": manifest}


def download_funding(symbol: str, start: str, out: Path, end: date | None = None) -> dict:
    end = end or date.today()
    frames, missing = [], []
    for y, m in _months(start, end):
        name = f"{symbol}-fundingRate-{y}-{m:02d}"
        url = f"{BASE}/futures/um/monthly/fundingRate/{symbol}/{name}.zip"
        r = _fetch_verified_csv(url, f"{name}.csv")
        if r is None:
            missing.append(f"{y}-{m:02d}")
            continue
        df = pd.read_csv(io.BytesIO(r[0]), dtype=str)
        df.columns = FUNDING_COLS[: len(df.columns)]
        df["time"] = _normalize_ts(df["calc_time"])
        df["funding_rate"] = pd.to_numeric(df["last_funding_rate"], errors="raise")
        frames.append(df[["time", "funding_rate"]])
    df = pd.concat(frames).drop_duplicates("time").sort_values("time").reset_index(drop=True)
    df.to_parquet(out, index=False)
    return {"file": str(out), "rows": len(df), "first": str(df.time.iloc[0]),
            "last": str(df.time.iloc[-1]), "months_missing": missing}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "data" / "raw"
    report = {}
    # Spot BTCUSDT desde el inicio de Binance (2017-08)
    for iv in ["1d", "4h", "1h", "15m"]:
        report[f"spot_{iv}"] = download_klines("spot", "BTCUSDT", iv, "2017-08",
                                               root / f"spot_BTCUSDT_{iv}.parquet")
        print(iv, report[f"spot_{iv}"]["rows"], report[f"spot_{iv}"]["first"],
              report[f"spot_{iv}"]["last"], "faltan:", report[f"spot_{iv}"]["months_missing"],
              flush=True)
    # Perpetuo USDT-M desde 2019-09
    for iv in ["1h", "4h"]:
        report[f"perp_{iv}"] = download_klines("futures/um", "BTCUSDT", iv, "2019-09",
                                               root / f"perp_BTCUSDT_{iv}.parquet")
        print("perp", iv, report[f"perp_{iv}"]["rows"], report[f"perp_{iv}"]["first"],
              report[f"perp_{iv}"]["last"], "faltan:",
              report[f"perp_{iv}"]["months_missing"], flush=True)
    report["funding"] = download_funding("BTCUSDT", "2019-09", root / "perp_BTCUSDT_funding.parquet")
    print("funding", report["funding"], flush=True)
    (root / "manifest.json").write_text(json.dumps(report, indent=1, default=str))
