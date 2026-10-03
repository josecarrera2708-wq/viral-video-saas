"""Datos de la Fase 2 (primas de riesgo): futuros trimestrales USDT-M de Binance (Binance Vision, 1 h), contado 1 h y DVOL de Deribit (diario).

Futuros: un contrato por trimestre (vence el último viernes de mar/jun/sep/dic a las 08:00 UTC). Los contratos vencidos se guardan en
data/raw/primas/ y no se vuelven a descargar. DVOL: API pública de Deribit (get_volatility_index_data), solo lectura.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from src.live.vision_feed import VisionFeed, SPOT, BASE

ROOT = Path(__file__).resolve().parents[2]
HIST = ROOT / "paper_state" / "hist"                              # copia congelada en git (las máquinas nuevas no tienen data/raw)
RAW = ROOT / "data" / "raw" if (ROOT / "data" / "raw" / "spot_BTCUSDT_1h.parquet").exists() else HIST
P = RAW / "primas"
FIRST_EXPIRY = pd.Timestamp("2021-03-26 08:00", tz="UTC")       # primer trimestral BTCUSDT USDT-M
LISTED_DAYS = 200                                                # se busca historia desde ~200 d antes del vencimiento


def last_friday(y: int, m: int) -> pd.Timestamp:
    d = pd.Timestamp(y, m, 1) + pd.offsets.MonthEnd(0)
    while d.weekday() != 4:
        d -= pd.Timedelta(days=1)
    return pd.Timestamp(d.date()).tz_localize("UTC") + pd.Timedelta("8h")


def expiries(until: pd.Timestamp) -> list[pd.Timestamp]:
    out, y, m = [], 2021, 3
    while True:
        e = last_friday(y, m)
        if e > until:
            return out
        if e >= FIRST_EXPIRY:
            out.append(e)
        m += 3
        if m > 12:
            y, m = y + 1, 3


def symbol(e: pd.Timestamp) -> str:
    return f"BTCUSDT_{e:%y%m%d}"


def _klines(feed: VisionFeed, a: pd.Timestamp, b: pd.Timestamp, now: pd.Timestamp) -> pd.DataFrame:
    """Velas 1 h [a, b) cerradas antes de `now`: archivo mensual si el mes está completo, si no día a día."""
    frames = []; month = pd.Timestamp(a.year, a.month, 1, tz="UTC")
    while month < b:
        mdf = feed._month(month.year, month.month) if (month + pd.offsets.MonthBegin(1)) <= now.floor("D") else None
        if mdf is None:
            d = max(month, a.floor("D")); end = min(month + pd.offsets.MonthEnd(0), now.floor("D") - pd.Timedelta(days=1), b)
            while d <= end:
                x = feed._day(d)
                if x is not None:
                    frames.append(x)
                d += pd.Timedelta(days=1)
        else:
            frames.append(mdf)
        month += pd.offsets.MonthBegin(1)
    if not frames:
        return pd.DataFrame(columns=["open", "high", "low", "close"])
    df = pd.concat(frames).sort_index(); df = df[~df.index.duplicated()]
    df = df[(df.index >= a) & (df.index < b) & (df.index + pd.Timedelta("1h") <= now)]
    return df[["open", "high", "low", "close"]].astype(float)


def futures(now: pd.Timestamp) -> dict[str, pd.DataFrame]:
    """{símbolo: velas 1 h} de todos los trimestrales que vencen antes de now + 200 d (los listados hoy incluidos)."""
    P.mkdir(parents=True, exist_ok=True); out = {}
    for e in expiries(now + pd.Timedelta(days=LISTED_DAYS)):
        s = symbol(e); f = P / f"fut_{s}_1h.parquet"
        if f.exists():
            df = pd.read_parquet(f)
        else:
            df = _klines(VisionFeed(symbol=s, interval="1h", base=BASE), e - pd.Timedelta(days=LISTED_DAYS), e, now)
            if e <= now - pd.Timedelta(days=2) and len(df):
                df.to_parquet(f)                                   # vencido: definitivo
        if len(df):
            out[s] = df
    return out


def spot_1h(now: pd.Timestamp) -> pd.DataFrame:
    s = pd.read_parquet(RAW / "spot_BTCUSDT_1h.parquet")
    s = (s.set_index("time") if "time" in s else s)[["open", "high", "low", "close"]].astype(float)
    new = _klines(VisionFeed(symbol="BTCUSDT", interval="1h", base=SPOT), s.index[-1] + pd.Timedelta("1h"), now, now)
    s = pd.concat([s, new]); return s[~s.index.duplicated(keep="first")].sort_index()


def dvol(now: pd.Timestamp) -> pd.Series:
    """DVOL de Deribit (BTC), cierre diario en % anual, indexado por el día UTC al que corresponde la vela."""
    P.mkdir(parents=True, exist_ok=True); f = P / "dvol_btc_1d.parquet"
    old = pd.read_parquet(f)["dvol"] if f.exists() else pd.Series(dtype=float)
    a = int(((old.index[-1] - pd.Timedelta(days=3)) if len(old) else pd.Timestamp("2021-03-01", tz="UTC")).timestamp() * 1000)
    rows, end = [], int(now.timestamp() * 1000)
    while True:
        r = requests.get("https://www.deribit.com/api/v2/public/get_volatility_index_data", timeout=30,
                         params={"currency": "BTC", "start_timestamp": a, "end_timestamp": end, "resolution": "1D"}).json()["result"]
        rows += r["data"]
        c = r.get("continuation")
        if not c or c <= a or not r["data"]:
            break
        end = int(c)
    s = pd.Series({pd.Timestamp(row[0], unit="ms", tz="UTC"): float(row[4]) for row in rows}, dtype=float)      # [t, o, h, l, c]
    s = s[s.index + pd.Timedelta("1D") <= now]                    # solo días cerrados
    s = pd.concat([old, s]); s = s[~s.index.duplicated(keep="last")].sort_index()
    s.to_frame("dvol").to_parquet(f); return s
