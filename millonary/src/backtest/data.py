"""Carga de datos listos para backtest: velas del perpetuo recortadas al funding disponible."""
from pathlib import Path
import numpy as np
import pandas as pd
from .funding import align_funding, trim_to_funding

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
DELTA = {"1h": pd.Timedelta("1h"), "4h": pd.Timedelta("4h"), "1d": pd.Timedelta("1D")}


def _daily_from_1h():
    h = pd.read_parquet(RAW / "perp_BTCUSDT_1h.parquet").set_index("time")
    g = h.resample("1D")
    d = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum",
               "quote_volume": "sum", "trades": "sum", "taker_buy_base": "sum", "taker_buy_quote": "sum"})
    return d[g["close"].count() == 24]                    # solo días completos


def load_perp(interval: str = "1h"):
    if interval == "1d":
        d = _daily_from_1h()
    else:
        d = pd.read_parquet(RAW / f"perp_BTCUSDT_{interval}.parquet").set_index("time")
    fund = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")
    d = trim_to_funding(d, fund, DELTA[interval])
    return d, align_funding(d.index, DELTA[interval], fund)
