"""Búsqueda v12 (config/busqueda_v12_prerregistrada.md): FILTRO ESTADÍSTICO de entradas (meta-etiquetado, López de Prado).

Idea: no se entra en todo lo que se ve. Todas las señales ya programadas (mesa intradía 1 h, mesa de 15 min, patrones de 1 h de v7 y setups
de v11) forman los EVENTOS; un modelo estima la probabilidad de que cada evento llegue al objetivo y solo se opera si la esperanza, tras
costes, supera +0,05 R. Barreras iguales para todos los eventos; el tamaño sale de Kelly/4 acotado y el apalancamiento tiene un tope
según la temporalidad de la señal. Ejecución en velas de 5 min (src/busqueda/sim5.py). Todo causal: variables con datos hasta el cierre.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr
from ..intraday import setups as I1
from ..desk15 import setups as D15
from .intradia5 import RAW, bars
from .sim5 import Gestion, Costes, _sim
from .v7 import GRUPOS, _patron
from . import v11

# ---------------- parámetros fijos (prerregistro) ----------------
S_MIN_PCT, S_ATR, S_MAX_PCT = 0.005, 0.75, 0.03          # stop s = máx(0,50 %; 0,75·ATR14 de 1 h), ≤ 3 %
HORAS = 4.0                                             # barrera de tiempo
VENTANA = pd.Timedelta("60min")                          # señales en la misma dirección dentro de 60 min = un evento; opuestas → se descartan
COSTE_IV = 2 * 0.0005 + 2 * 0.0002                       # ida y vuelta taker + deslizamiento (para la variable coste en R)
CONFIGS = {"C1 2R": Gestion(k=2.0, horas=HORAS, modo=0), "C2 3R": Gestion(k=3.0, horas=HORAS, modo=0),
           "C3 2R + protección (promediar 1 vez)": Gestion(k=2.0, horas=HORAS, modo=1, a=1.0, m=1.0, b=2.0, hh=0.1)}
EV_MIN = 0.05                                           # se opera si p·W − (1−p)·L ≥ +0,05 R
RIESGO_MIN, RIESGO_MAX, KELLY_FRAC = 0.0025, 0.01, 0.25
APAL_MAX = {"5m": 10.0, "15m": 10.0, "1h": 5.0, "2h": 3.0}    # tope de apalancamiento por temporalidad de la señal
MAX_POS, RIESGO_ABIERTO = 2, 0.02
ORIGENES = ("I", "P", "E", "S")                          # mesa 1 h · mesa 15 min · patrones v7 · setups v11


# ---------------- eventos ----------------
def _spec_events(df: pd.DataFrame, specs: dict, tf: str, pref: str) -> list[pd.DataFrame]:
    out = []; step = pd.Timedelta(tf.replace("m", "min"))
    for name, sp in specs.items():
        e = np.asarray(sp.entry); i = np.flatnonzero(e != 0)
        out.append(pd.DataFrame({"t": df.index[i] + step, "d": e[i].astype(np.int8), "setup": name, "origen": pref, "tf": tf}))
    return out


def señales(b5: pd.DataFrame, con_oi: bool = True) -> pd.DataFrame:
    """Todas las señales primarias, sin elegirlas por resultados. t = cierre de la vela de señal."""
    h1, m15 = bars(b5, "1h"), bars(b5, "15m"); L = []
    L += _spec_events(h1, I1.all_specs(h1), "1h", "I")
    L += _spec_events(m15, D15.all_specs(m15), "15m", "P")
    for g, (kind, sub) in GRUPOS.items():
        r, _ = _patron(h1, kind, sub); i = np.flatnonzero(r.d)
        L.append(pd.DataFrame({"t": h1.index[i] + pd.Timedelta("1h"), "d": np.asarray(r.d)[i].astype(np.int8), "setup": g, "origen": "E", "tf": "1h"}))
    tfs = {"S1": "5m", "S2": "5m", "S3": "2h", "S4": "1h", "S5": "1h", "S6": "5m"}
    for name, (fn, _h, usa_oi) in v11.SETUPS.items():
        if usa_oi and not con_oi: continue
        s = fn(b5)
        L.append(pd.DataFrame({"t": s["t"], "d": s["d"], "setup": name, "origen": "S", "tf": tfs[name[:2]]}))
    ev = pd.concat(L, ignore_index=True)
    ev["t"] = pd.DatetimeIndex(ev["t"]).astype("datetime64[ns, UTC]")
    return ev.sort_values(["t", "setup"], kind="stable").reset_index(drop=True)


def agrupar(sig: pd.DataFrame) -> pd.DataFrame:
    """Un evento = racimo de señales cuyo primer elemento abre una ventana de 60 min. Si en el racimo hay direcciones opuestas, se descarta.
    El evento toma la hora, la temporalidad y el setup del PRIMERO (lo que se sabía en ese momento); n_setups = setups distintos del racimo
    que ya habían disparado a la hora del evento (solo el primero o los simultáneos: nada del futuro)."""
    t = sig["t"].to_numpy(); n = len(sig); rows = []; i = 0
    while i < n:
        j = i
        while j + 1 < n and t[j + 1] - t[i] < VENTANA.to_timedelta64():
            j += 1
        blk = sig.iloc[i:j + 1]
        if blk["d"].nunique() == 1:
            now = blk[blk["t"] == blk["t"].iloc[0]]
            r = {"t": blk["t"].iloc[0], "d": int(blk["d"].iloc[0]), "setup": now["setup"].iloc[0], "tf": now["tf"].iloc[0],
                 "n_setups": now["setup"].nunique()}
            for o in ORIGENES:
                r["o_" + o] = int((now["origen"] == o).any())
            rows.append(r)
        i = j + 1
    return pd.DataFrame(rows)


def barrera(b5: pd.DataFrame, ev: pd.DataFrame) -> np.ndarray:
    """s = máx(0,50 %·P; 0,75·ATR14 de 1 h) con la última vela de 1 h CERRADA y P = último cierre de 5 min; NaN si s > 3 %."""
    h = bars(b5, "1h"); a = atr(h, 14)
    A = pd.DataFrame({"k": (h.index + pd.Timedelta("1h")).astype("datetime64[ns, UTC]"), "atr": a.to_numpy()})
    P = pd.DataFrame({"k": (b5.index + pd.Timedelta("5min")).astype("datetime64[ns, UTC]"), "P": b5["close"].to_numpy()})
    T = pd.DataFrame({"k": ev["t"].astype("datetime64[ns, UTC]")})
    x = pd.merge_asof(T, A, on="k", direction="backward"); x = pd.merge_asof(x, P, on="k", direction="backward")
    s = np.maximum(S_MIN_PCT * x["P"].to_numpy(), S_ATR * x["atr"].to_numpy())
    return np.where(s / x["P"].to_numpy() <= S_MAX_PCT, s, np.nan)


# ---------------- etiquetas (cada evento por separado) ----------------
def etiquetas(b5: pd.DataFrame, f5: np.ndarray, ev: pd.DataFrame, s: np.ndarray, g: Gestion, costes: Costes = Costes()) -> pd.DataFrame:
    """R de cada evento simulado AISLADO (sin bloqueo por posición abierta), con el mismo motor que el papel. Devuelve R y hora de salida."""
    o, h, l, c = (b5[k].to_numpy(float) for k in ("open", "high", "low", "close")); fu = np.asarray(f5, float)
    si = np.searchsorted(b5.index.asi8, pd.DatetimeIndex(ev["t"]).asi8, side="left").astype(np.int64)
    d = ev["d"].to_numpy(np.int8); R = np.full(len(ev), np.nan); X = np.full(len(ev), -1, np.int64); why = np.zeros(len(ev), np.int8)
    nan1 = np.array([np.nan]); mb = int(round(g.horas * 12))
    for k in range(len(ev)):
        if not np.isfinite(s[k]) or si[k] >= len(o): continue
        e, x, _, r, *_r, w = _sim(o, h, l, c, fu, si[k:k + 1], s[k:k + 1], nan1, d[k:k + 1], g.k, mb, g.modo, g.a, g.m, g.b, g.hh, g.k2, 0,
                                   costes.taker, costes.maker, costes.slip, costes.pen, costes.riesgo, costes.apal, costes.capital)
        if len(r): R[k] = r[0]; X[k] = x[0]; why[k] = w[0]
    sal = pd.Series(b5.index[np.clip(X, 0, len(b5) - 1)]); sal[X < 0] = pd.NaT
    return pd.DataFrame({"R": R, "salida": sal.to_numpy(), "motivo": why})


COSTE_CERO = Costes(0.0, 0.0, 0.0, 0.0)


# ---------------- variables ----------------
def _z(x: pd.Series, n: int, minp: int) -> pd.Series:
    m = x.shift(1).rolling(n, min_periods=minp).mean(); s = x.shift(1).rolling(n, min_periods=minp).std()
    return (x - m) / s


def _horarias(b5: pd.DataFrame, gemelo: bool) -> pd.DataFrame:
    """Variables por vela de 1 h CERRADA, indexadas por su hora de cierre (= cuándo se conocen)."""
    h = bars(b5, "1h"); c = h["close"]; lr = np.log(c).diff(); a = atr(h, 14)
    v1 = lr.rolling(24).std(); v7 = lr.rolling(168).std()
    F = pd.DataFrame(index=h.index)
    F["vol_1h"] = v1; F["vol_ratio"] = v1 / v7
    F["atr_pct"] = a.rolling(720, min_periods=300).rank(pct=True)
    for n in (1, 4, 24, 168):
        F[f"ret_{n}h"] = np.log(c / c.shift(n)) / (v1 * np.sqrt(n))
    F["dist_ema200"] = (c - ema(c, 200)) / a
    h4 = h["close"].resample("4h", label="left", closed="left").last(); e4 = ema(h4, 50)
    e4.index = e4.index + pd.Timedelta("4h") - pd.Timedelta("1h")              # conocida al cierre de la vela de 4 h
    F["dist_ema50_4h"] = (c - e4.reindex(h.index, method="ffill")) / a
    ti = 2 * h["taker_buy_base"] / h["volume"] - 1
    F["taker_1h"] = _z(ti, 720, 300)
    ti4 = 2 * h["taker_buy_base"].rolling(4).sum() / h["volume"].rolling(4).sum() - 1
    F["taker_4h"] = _z(ti4, 720, 300)
    hr = h.index.hour; vv = h["volume"]
    F["rvol_hora"] = vv / vv.groupby(hr).transform(lambda x: x.shift(1).rolling(20, min_periods=10).mean())
    F["hi24"] = h["high"].rolling(24).max(); F["lo24"] = h["low"].rolling(24).min()
    F["hi7d"] = h["high"].rolling(168).max(); F["lo7d"] = h["low"].rolling(168).min()
    F["close"] = c
    if not gemelo:
        m = pd.read_parquet(RAW / "perp_BTCUSDT_metrics_5m.parquet").sort_values("time")
        m["k"] = (m["time"] + pd.Timedelta("10min")).astype("datetime64[ns, UTC]")
        m.loc[m["sum_open_interest"] <= 0, "sum_open_interest"] = np.nan
        T = pd.DataFrame({"k": (h.index + pd.Timedelta("1h")).astype("datetime64[ns, UTC]")})
        M = pd.merge_asof(T, m.drop(columns="time"), on="k", direction="backward", tolerance=pd.Timedelta("30min")); M.index = h.index
        oi = np.log(M["sum_open_interest"])
        F["doi_4h"] = oi.diff(4); F["doi_24h"] = oi.diff(24); F["oi_x_ret4"] = np.sign(F["ret_4h"]) * F["doi_4h"]
        F["ls_z"] = _z(M["count_long_short_ratio"], 720, 300); F["top_z"] = _z(M["sum_toptrader_long_short_ratio"], 720, 300)
        p = pd.read_parquet(RAW / "perp_BTCUSDT_premium_1h.parquet"); p["k"] = (p["time"] + pd.Timedelta("1h")).astype("datetime64[ns, UTC]")
        F["prima"] = pd.merge_asof(T, p[["k", "premium"]].sort_values("k"), on="k", direction="backward", tolerance=pd.Timedelta("2h"))["premium"].to_numpy()
        fu = pd.read_parquet(RAW / "perp_BTCUSDT_funding_v11.parquet").sort_values("time")
        fu["fz"] = (fu["funding_rate"] - fu["funding_rate"].shift(1).rolling(90, min_periods=30).mean()) / fu["funding_rate"].shift(1).rolling(90, min_periods=30).std()
        fu["k"] = fu["time"].astype("datetime64[ns, UTC]")
        F["funding_z"] = pd.merge_asof(T, fu[["k", "fz"]], on="k", direction="backward")["fz"].to_numpy()
        fg = pd.read_parquet(RAW / "fear_greed.parquet").sort_values("time"); fg["k"] = (fg["time"] + pd.Timedelta("1D")).astype("datetime64[ns, UTC]")
        F["fear_greed"] = pd.merge_asof(T, fg[["k", "fng"]], on="k", direction="backward")["fng"].to_numpy()   # el del día ANTERIOR
    F.index = (h.index + pd.Timedelta("1h")).astype("datetime64[ns, UTC]")
    return F


FIRMADAS = ["ret_1h", "ret_4h", "ret_24h", "ret_168h", "dist_ema200", "dist_ema50_4h", "taker_1h", "taker_4h", "ls_z", "top_z", "prima", "funding_z"]


def variables(b5: pd.DataFrame, ev: pd.DataFrame, s: np.ndarray, gemelo: bool = False) -> pd.DataFrame:
    """Lista cerrada. Datos hasta el cierre de la señal (última vela de 1 h cerrada). Firmadas por el lado (×d)."""
    H = _horarias(b5, gemelo)
    T = pd.DataFrame({"k": ev["t"].astype("datetime64[ns, UTC]")})
    X = pd.merge_asof(T, H.reset_index(names="k"), on="k", direction="backward").drop(columns="k")
    d = ev["d"].to_numpy(float); P = X["close"].to_numpy(); s = np.asarray(s, float)
    for c in FIRMADAS:
        if c in X: X[c] = X[c] * d
    X["hueco_24h"] = np.where(d > 0, X["hi24"] - P, P - X["lo24"]) / s
    X["hueco_7d"] = np.where(d > 0, X["hi7d"] - P, P - X["lo7d"]) / s
    pos = (P - X["lo24"]) / (X["hi24"] - X["lo24"]); X["pos_24h"] = np.where(d > 0, pos, 1 - pos)
    X = X.drop(columns=["hi24", "lo24", "hi7d", "lo7d", "close"])
    X["coste_R"] = COSTE_IV * P / s; X["stop_pct"] = s / P
    t = pd.DatetimeIndex(ev["t"]); hh = t.hour + t.minute / 60
    X["hora_sin"] = np.sin(2 * np.pi * hh / 24); X["hora_cos"] = np.cos(2 * np.pi * hh / 24)
    for a, b in ((0, 7), (7, 13), (13, 21), (21, 24)):
        X[f"sesion_{a}_{b}"] = ((hh >= a) & (hh < b)).astype(float)
    X["fin_semana"] = (t.dayofweek >= 5).astype(float)
    X["min_al_funding"] = ((8 - (hh % 8)) % 8) * 60
    X["largo"] = (d > 0).astype(float); X["n_setups"] = ev["n_setups"].to_numpy(float)
    for o in ORIGENES:
        X["o_" + o] = ev["o_" + o].to_numpy(float)
    for tf in APAL_MAX:
        X["tf_" + tf] = (ev["tf"] == tf).to_numpy(float)
    return X.astype(float)


# ---------------- pesos, umbral y tamaño ----------------
def pesos_unicidad(t: pd.Series, salida: pd.Series) -> np.ndarray:
    """1 / nº de etiquetas que se solapan con la de cada evento (incluida ella)."""
    a = pd.DatetimeIndex(t).asi8; b = pd.DatetimeIndex(salida).asi8; o = np.argsort(a); a_s = a[o]
    bs = np.sort(b)
    # solapan con i: los que empiezan antes de que acabe i y acaban después de que empiece i
    n = np.searchsorted(a_s, b, side="right") - np.searchsorted(bs, a, side="left")
    return 1.0 / np.maximum(n, 1)


def wl(R_bruta: np.ndarray) -> tuple[float, float]:
    """W̄ y L̄: medias BRUTAS (sin costes) de ganadoras y |perdedoras| del entrenamiento."""
    R = R_bruta[np.isfinite(R_bruta)]
    return float(R[R > 0].mean()), float(-R[R <= 0].mean())


def ev_neto(p: np.ndarray, W: float, L: float, coste_R: np.ndarray, lu: float) -> np.ndarray:
    """EV = p·(W − c) − (1−p)·(L + c), con c = coste de ida y vuelta en R de pérdida máxima."""
    c = coste_R / lu
    return p * (W - c) - (1 - p) * (L + c)


def riesgo_kelly(p: np.ndarray, p_base: float, W: float, L: float) -> np.ndarray:
    pt = p_base + 0.5 * (p - p_base); f = pt / L - (1 - pt) / W
    return np.clip(KELLY_FRAC * f, RIESGO_MIN, RIESGO_MAX)


def cartera(ops: pd.DataFrame, capital: float = 1000.0) -> pd.DataFrame:
    """Simula el capital con las operaciones elegidas (orden de entrada): ≤2 posiciones, riesgo abierto ≤2 %, nunca opuestas.
    Riesgo por operación = Kelly/4 acotado; nocional ≤ tope de apalancamiento de su temporalidad × capital. pnl = R · riesgo efectivo · capital."""
    ops = ops.sort_values("t").reset_index(drop=True); eq = capital; abiertas = []; rows = []
    for r in ops.itertuples():
        for x in [x for x in abiertas if x[0] <= r.t]:
            eq += x[3]
        abiertas = [x for x in abiertas if x[0] > r.t]
        if len(abiertas) >= MAX_POS or any(x[1] != r.d for x in abiertas): continue
        rk = min(r.riesgo, RIESGO_ABIERTO - sum(x[2] for x in abiertas))
        if rk < RIESGO_MIN: continue
        apal = rk / (r.stop_pct * r.lu)
        if apal > APAL_MAX[r.tf]:
            rk = APAL_MAX[r.tf] * r.stop_pct * r.lu; apal = APAL_MAX[r.tf]
        pnl = r.R * rk * eq
        abiertas.append((r.salida, r.d, rk, pnl)); rows.append({"t": r.t, "salida": r.salida, "d": r.d, "tf": r.tf, "R": r.R, "riesgo": rk, "apal": apal, "pnl": pnl})
    out = pd.DataFrame(rows)
    if len(out):
        x = out.sort_values("salida"); x["capital"] = capital + x["pnl"].cumsum(); out = out.join(x[["capital"]])
    return out
