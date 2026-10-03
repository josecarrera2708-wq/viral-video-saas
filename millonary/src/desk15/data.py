"""Datos de la mesa de 15 min: velas y funding de Deribit BTC-PERPETUAL (único proveedor accesible desde este entorno).

La API de Deribit devuelve las ÚLTIMAS 5.000 velas anteriores a `end_timestamp`; se pagina hacia atrás.
Solo se usan velas CERRADAS. El funding por vela es interest_1h/4 (tasa horaria repartida en 4 velas), pagado en la vela que cierra tras cada marca horaria.
"""
from __future__ import annotations
import time
from pathlib import Path
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
API = "https://www.deribit.com/api/v2/public"
INSTR = "BTC-PERPETUAL"
M15 = pd.Timedelta("15min")
CACHE = ROOT / "data" / "cache"


def _ms(t) -> int:
    return int(pd.Timestamp(t).tz_convert("UTC").timestamp() * 1000)


def _get(path: str, params: dict, tries: int = 4) -> dict:
    for k in range(tries):
        try:
            j = requests.get(f"{API}/{path}", params=params, timeout=40).json()
            if "result" in j:
                return j["result"]
        except Exception:                                            # noqa: BLE001
            pass
        time.sleep(2 ** k)
    raise RuntimeError(f"Deribit no responde: {path}")


def fetch_bars(start, now, get=None) -> pd.DataFrame:
    """Velas de 15 min CERRADAS entre start y now (paginadas hacia atrás)."""
    get = get or _get; start, now = pd.Timestamp(start), pd.Timestamp(now); end = now; parts = []
    while True:
        j = get("get_tradingview_chart_data", {"instrument_name": INSTR, "resolution": "15", "start_timestamp": _ms(start), "end_timestamp": _ms(end)})
        if not j["ticks"]:
            break
        t = pd.to_datetime(pd.Series(j["ticks"]), unit="ms", utc=True)
        parts.append(pd.DataFrame({"open": j["open"], "high": j["high"], "low": j["low"], "close": j["close"], "volume": j["volume"]}, index=pd.DatetimeIndex(t)))
        if t.iloc[0] <= start or len(t) < 5000:
            break
        end = t.iloc[0] - pd.Timedelta("1min")
    df = pd.concat(parts).sort_index(); df = df[~df.index.duplicated()]
    df = df[df.index >= start]
    return df[df.index + M15 <= now]


def fetch_funding(idx: pd.DatetimeIndex, now, get=None) -> np.ndarray:
    """Funding por vela de 15 min (interest_1h/4 en la vela que cierra tras la marca horaria). 0 si el proveedor falla."""
    get = get or _get
    try:
        s = {}; a = idx[0]; end = pd.Timestamp(now)
        while end > a:
            j = get("get_funding_rate_history", {"instrument_name": INSTR, "start_timestamp": _ms(max(a, end - pd.Timedelta(days=30))), "end_timestamp": _ms(end)})
            if not j:
                break
            for x in j:
                s[pd.Timestamp(x["timestamp"], unit="ms", tz="UTC").floor("1h")] = x["interest_1h"]
            end = end - pd.Timedelta(days=30)
        ser = pd.Series(s).sort_index()
        # la entrada de la hora h cubre [h-1h, h): cada una de sus 4 velas carga 1/4 de interest_1h
        h_end = (idx + M15 - pd.Timedelta("1ns")).floor("1h") + pd.Timedelta("1h")
        out = ser.reindex(h_end).fillna(0.0).to_numpy() / 4.0
        return out
    except Exception:                                                # noqa: BLE001
        return np.zeros(len(idx))


def load_history(start="2022-06-01", now=None) -> tuple[pd.DataFrame, np.ndarray]:
    """Histórico 15 min en caché (data/cache/deribit_15m.parquet); se completa hasta `now`."""
    CACHE.mkdir(parents=True, exist_ok=True); p = CACHE / "deribit_15m.parquet"; f = CACHE / "deribit_15m_funding.parquet"
    now = pd.Timestamp(now) if now is not None else pd.Timestamp.now(tz="UTC")
    if p.exists():
        old = pd.read_parquet(p); a = old.index[-1] + M15
        new = fetch_bars(a, now) if now - a > M15 else old.iloc[:0]
        df = pd.concat([old, new]); df = df[~df.index.duplicated()].sort_index()
    else:
        df = fetch_bars(pd.Timestamp(start, tz="UTC") if pd.Timestamp(start).tzinfo is None else start, now)
    df.to_parquet(p)
    fu = fetch_funding(df.index, now) if not f.exists() or len(pd.read_parquet(f)) != len(df) else pd.read_parquet(f)["f"].to_numpy()
    pd.DataFrame({"f": fu}, index=df.index).to_parquet(f)
    return df, fu
