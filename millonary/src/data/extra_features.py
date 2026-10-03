"""Series exógenas alineadas a las velas de forma CAUSAL (solo información ya conocida en la vela).

Reglas de no-fuga:
  * Derivados de 5 min (OI, ratios): se toma la última foto con create_time <= APERTURA de la vela
    (un desfase de una vela: seguro).
  * Funding: último funding liquidado con time <= apertura de la vela.
  * Prima del perpetuo: cierre de la propia vela (se conoce al cierre).
  * Fear & Greed (diario): el valor del día D se usa desde D+1 00:00 UTC (retraso de 1 día).
  * FRED (VIX, DGS10, DGS2, dólar): retraso de 2 días (se publican con demora y se revisan).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"


def _asof(idx: pd.DatetimeIndex, src: pd.DataFrame, cols: list[str], lag: pd.Timedelta = pd.Timedelta(0)):
    """Para cada vela (apertura T) devuelve la última fila de src con time + lag <= T."""
    s = src[["time"] + cols].copy()
    s["time"] = s["time"].astype("datetime64[ns, UTC]") + lag
    s = s.sort_values("time")
    left = pd.DataFrame({"time": pd.DatetimeIndex(idx).astype("datetime64[ns, UTC]")})
    out = pd.merge_asof(left, s, on="time", direction="backward")
    out.index = idx
    return out[cols]


def build_extra(idx: pd.DatetimeIndex) -> pd.DataFrame:
    idx = pd.DatetimeIndex(idx)
    ex = pd.DataFrame(index=idx)
    fund = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")
    fund["time"] = fund["time"].dt.round("min")
    ex["funding"] = _asof(idx, fund, ["funding_rate"])["funding_rate"]
    prem = pd.read_parquet(RAW / "perp_BTCUSDT_premium_1h.parquet").set_index("time")["premium"]
    prem.index = prem.index.astype("datetime64[ns, UTC]")
    ex["premium"] = prem.reindex(idx.astype("datetime64[ns, UTC]")).to_numpy()
    met = pd.read_parquet(RAW / "perp_BTCUSDT_metrics_5m.parquet")
    met = met[met["sum_open_interest_value"] > 0]                   # descarta fotos vacías
    m = _asof(idx, met, ["sum_open_interest_value", "count_toptrader_long_short_ratio",
                         "sum_toptrader_long_short_ratio", "count_long_short_ratio",
                         "sum_taker_long_short_vol_ratio"])
    ex["oi_value"] = m["sum_open_interest_value"]
    ex["ls_top_acc"] = m["count_toptrader_long_short_ratio"]
    ex["ls_top_pos"] = m["sum_toptrader_long_short_ratio"]
    ex["ls_all"] = m["count_long_short_ratio"]
    ex["taker_ls"] = m["sum_taker_long_short_vol_ratio"]
    fg = pd.read_parquet(RAW / "fear_greed.parquet")
    ex["fng"] = _asof(idx, fg, ["fng"], lag=pd.Timedelta(days=1))["fng"]
    for name, col in (("vix", "VIXCLS"), ("y10", "DGS10"), ("y2", "DGS2"), ("usd", "DTWEXBGS")):
        f = pd.read_parquet(RAW / f"fred_{col}.parquet").dropna().rename(columns={"date": "time", col: name})
        ex[name] = _asof(idx, f, [name], lag=pd.Timedelta(days=2))[name]
    return ex
