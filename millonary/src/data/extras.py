"""Datos complementarios: días recientes (Binance Vision diario), Fear&Greed y macro FRED.
Solo hosts permitidos; solo se parsea JSON/CSV numérico."""
import io, json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlparse
import pandas as pd, requests
from binance_vision import BASE, _fetch_verified_csv, _parse_klines

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"
ALLOWED = {"api.alternative.me", "fred.stlouisfed.org", "data.binance.vision"}


def _http(url: str) -> bytes:
    u = urlparse(url)
    assert u.scheme == "https" and u.hostname in ALLOWED, url
    r = requests.get(url, timeout=60, allow_redirects=False)
    r.raise_for_status()
    return r.content


def append_recent(market: str, name: str, iv: str) -> int:
    path = RAW / f"{name}_{iv}.parquet"
    df = pd.read_parquet(path)
    d = (df.time.iloc[-1] + pd.Timedelta(days=1)).date()
    new = []
    while d < date.today():
        fn = f"BTCUSDT-{iv}-{d:%Y-%m-%d}"
        r = _fetch_verified_csv(f"{BASE}/{market}/daily/klines/BTCUSDT/{iv}/{fn}.zip", f"{fn}.csv")
        if r is not None:
            new.append(_parse_klines(r[0]))
        d += timedelta(days=1)
    if new:
        df = pd.concat([df] + new).drop_duplicates("time").sort_values("time").reset_index(drop=True)
        df.to_parquet(path, index=False)
    return sum(len(x) for x in new)


def fear_greed() -> pd.DataFrame:
    j = json.loads(_http("https://api.alternative.me/fng/?limit=0&format=json"))["data"]
    df = pd.DataFrame(j)
    df["time"] = pd.to_datetime(pd.to_numeric(df.timestamp), unit="s", utc=True)
    df["fng"] = pd.to_numeric(df.value)
    df = df[["time", "fng", "value_classification"]].sort_values("time").reset_index(drop=True)
    df.to_parquet(RAW / "fear_greed.parquet", index=False)
    return df


def fred(series: str) -> pd.DataFrame:
    raw = _http(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")
    df = pd.read_csv(io.BytesIO(raw), na_values=".")
    df.columns = ["date", series]
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df[series] = pd.to_numeric(df[series], errors="coerce")
    df.to_parquet(RAW / f"fred_{series}.parquet", index=False)
    return df


if __name__ == "__main__":
    for market, name, iv in [("spot", "spot_BTCUSDT", "1h"), ("spot", "spot_BTCUSDT", "4h"),
                             ("spot", "spot_BTCUSDT", "1d"), ("spot", "spot_BTCUSDT", "15m"),
                             ("futures/um", "perp_BTCUSDT", "1h"), ("futures/um", "perp_BTCUSDT", "4h")]:
        print(name, iv, "días recientes añadidas (filas):", append_recent(market, name, iv), flush=True)
    fg = fear_greed(); print("fear&greed", len(fg), fg.time.iloc[0].date(), fg.time.iloc[-1].date(), int(fg.fng.iloc[-1]))
    for s in ["DFF", "DGS10", "DGS2", "CPIAUCSL", "UNRATE", "VIXCLS", "DTWEXBGS", "T10YIE"]:
        try:
            d = fred(s); print("FRED", s, len(d), d.date.iloc[0].date(), d.date.iloc[-1].date())
        except Exception as e:
            print("FRED", s, "ERROR", e)
