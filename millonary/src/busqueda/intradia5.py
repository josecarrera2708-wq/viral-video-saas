"""Utilidades de la búsqueda v11 (intradía 15 min-4 h ejecutada en velas de 5 min): datos, velas completas, resumen por periodo y puertas.
Datos: perpetuo BTCUSDT de Binance (data.binance.vision), 5 min desde 2020-01; funding de perp_BTCUSDT_funding_v11.parquet."""
from __future__ import annotations
import numpy as np
import pandas as pd
import scipy.stats as st
from ..backtest.funding import align_funding
from ..desk15.data import ROOT
from .sim5 import simulate, Gestion, Costes

END = "2026-09-28"
PER = {"construccion": ("2020-03-01", "2024-01-01"), "validacion": ("2024-01-01", "2025-07-01"), "examen": ("2025-07-01", END)}
RAW = ROOT / "data" / "raw"
COLS = ["open", "high", "low", "close", "volume", "trades", "taker_buy_base"]


def load5() -> tuple[pd.DataFrame, np.ndarray]:
    d = pd.read_parquet(RAW / "perp_BTCUSDT_5m.parquet").set_index("time")[COLS]
    d.index = d.index.astype("datetime64[ns, UTC]"); d = d[d.index < pd.Timestamp(END, tz="UTC") + pd.Timedelta("1D")]
    ev = pd.read_parquet(RAW / "perp_BTCUSDT_funding_v11.parquet")
    ev = ev[(ev["time"] > d.index[0]) & (ev["time"] <= d.index[-1] + pd.Timedelta("5min"))]
    return d, align_funding(d.index, pd.Timedelta("5min"), ev[["time", "funding_rate"]])


def bars(b5: pd.DataFrame, tf: str) -> pd.DataFrame:
    """Velas COMPLETAS de 15 min / 1 h a partir de las de 5 min (índice = apertura)."""
    n = {"15m": 3, "1h": 12, "4h": 48}[tf]
    g = b5.resample(tf.replace("m", "min"), label="left", closed="left")
    out = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "trades": "sum", "taker_buy_base": "sum"})
    return out[g["close"].count() == n].dropna()


def metrics(index: pd.DatetimeIndex, tf: str) -> pd.DataFrame:
    """Métricas de derivados de Binance (OI, ratios) conocidas AL CIERRE de cada vela: el dato con sello t se usa desde t + 5 min."""
    m = pd.read_parquet(RAW / "perp_BTCUSDT_metrics_5m.parquet").sort_values("time")
    m["known"] = (m["time"] + pd.Timedelta("5min")).astype("datetime64[ns, UTC]")
    close_t = pd.DataFrame({"t": (index + pd.Timedelta(tf.replace("m", "min"))).astype("datetime64[ns, UTC]")})
    out = pd.merge_asof(close_t, m.drop(columns="time").rename(columns={"known": "t"}), on="t", direction="backward",
                        tolerance=pd.Timedelta("30min"))
    out.index = index
    return out.drop(columns="t")


def run_period(b5, f5, sig: dict, g: Gestion, per: str, costes: Costes = Costes(), lim_bars: int = 0) -> pd.DataFrame:
    a, b = (pd.Timestamp(x, tz="UTC") for x in PER[per])
    t = pd.DatetimeIndex(sig["t"]); m = (t >= a) & (t < b)
    lim = None if sig.get("lim") is None else np.asarray(sig["lim"])[m]
    return simulate(b5, f5, t[m], np.asarray(sig["d"])[m], np.asarray(sig["sd"])[m], g, costes, lim, lim_bars)


def resumen(tr: pd.DataFrame, per: str, capital: float = 1000.0) -> dict:
    a, b = (pd.Timestamp(x, tz="UTC") for x in PER[per]); days = (b - a).days
    n = len(tr); R = tr["R"].to_numpy() if n else np.zeros(0)
    eq = pd.Series(capital + np.cumsum(tr["pnl"].to_numpy()), index=tr["salida"]) if n else pd.Series(dtype=float)
    eq = pd.concat([pd.Series([capital], index=[a]), eq]).groupby(level=0).last()
    dd = eq.resample("1D").last().ffill(); ret = dd.pct_change().dropna()
    t = float(R.mean() / (R.std(ddof=1) / np.sqrt(n))) if n > 2 and R.std(ddof=1) > 0 else 0.0
    return {"n": n, "por_dia": n / days, "acierto": float((R > 0).mean()) if n else 0.0, "R_media": float(R.mean()) if n else 0.0, "t_R": t,
            "p_1s": float(1 - st.t.cdf(t, df=max(n - 1, 1))) if n > 2 else 1.0, "retorno": float(eq.iloc[-1] / capital - 1),
            "caida_max": float((1 - eq / eq.cummax()).max()), "sharpe": float(ret.mean() / ret.std(ddof=1) * np.sqrt(365)) if len(ret) > 10 and ret.std(ddof=1) > 0 else 0.0,
            "activadas": float(tr["activada"].mean()) if n else 0.0, "diario": ret.to_numpy()}
