"""Carga de datos listos para backtest: velas del perpetuo recortadas al funding disponible."""
from pathlib import Path
import numpy as np
import pandas as pd
from .funding import align_funding, trim_to_funding

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
DELTA = {"1h": pd.Timedelta("1h"), "4h": pd.Timedelta("4h")}


def load_perp(interval: str = "1h"):
    d = pd.read_parquet(RAW / f"perp_BTCUSDT_{interval}.parquet").set_index("time")
    fund = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")
    d = trim_to_funding(d, fund, DELTA[interval])
    return d, align_funding(d.index, DELTA[interval], fund)
