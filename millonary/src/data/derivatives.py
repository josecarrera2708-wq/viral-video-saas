"""Datos de derivados de Binance Vision: open interest, ratios largo/corto, prima del perpetuo.
Misma seguridad que binance_vision.py (host único, checksum SHA-256, solo CSV numérico)."""
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
from binance_vision import BASE, _fetch_verified_csv, _months, _normalize_ts

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
COLS = ["create_time", "symbol", "sum_open_interest", "sum_open_interest_value",
        "count_toptrader_long_short_ratio", "sum_toptrader_long_short_ratio",
        "count_long_short_ratio", "sum_taker_long_short_vol_ratio"]


def _day(d):
    fn = f"BTCUSDT-metrics-{d:%Y-%m-%d}"
    r = _fetch_verified_csv(f"{BASE}/futures/um/daily/metrics/BTCUSDT/{fn}.zip", f"{fn}.csv")
    if r is None:
        return None
    df = pd.read_csv(io.BytesIO(r[0]), dtype=str)
    assert list(df.columns) == COLS, df.columns
    return df


def download_metrics(start=date(2020, 9, 1)):
    days = []; d = start
    while d < date.today():
        days.append(d); d += timedelta(days=1)
    with ThreadPoolExecutor(8) as ex:
        frames = [f for f in ex.map(_day, days) if f is not None]
    df = pd.concat(frames).drop_duplicates("create_time")
    df["time"] = pd.to_datetime(df["create_time"], utc=True)
    for c in COLS[2:]:
        if c != "symbol": df[c] = pd.to_numeric(df[c], errors="raise")
    df = df.drop(columns=["create_time", "symbol"]).sort_values("time").reset_index(drop=True)
    df.to_parquet(RAW / "perp_BTCUSDT_metrics_5m.parquet", index=False)
    return df, len(days) - len(frames)


def download_premium(interval="1h", start="2020-01"):
    frames = []
    for y, m in _months(start, date.today()):
        fn = f"BTCUSDT-{interval}-{y}-{m:02d}"
        r = _fetch_verified_csv(f"{BASE}/futures/um/monthly/premiumIndexKlines/BTCUSDT/{interval}/{fn}.zip", f"{fn}.csv")
        if r is None: continue
        raw = pd.read_csv(io.BytesIO(r[0]), header=None, dtype=str)
        if raw.iloc[0, 0].lower().startswith("open"): raw = raw.iloc[1:]
        df = pd.DataFrame({"time": _normalize_ts(raw[0]), "premium": pd.to_numeric(raw[4], errors="raise")})
        frames.append(df)
    out = pd.concat(frames).drop_duplicates("time").sort_values("time").reset_index(drop=True)
    out.to_parquet(RAW / f"perp_BTCUSDT_premium_{interval}.parquet", index=False)
    return out


if __name__ == "__main__":
    df, missing = download_metrics()
    print("metrics 5m:", len(df), df.time.iloc[0], "→", df.time.iloc[-1], "| días sin archivo:", missing)
    print(df.describe().T[["min", "max"]].round(3).to_string())
    p = download_premium("1h"); print("premium 1h:", len(p), p.time.iloc[0], "→", p.time.iloc[-1])
