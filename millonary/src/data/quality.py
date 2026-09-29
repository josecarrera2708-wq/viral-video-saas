"""Control de calidad de las velas: huecos, duplicados, coherencia OHLC y entre marcos."""
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
STEP = {"15m": "15min", "1h": "1h", "4h": "4h", "1d": "1D"}


def check(name: str, iv: str) -> dict:
    df = pd.read_parquet(RAW / f"{name}_{iv}.parquet")
    t = df["time"]
    exp = pd.date_range(t.iloc[0], t.iloc[-1], freq=STEP[iv], tz="UTC")
    missing = exp.difference(pd.DatetimeIndex(t))
    bad = ((df.high < df[["open", "close", "low"]].max(axis=1)) |
           (df.low > df[["open", "close", "high"]].min(axis=1)) |
           (df[["open", "high", "low", "close"]] <= 0).any(axis=1) |
           (df.volume < 0)).sum()
    ret = df.close.pct_change().abs()
    return {"file": f"{name}_{iv}", "rows": len(df), "first": str(t.iloc[0])[:16],
            "last": str(t.iloc[-1])[:16], "dups": int(t.duplicated().sum()),
            "missing_bars": len(missing), "bad_ohlc": int(bad),
            "max_move_1bar_%": round(float(ret.max()) * 100, 1),
            "zero_volume": int((df.volume == 0).sum()),
            "gaps_ge_1h": _gaps(missing)}


def _gaps(missing):
    if len(missing) == 0:
        return []
    s = pd.Series(missing)
    grp = (s.diff() != s.diff().mode().iloc[0]).cumsum()
    out = []
    for _, g in s.groupby(grp):
        out.append((str(g.iloc[0])[:16], len(g)))
    return out[:6]


def cross(name: str) -> dict:
    """La 1h agregada a 4h y 1d debe coincidir con las velas 4h y 1d descargadas."""
    h = pd.read_parquet(RAW / f"{name}_1h.parquet").set_index("time")
    res = {}
    for iv, rule in (("4h", "4h"), ("1d", "1D")):
        ref = pd.read_parquet(RAW / f"{name}_{iv}.parquet").set_index("time")
        agg = h.resample(rule).agg({"open": "first", "high": "max", "low": "min",
                                    "close": "last", "volume": "sum"}).dropna()
        j = agg.join(ref, lsuffix="_a", rsuffix="_r", how="inner")
        res[iv] = {"bars": len(j),
                   "close_max_rel_diff": float(((j.close_a - j.close_r).abs() / j.close_r).max()),
                   "high_max_rel_diff": float(((j.high_a - j.high_r).abs() / j.high_r).max()),
                   "vol_max_rel_diff": float(((j.volume_a - j.volume_r).abs() /
                                              j.volume_r.clip(lower=1e-9)).max())}
    return res


if __name__ == "__main__":
    for name, ivs in (("spot_BTCUSDT", ["15m", "1h", "4h", "1d"]), ("perp_BTCUSDT", ["1h", "4h"])):
        for iv in ivs:
            print(check(name, iv))
    print("cross spot:", cross("spot_BTCUSDT"))
    print("cross perp:", cross("perp_BTCUSDT"))
    f = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")
    d = f["time"].diff().dt.total_seconds().div(3600)
    print("funding: rows", len(f), "intervalos (h) más comunes:", d.round(1).value_counts().head(4).to_dict(),
          "min/max:", f.funding_rate.min(), f.funding_rate.max())
