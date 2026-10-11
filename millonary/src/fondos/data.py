"""Datos de la mesa de fondos: velas DIARIAS de BTC (día UTC, 00:00 → 24:00).

Columnas: open/high/low/close del contado (Binance spot), pclose = cierre del perpetuo USDT-M (desde 2020-01), f = suma de las tasas
de funding liquidadas dentro del día (00:00, 24:00] (sintético 0,01 %/8 h antes de 2020 y en el mes aún no publicado), f_real.
Histórico: data/raw (2017-08 → 2026-09-28) + Binance Vision, congelado en paper_state/fondos/hist.parquet para la rutina.
Hacia delante: archivos diarios de Binance Vision verificados por SHA-256. Todo se recalcula desde el principio en cada ejecución,
así que el funding sintético del mes en curso se sustituye solo por el real cuando Binance publica el mes.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from ..backtest.funding import align_funding

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
D = ROOT / "paper_state" / "fondos"
DAY, H4 = pd.Timedelta("1D"), pd.Timedelta("4h")


def _splice_spot(d: pd.DataFrame) -> pd.DataFrame:
    """Igual que el núcleo: excluye la caída del servidor de feb-2018 y empalma sin retorno artificial; rejilla de 4 h completa."""
    a, b = pd.Timestamp("2018-02-08", tz="UTC"), pd.Timestamp("2018-02-11", tz="UTC")
    pre, post = d[d.index < a], d[d.index >= b].copy()
    if len(pre) and len(post):
        post[["open", "high", "low", "close"]] *= pre["close"].iloc[-1] / post["open"].iloc[0]
        d = pd.concat([pre, post])
    full = pd.date_range(d.index[0], d.index[-1], freq="4h", tz="UTC"); d = d.reindex(full)
    d["close"] = d["close"].ffill()
    for c in ("open", "high", "low"):
        d[c] = d[c].fillna(d["close"])
    return d


def _grid(d: pd.DataFrame) -> pd.DataFrame:
    """Precios REALES en la rejilla de 4 h; los huecos (caída del servidor de feb-2018) se rellenan planos con el último cierre.
    No se reescala como en el núcleo: el carry compara el nivel del contado con el del perpetuo y la rutina empalma datos nuevos reales
    (la primera ejecución con el empalme ×0,89 dio al carry una beta oculta de −0,11; corregido y anotado en el registro)."""
    full = pd.date_range(d.index[0], d.index[-1], freq="4h", tz="UTC"); d = d.reindex(full)
    d["close"] = d["close"].ffill()
    for c in ("open", "high", "low"):
        d[c] = d[c].fillna(d["close"])
    return d


def to_daily(b4: pd.DataFrame) -> pd.DataFrame:
    """Velas diarias desde las de 4 h; solo días con sus 6 velas."""
    g = b4.groupby(b4.index.floor("1D"))
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(), "n": g["close"].count()})
    return out[out["n"] == 6].drop(columns="n")


def funding_daily(idx: pd.DatetimeIndex, events: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Suma de tasas por día; antes de 2020 sintético 0,0003/día (3 × 0,01 %), como en el núcleo."""
    real_from = pd.Timestamp("2020-01-01", tz="UTC")
    ev = events[(events["time"] > idx[0]) & (events["time"] <= idx[-1] + DAY)]
    f = align_funding(idx, DAY, ev[["time", "funding_rate"]]) if len(ev) else np.zeros(len(idx))
    real = np.asarray(idx >= real_from)
    f = np.where(real, f, 0.0003)
    syn = ev[ev.get("synthetic", pd.Series(False, index=ev.index)).astype(bool)]["time"] if len(ev) else pd.Series(dtype="datetime64[ns, UTC]")
    has_syn = np.zeros(len(idx), bool)
    if len(syn):
        k = np.searchsorted(idx.asi8, pd.DatetimeIndex(syn).asi8, side="left") - 1
        has_syn[k[(k >= 0) & (k < len(idx))]] = True
    return f, real & ~has_syn


def build_history(now: pd.Timestamp | None = None) -> pd.DataFrame:
    """Histórico completo desde data/raw + Vision hasta el último día cerrado (se usa para congelar hist.parquet y para evaluar)."""
    from ..live.vision_feed import VisionFeed, SPOT
    now = now or pd.Timestamp.now(tz="UTC")
    s4 = pd.read_parquet(RAW / "spot_BTCUSDT_4h.parquet").set_index("time")[["open", "high", "low", "close"]]
    p4 = pd.read_parquet(RAW / "perp_BTCUSDT_4h.parquet").set_index("time")[["open", "high", "low", "close"]]
    s4, p4 = _append_vision(s4, VisionFeed(base=SPOT), now), _append_vision(p4, VisionFeed(), now)
    d = to_daily(_grid(s4))
    pc = to_daily(p4)["close"]
    d["pclose"] = pc.reindex(d.index)
    fr = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")[["time", "funding_rate"]]
    fr["time"] = pd.DatetimeIndex(fr["time"]).round("min"); fr["synthetic"] = False
    last = fr["time"].max()
    newf = VisionFeed().funding(last, now)
    ev = pd.concat([fr, newf]).drop_duplicates("time", keep="last").sort_values("time")
    d["f"], d["f_real"] = funding_daily(d.index, ev)
    d = d[d.index + DAY <= now]
    return d


def _append_vision(b4: pd.DataFrame, feed, now: pd.Timestamp) -> pd.DataFrame:
    a = b4.index[-1] + H4
    days = int((now.floor("1D") - a.floor("1D")) / DAY)
    if days <= 0:
        return b4
    new = feed.bars(days * 6 + 12, now)[["open", "high", "low", "close"]]
    new = new[new.index >= a]
    return pd.concat([b4, new]).sort_index().loc[lambda x: ~x.index.duplicated()]


def load(now: pd.Timestamp | None = None) -> pd.DataFrame:
    """Histórico congelado + días nuevos de Binance Vision (para la rutina hacia delante)."""
    from ..live.vision_feed import VisionFeed, SPOT
    now = now or pd.Timestamp.now(tz="UTC")
    h = pd.read_parquet(D / "hist.parquet")
    a = h.index[-1] + DAY
    if now.floor("1D") - a < DAY:
        return h
    s4 = VisionFeed(base=SPOT).bars(int((now - a) / H4) + 12, now); p4 = VisionFeed().bars(int((now - a) / H4) + 12, now)
    s4, p4 = s4[s4.index >= a], p4[p4.index >= a]
    if not len(s4):
        return h
    nd = to_daily(s4[["open", "high", "low", "close"]])
    nd["pclose"] = to_daily(p4[["open", "high", "low", "close"]])["close"].reindex(nd.index) if len(p4) else np.nan
    ev = VisionFeed().funding(a - DAY, now)
    nd["f"], nd["f_real"] = funding_daily(nd.index, ev) if len(nd) else (np.zeros(0), np.zeros(0, bool))
    nd = nd[nd.index + DAY <= now]
    return pd.concat([h, nd]).sort_index().loc[lambda x: ~x.index.duplicated()]

