import sys, pathlib, io, zipfile, hashlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.live.config import LiveConfig, RiskLimits
from src.live.vision_feed import VisionFeed, BASE
from src.live.catchup import catchup
from src.live.store import Store
from src.live.trader import PaperTrader

H4 = pd.Timedelta("4h")


def synth(start="2023-06-01", n=2600, seed=0):
    rng = np.random.default_rng(seed)
    c = 30000 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n)))
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range(start, periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.003, "low": np.minimum(o, c) * 0.997, "close": c, "volume": 1.0}, index=idx)


def csv_of(df, micro=False, header=True):
    ot = ((df.index - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(milliseconds=1)).to_numpy() * (1000 if micro else 1)
    rows = ["open_time,open,high,low,close,volume,close_time,quote_volume,count,taker_buy_volume,taker_buy_quote_volume,ignore"] if header else []
    for t, (i, r) in zip(ot, df.iterrows()):
        rows.append(f"{t},{r.open},{r.high},{r.low},{r.close},{r.volume},{t + 14399999},0,1,0,0,0")
    return "\n".join(rows).encode()


def make_server(df, now, tamper=None):
    """Simula Binance Vision: mensual para meses completos, diario para el resto (hasta AYER)."""
    files = {}
    def add(url, name, content):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z: z.writestr(name, content)
        blob = buf.getvalue(); files[url] = blob
        files[url + ".CHECKSUM"] = (hashlib.sha256(blob).hexdigest() + "  " + name + ".zip").encode()
    for (y, m), g in df.groupby([df.index.year, df.index.month]):
        first = pd.Timestamp(y, m, 1, tz="UTC")
        if first + pd.offsets.MonthBegin(1) <= now.floor("D"):
            n = f"BTCUSDT-4h-{y}-{m:02d}"; add(f"{BASE}/monthly/klines/BTCUSDT/4h/{n}.zip", n + ".csv", csv_of(g))
        for d, gd in g.groupby(g.index.floor("D")):
            if d < now.floor("D"):
                n = f"BTCUSDT-4h-{d:%Y-%m-%d}"; add(f"{BASE}/daily/klines/BTCUSDT/4h/{n}.zip", n + ".csv", csv_of(gd, micro=d >= pd.Timestamp("2025-01-01", tz="UTC")))
    if tamper:
        k = next(u for u in files if u.endswith(tamper) and not u.endswith("CHECKSUM"))
        files[k] = files[k][:-5] + b"XXXXX"
    def get(url):
        assert url.startswith("https://data.binance.vision/")
        return files.get(url)
    return get


def test_vision_feed_assembles_closed_bars_and_matches_source():
    df = synth(); now = pd.Timestamp("2023-09-20 12:05", tz="UTC")
    feed = VisionFeed(get_bytes=make_server(df, now))
    got = feed.bars(600, now)
    assert len(got) == 600 and (got.index + H4 <= now).all()
    assert (got.index.to_series().diff().dropna() == H4).all() and not got.index.has_duplicates
    ref = df.loc[got.index]
    assert np.allclose(got["close"], ref["close"]) and np.allclose(got["high"], ref["high"])
    assert got.index[-1] == pd.Timestamp("2023-09-19 20:00", tz="UTC")       # el día en curso aún no está publicado


def test_vision_feed_handles_microsecond_timestamps_after_2025():
    df = synth(start="2025-01-02", n=800); now = pd.Timestamp("2025-04-01 00:30", tz="UTC")
    got = VisionFeed(get_bytes=make_server(df, now)).bars(300, now)
    assert got.index[0] > pd.Timestamp("2025-01-01", tz="UTC") and got.index.year.max() == 2025


def test_vision_feed_rejects_tampered_files_and_foreign_hosts():
    df = synth(); now = pd.Timestamp("2023-09-20 12:05", tz="UTC")
    with pytest.raises(RuntimeError, match="CHECKSUM"):
        VisionFeed(get_bytes=make_server(df, now, tamper="BTCUSDT-4h-2023-08.zip")).bars(600, now)
    from src.live.vision_feed import default_bytes
    with pytest.raises(ValueError, match="no permitida"):
        default_bytes("https://evil.example.com/x.zip")


def test_vision_funding_marks_current_month_as_synthetic():
    now = pd.Timestamp("2023-09-20 12:05", tz="UTC")
    f = VisionFeed(get_bytes=lambda u: None).funding(pd.Timestamp("2023-09-15", tz="UTC"), now)
    assert f["synthetic"].all() and (f["funding_rate"] == 0.0001).all() and f["time"].max() <= now


def test_catchup_is_incremental_and_idempotent():
    df = synth(); d = pathlib.Path(tempfile.mkdtemp())
    cfg = LiveConfig(capital=1000.0, data_dir=d, min_history_bars=300, risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    tr = PaperTrader(cfg, Store(d / "s.db"))
    start = pd.Timestamp("2023-08-25", tz="UTC")
    now1 = pd.Timestamp("2023-09-01 12:05", tz="UTC"); r1 = catchup(cfg, VisionFeed(get_bytes=make_server(df, now1)), start, now1, tr)
    now2 = pd.Timestamp("2023-09-05 12:05", tz="UTC"); r2 = catchup(cfg, VisionFeed(get_bytes=make_server(df, now2)), start, now2, tr)
    r3 = catchup(cfg, VisionFeed(get_bytes=make_server(df, now2)), start, now2, tr)
    assert r1["status"] == "ok" and r1["velas_procesadas"] > 0 and r2["velas_procesadas"] > 0
    assert r3["velas_procesadas"] == 0 and r3["equity"] == r2["equity"]                 # segunda pasada = sin cambios
    # el mismo resultado que procesar todo de una vez
    d2 = pathlib.Path(tempfile.mkdtemp()); tr2 = PaperTrader(LiveConfig(capital=1000.0, data_dir=d2, min_history_bars=300, risk=cfg.risk), Store(d2 / "s.db"))
    rall = catchup(LiveConfig(capital=1000.0, data_dir=d2, min_history_bars=300, risk=cfg.risk), VisionFeed(get_bytes=make_server(df, now2)), start, now2, tr2)
    assert rall["equity"] == pytest.approx(r2["equity"], rel=1e-12) and rall["operaciones_total"] == r2["operaciones_total"]
    assert (d / "equity.csv").exists() and (d / "trades.csv").exists()
