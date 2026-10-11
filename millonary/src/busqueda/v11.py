"""Búsqueda v11 (config/busqueda_v11_prerregistrada.md): intradía 15 min-4 h con objetivo 2R/3R y «entrada de protección».
Setups propuestos por los agentes de investigación (docs/investigacion_v11/), con sus parámetros de fuente. Señal al CIERRE de una vela;
ejecución en velas de 5 min (src/busqueda/sim5.py). Cada generador devuelve {"t": cierre de la vela de señal, "d": ±1, "sd": distancia de stop}.

S1 ORB 60 min de la apertura de Nueva York + volumen relativo (Zarattini-Barbon-Aziz; cazador académico n.º 4)
S2 ORB 15 min, mismas reglas (cazador de traders n.º 1)
S3 Reversión tras salto ≥3σ en velas de 2 h (De Nicola 2021; cazador académico n.º 3)
S4 Rebote tras cascada de liquidaciones inferida: −4σ en 1 h + caída del OI + volumen extremo (cazador de flujo E1)
S5 Squeeze contra el lado abarrotado: prima extrema + OI creciente + ruptura de 24 h (cazador de flujo E3)
S6 Recuperación / rechazo del VWAP de la sesión de Nueva York (cazador de traders n.º 2)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from ..signals.indicators import atr
from .intradia5 import RAW, bars
from .sim5 import Gestion

NY = "America/New_York"
SD_MIN, SD_MAX = 0.0035, 0.03          # stop válido entre 0,35 % y 3 % del precio (cazador de traders); fuera, no se opera
GESTIONES = {
    "2R": lambda h: Gestion(k=2.0, horas=h, modo=0),
    "3R": lambda h: Gestion(k=3.0, horas=h, modo=0),
    "C2 una entrada, stop doble": lambda h: Gestion(k=1.0, horas=h, modo=0),          # sd×2 y objetivo en el mismo precio que 2R
    "P3 protección: promediar 1 vez": lambda h: Gestion(k=2.0, horas=h, modo=1, a=1.0, m=1.0, b=2.0, hh=0.1),
    "P4 protección: girar 1 vez": lambda h: Gestion(k=2.0, horas=h, modo=2, a=1.0, m=1.0, b=1.0, k2=2.0),
}
SD_MULT = {"C2 una entrada, stop doble": 2.0}


def _nyse_days(idx_ny: pd.DatetimeIndex) -> np.ndarray:
    d = idx_ny.normalize().tz_localize(None)
    hol = USFederalHolidayCalendar().holidays(d.min(), d.max())
    return (idx_ny.dayofweek < 5) & ~d.isin(hol)


def _out(t, d, sd, close):
    t, d, sd, close = (np.asarray(x) for x in (t, d, sd, close))
    ok = (d != 0) & np.isfinite(sd) & (sd / close >= SD_MIN) & (sd / close <= SD_MAX)
    return {"t": pd.DatetimeIndex(t[ok]), "d": d[ok].astype(np.int8), "sd": sd[ok].astype(float)}


def s_orb(b5: pd.DataFrame, minutos: int) -> dict:
    """Rango de los primeros `minutos` tras las 09:30 NY; RVOL ≥ 1 frente a la media del mismo tramo en los 14 días hábiles previos;
    dirección = signo del rango (cierre − apertura); señal = primer cierre de 5 min fuera del rango antes de las 12:00 NY; stop = otro extremo."""
    ny = b5.index.tz_convert(NY); mins = ny.hour * 60 + ny.minute; day = ny.normalize()
    ok_day = _nyse_days(ny)
    in_rng = ok_day & (mins >= 570) & (mins < 570 + minutos)
    g = b5[in_rng].groupby(day[in_rng])
    R = pd.DataFrame({"H": g["high"].max(), "L": g["low"].min(), "O": g["open"].first(), "C": g["close"].last(), "V": g["volume"].sum(),
                      "n": g["close"].count()})
    R = R[R["n"] == minutos // 5]
    R["rvol"] = R["V"] / R["V"].shift(1).rolling(14, min_periods=10).mean()
    R["dir"] = np.sign(R["C"] - R["O"])
    t, d, sd, cl = [], [], [], []
    after = ok_day & (mins >= 570 + minutos) & (mins < 720)
    sub = b5[after]; sday = day[after]
    for dd, grp in sub.groupby(sday):
        if dd not in R.index: continue
        r = R.loc[dd]
        if not (r["rvol"] >= 1.0) or r["dir"] == 0: continue
        c = grp["close"].to_numpy()
        hit = np.flatnonzero(c > r["H"]) if r["dir"] > 0 else np.flatnonzero(c < r["L"])
        if len(hit) == 0: continue
        i = hit[0]; px = c[i]
        t.append(grp.index[i] + pd.Timedelta("5min")); d.append(int(r["dir"])); cl.append(px)
        sd.append(px - r["L"] if r["dir"] > 0 else r["H"] - px)
    return _out(t, d, sd, cl)


def s_salto2h(b5: pd.DataFrame) -> dict:
    """Velas de 2 h alineadas a horas pares UTC; r = ln(C/C₋₁); σ = desviación de las 360 barras previas.
    r ≥ +3σ → corto, r ≤ −3σ → largo. Stop 1σ (en precio), objetivo 2R, salida a las 2 h."""
    g = b5.resample("2h", label="left", closed="left")
    b = g.agg({"open": "first", "high": "max", "low": "min", "close": "last"})[g["close"].count() == 24].dropna()
    r = np.log(b["close"]).diff(); s = r.shift(1).rolling(360, min_periods=300).std()
    d = np.where(r >= 3 * s, -1, np.where(r <= -3 * s, 1, 0))
    return _out(b.index + pd.Timedelta("2h"), d, (s * b["close"]).to_numpy(), b["close"].to_numpy())


def _oi_hourly(index_1h: pd.DatetimeIndex) -> pd.DataFrame:
    """OI (BTC) y prima conocidos al cierre de cada vela de 1 h. OI: registro con sello ≤ cierre − 10 min. Prima: vela de 1 h ya cerrada."""
    m = pd.read_parquet(RAW / "perp_BTCUSDT_metrics_5m.parquet")[["time", "sum_open_interest"]].sort_values("time")
    m.loc[m["sum_open_interest"] <= 0, "sum_open_interest"] = np.nan
    m["t"] = (m["time"] + pd.Timedelta("10min")).astype("datetime64[ns, UTC]")
    T = pd.DataFrame({"t": (index_1h + pd.Timedelta("1h")).astype("datetime64[ns, UTC]")})
    oi = pd.merge_asof(T, m[["t", "sum_open_interest"]], on="t", direction="backward", tolerance=pd.Timedelta("30min"))["sum_open_interest"].to_numpy()
    p = pd.read_parquet(RAW / "perp_BTCUSDT_premium_1h.parquet")
    p["t"] = (p["time"] + pd.Timedelta("1h")).astype("datetime64[ns, UTC]")
    pr = pd.merge_asof(T, p[["t", "premium"]].sort_values("t"), on="t", direction="backward", tolerance=pd.Timedelta("1h"))["premium"].to_numpy()
    return pd.DataFrame({"oi": oi, "prem": pr}, index=index_1h)


def _pct_prev(x: pd.Series, n: int, q: float, minp: int) -> pd.Series:
    return x.shift(1).rolling(n, min_periods=minp).quantile(q)


def s_cascada(b5: pd.DataFrame) -> dict:
    h = bars(b5, "1h"); X = _oi_hourly(h.index); a = atr(h, 14)
    r = np.log(h["close"]).diff(); s = r.shift(1).rolling(720, min_periods=600).std()
    doi = np.log(X["oi"]).diff()                                    # ΔOI de 60 min
    p5 = _pct_prev(doi, 720, 0.05, 500); v95 = _pct_prev(h["volume"], 720, 0.95, 500)
    ti = 2 * h["taker_buy_base"] / h["volume"] - 1
    base = (doi <= p5) & (h["volume"] >= v95)
    d = np.where(base & (r <= -4 * s) & (ti < 0), 1, np.where(base & (r >= 4 * s) & (ti > 0), -1, 0))
    c, hi, lo = h["close"], h["high"], h["low"]
    raw = np.where(d > 0, c - lo, hi - c) + 0.25 * a
    sd = np.clip(raw, a, 3 * a)
    return _out(h.index + pd.Timedelta("1h"), d, sd.to_numpy(), c.to_numpy())


def s_squeeze(b5: pd.DataFrame) -> dict:
    h = bars(b5, "1h"); X = _oi_hourly(h.index); a = atr(h, 14)
    prem8 = X["prem"].rolling(8, min_periods=8).mean()
    lo5 = _pct_prev(prem8, 2160, 0.05, 1500); hi95 = _pct_prev(prem8, 2160, 0.95, 1500)
    doi24 = np.log(X["oi"]).diff(24); q80 = _pct_prev(doi24, 2160, 0.80, 1500)
    c, hi, lo = h["close"], h["high"], h["low"]
    up = c > hi.shift(1).rolling(24).max(); dn = c < lo.shift(1).rolling(24).min()
    d = np.where((prem8 <= lo5) & (doi24 >= q80) & up, 1, np.where((prem8 >= hi95) & (doi24 >= q80) & dn, -1, 0))
    raw = np.where(d > 0, c - lo, hi - c) + 0.25 * a
    return _out(h.index + pd.Timedelta("1h"), d, np.clip(raw, a, 3 * a).to_numpy(), c.to_numpy())


def s_vwap(b5: pd.DataFrame) -> dict:
    """VWAP (precio típico) anclado a las 09:30 NY. Entre 10:00 y 14:00 NY: ≥6 cierres seguidos por debajo y luego un cierre por encima con
    volumen ≥ media de 20 velas → largo (corto simétrico). Stop: extremo del tramo bajo el VWAP − 0,1·ATR(14) de 5 min. Una por lado y día."""
    ny = b5.index.tz_convert(NY); mins = ny.hour * 60 + ny.minute; day = ny.normalize()
    sess = _nyse_days(ny) & (mins >= 570) & (mins < 960)
    a5 = atr(b5, 14).to_numpy(); vm = b5["volume"].shift(1).rolling(20).mean().to_numpy()
    t, d, sd, cl = [], [], [], []
    for dd, grp in b5[sess].groupby(day[sess]):
        tp = (grp["high"] + grp["low"] + grp["close"]) / 3; v = grp["volume"]
        vw = ((tp * v).cumsum() / v.cumsum()).to_numpy(); c = grp["close"].to_numpy(); hi = grp["high"].to_numpy(); lo = grp["low"].to_numpy()
        gm = (grp.index.tz_convert(NY).hour * 60 + grp.index.tz_convert(NY).minute).to_numpy()
        pos = b5.index.get_indexer(grp.index); done = {1: False, -1: False}; run_b = run_a = 0
        for i in range(len(grp)):
            if i > 0 and 600 <= gm[i] < 840:
                for s_, run in ((1, run_b), (-1, run_a)):
                    cross = (c[i] > vw[i]) if s_ == 1 else (c[i] < vw[i])
                    if not done[s_] and run >= 6 and cross and v.iloc[i] >= vm[pos[i]]:
                        seg = slice(i - run, i)
                        ext = lo[seg].min() - 0.1 * a5[pos[i]] if s_ == 1 else hi[seg].max() + 0.1 * a5[pos[i]]
                        t.append(grp.index[i] + pd.Timedelta("5min")); d.append(s_); cl.append(c[i]); sd.append(abs(c[i] - ext)); done[s_] = True
            run_b = run_b + 1 if c[i] < vw[i] else 0
            run_a = run_a + 1 if c[i] > vw[i] else 0
    return _out(t, d, sd, cl)


SETUPS = {
    "S1 ORB 60 min Nueva York + volumen": (lambda b5: s_orb(b5, 60), 4.0, False),
    "S2 ORB 15 min Nueva York + volumen": (lambda b5: s_orb(b5, 15), 4.0, False),
    "S3 Reversión tras salto 3σ (2 h)": (s_salto2h, 2.0, False),
    "S4 Rebote tras cascada (OI)": (s_cascada, 4.0, True),
    "S5 Squeeze contra el lado abarrotado": (s_squeeze, 4.0, True),
    "S6 VWAP de Nueva York": (s_vwap, 4.0, False),
}   # (generador, horas máximas, usa OI/prima → sin pre-muestra)
