import numpy as np
import pandas as pd


def align_funding(bar_open_times: pd.DatetimeIndex, bar_delta: pd.Timedelta,
                  funding: pd.DataFrame) -> np.ndarray:
    """Suma en cada vela TODAS las tasas de funding liquidadas dentro de (apertura, apertura+delta].
    Sirve para 1h, 4h y 1d (un evento cae en la vela cuyo cierre es igual o posterior a su marca).
    Falla (no ignora en silencio) si hay marcas dentro del rango de velas que no caen en ninguna."""
    idx = pd.DatetimeIndex(bar_open_times)
    if idx.tz is None:
        raise ValueError("las velas deben llevar zona horaria (UTC)")
    out = np.zeros(len(idx))
    t = pd.DatetimeIndex(funding["time"]).round("min")
    ot = idx.astype("datetime64[ns, UTC]").asi8
    tt = t.astype("datetime64[ns, UTC]").asi8
    pos = np.searchsorted(ot, tt, side="left") - 1       # vela con apertura < T <= apertura + delta
    delta_ns = int(bar_delta.value)
    inside = (pos >= 0) & (pos < len(idx))
    ok = np.zeros(len(tt), bool)
    ok[inside] = tt[inside] <= ot[pos[inside]] + delta_ns
    in_range = (tt > ot[0]) & (tt <= ot[-1] + delta_ns)
    if (~ok & in_range).any():
        raise ValueError(f"{int((~ok & in_range).sum())} marcas de funding sin vela que las contenga")
    np.add.at(out, pos[ok], funding["funding_rate"].to_numpy()[ok])
    return out


def trim_to_funding(df: pd.DataFrame, funding: pd.DataFrame, bar_delta: pd.Timedelta):
    """Recorta las velas al último funding disponible: nunca simular sin funding."""
    last = pd.DatetimeIndex(funding["time"]).round("min").max() - bar_delta
    return df[df.index <= last]
