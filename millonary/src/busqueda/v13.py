"""Búsqueda v13 (config/busqueda_v13_prerregistrada.md): SWING de 1 a 3 días con el filtro estadístico de v12.

Mismo método que v12 (meta-etiquetado: un modelo decide qué señales tomar), pero con barreras de swing para que las comisiones pesen poco:
stop s = máx(2 %; 2·ATR14 de 4 h) (≤ 8 %), objetivo 2R/3R, barrera de tiempo de 72 h. Coste de ida y vuelta ≈ 0,07 R o menos.
Señales: las de 1 h, 2 h y 4 h ya programadas (mesa de 1 h, patrones v7 en 1 h y 4 h, setups v11). Se excluye la mesa de 15 min.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import atr
from ..intraday import setups as I1
from .intradia5 import bars
from .sim5 import Gestion
from .v7 import GRUPOS, _patron
from . import v11, v12
from .v12 import (etiquetas, pesos_unicidad, wl, ev_neto, riesgo_kelly, COSTE_CERO, EV_MIN,  # noqa: F401  (misma API que v12)
                  RIESGO_MIN, RIESGO_MAX, MAX_POS, RIESGO_ABIERTO)

S_MIN_PCT, S_ATR, S_MAX_PCT = 0.02, 2.0, 0.08            # stop s = máx(2 %; 2·ATR14 de 4 h), ≤ 8 %
HORAS = 72.0                                            # barrera de tiempo: 3 días
VENTANA = pd.Timedelta("4h")                             # señales en la misma dirección dentro de 4 h = un evento; opuestas → fuera
CONFIGS = {"C1 2R": Gestion(k=2.0, horas=HORAS, modo=0), "C2 3R": Gestion(k=3.0, horas=HORAS, modo=0),
           "C3 2R + protección (promediar 1 vez)": Gestion(k=2.0, horas=HORAS, modo=1, a=1.0, m=1.0, b=2.0, hh=0.1)}
APAL_MAX = {"5m": 3.0, "1h": 3.0, "2h": 3.0, "4h": 2.0}   # tope de apalancamiento por temporalidad de la señal (swing: más bajo)
ORIGENES = ("I", "E", "S")


def señales(b5: pd.DataFrame, con_oi: bool = True) -> pd.DataFrame:
    h1, h4 = bars(b5, "1h"), bars(b5, "4h"); L = []
    L += v12._spec_events(h1, I1.all_specs(h1), "1h", "I")
    for df, tf in ((h1, "1h"), (h4, "4h")):
        for g, (kind, sub) in GRUPOS.items():
            r, _ = _patron(df, kind, sub); i = np.flatnonzero(r.d)
            L.append(pd.DataFrame({"t": df.index[i] + pd.Timedelta(tf), "d": np.asarray(r.d)[i].astype(np.int8), "setup": f"{g} {tf}",
                                   "origen": "E", "tf": tf}))
    tfs = {"S1": "5m", "S2": "5m", "S3": "2h", "S4": "1h", "S5": "1h", "S6": "5m"}
    for name, (fn, _h, usa_oi) in v11.SETUPS.items():
        if usa_oi and not con_oi: continue
        s = fn(b5)
        L.append(pd.DataFrame({"t": s["t"], "d": s["d"], "setup": name, "origen": "S", "tf": tfs[name[:2]]}))
    ev = pd.concat(L, ignore_index=True)
    ev["t"] = pd.DatetimeIndex(ev["t"]).astype("datetime64[ns, UTC]")
    return ev.sort_values(["t", "setup"], kind="stable").reset_index(drop=True)


def agrupar(sig: pd.DataFrame) -> pd.DataFrame:
    """Como v12.agrupar, con ventana de 4 h y orígenes I/E/S."""
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
    """s = máx(2 %·P; 2·ATR14 de 4 h) con la última vela de 4 h CERRADA y P = último cierre de 5 min; NaN si s > 8 %."""
    h = bars(b5, "4h"); a = atr(h, 14)
    A = pd.DataFrame({"k": (h.index + pd.Timedelta("4h")).astype("datetime64[ns, UTC]"), "atr": a.to_numpy()})
    P = pd.DataFrame({"k": (b5.index + pd.Timedelta("5min")).astype("datetime64[ns, UTC]"), "P": b5["close"].to_numpy()})
    T = pd.DataFrame({"k": ev["t"].astype("datetime64[ns, UTC]")})
    x = pd.merge_asof(T, A, on="k", direction="backward"); x = pd.merge_asof(x, P, on="k", direction="backward")
    s = np.maximum(S_MIN_PCT * x["P"].to_numpy(), S_ATR * x["atr"].to_numpy())
    return np.where(s / x["P"].to_numpy() <= S_MAX_PCT, s, np.nan)


def variables(b5: pd.DataFrame, ev: pd.DataFrame, s: np.ndarray, gemelo: bool = False) -> pd.DataFrame:
    """Las mismas variables que v12 (lista cerrada), con orígenes y temporalidades de v13."""
    e = ev.copy()
    for o in v12.ORIGENES:
        if "o_" + o not in e: e["o_" + o] = 0
    X = v12.variables(b5, e, s, gemelo=gemelo)
    X = X.drop(columns=[c for c in X if c.startswith("tf_") or c in ("o_P",)])
    for tf in APAL_MAX:
        X["tf_" + tf] = (ev["tf"] == tf).to_numpy(float)
    return X


def cartera(ops: pd.DataFrame, capital: float = 1000.0) -> pd.DataFrame:
    """Igual que v12.cartera con los topes de apalancamiento de swing."""
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
