import numpy as np
import pandas as pd


def align_funding(bar_open_times: pd.DatetimeIndex, bar_delta: pd.Timedelta,
                  funding: pd.DataFrame) -> np.ndarray:
    """Asigna cada tasa de funding a la vela cuyo CIERRE coincide con la marca de funding."""
    out = np.zeros(len(bar_open_times))
    idx = pd.DatetimeIndex(bar_open_times)
    t = (pd.DatetimeIndex(funding["time"]).round("min") - bar_delta)
    pos = idx.get_indexer(t)
    ok = pos >= 0
    np.add.at(out, pos[ok], funding["funding_rate"].to_numpy()[ok])
    return out
