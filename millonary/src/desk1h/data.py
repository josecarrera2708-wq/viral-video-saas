"""Datos de la mesa de 1 h: velas de 1 h CERRADAS de Deribit, construidas a partir de las de 15 min (misma fuente; congeladas en paper_state/mesa15/hist.parquet).
Una vela de 1 h solo existe si sus 4 velas de 15 min están completas; el funding por vela de 1 h es la suma de sus 4 trozos."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..desk15.data import ROOT, M15

H1 = pd.Timedelta("1h")


def to_1h(bars: pd.DataFrame, f: np.ndarray) -> tuple[pd.DataFrame, np.ndarray]:
    b = bars.copy(); b["f"] = f; g = b.resample("1h", label="left", closed="left")
    o = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "f": "sum"}); cnt = g["close"].count(); o = o[cnt == 4].dropna()
    return o[["open", "high", "low", "close", "volume"]], o["f"].to_numpy()


def load_history_1h() -> tuple[pd.DataFrame, np.ndarray]:
    h = pd.read_parquet(ROOT / "paper_state" / "mesa15" / "hist.parquet"); return to_1h(h[["open", "high", "low", "close", "volume"]], h["f"].to_numpy())
