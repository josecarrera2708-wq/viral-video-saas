import numpy as np
import pandas as pd


def align_funding(bar_open_times: pd.DatetimeIndex, bar_delta: pd.Timedelta,
                  funding: pd.DataFrame) -> np.ndarray:
    """Asigna cada tasa de funding a la vela cuyo CIERRE coincide con la marca de funding.
    Falla (no ignora en silencio) si hay marcas dentro del rango de velas sin asignar."""
    idx = pd.DatetimeIndex(bar_open_times)
    if idx.tz is None:
        raise ValueError("las velas deben llevar zona horaria (UTC)")
    out = np.zeros(len(idx))
    t = pd.DatetimeIndex(funding["time"]).round("min") - bar_delta
    pos = idx.get_indexer(t)
    ok = pos >= 0
    in_range = (t >= idx[0]) & (t <= idx[-1])
    if (~ok & in_range).any():
        raise ValueError(f"{int((~ok & in_range).sum())} marcas de funding sin vela que las contenga")
    np.add.at(out, pos[ok], funding["funding_rate"].to_numpy()[ok])
    return out


def trim_to_funding(df: pd.DataFrame, funding: pd.DataFrame, bar_delta: pd.Timedelta):
    """Recorta las velas al último funding disponible: nunca simular sin funding."""
    last = pd.DatetimeIndex(funding["time"]).round("min").max() - bar_delta
    return df[df.index <= last]
