"""Fase 2 · primas de riesgo (config/primas_prerregistrada.md). Retornos diarios netos por unidad de capital, día UTC.

B01/B02 · basis trimestral (cash-and-carry con futuro de vencimiento): largo contado + corto trimestral USDT-M, mismos BTC, nocional 1×.
V01/V02 · prima de volatilidad: venta de varianza a 30 d (aproximación de straddle cubierto en delta) con strike = DVOL del día anterior.
Todas causales: lo que se decide a las 00:00 del día d usa solo velas cerradas antes de esa hora.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from src.primas.data import expiries, symbol

SPOT_C, FUT_C = 0.0010 + 0.0002, 0.0005 + 0.0002          # comisión + deslizamiento por lado (contado, futuro)
ENTER_B, EXIT_B2, MIN_DAYS = 0.05, 0.01, 30                # basis anualizado para entrar, para salir antes (B02), días mínimos al vencimiento
RISK_V, VOL_COST, ROLL = 0.005, 1.5, 30                    # VRP: pérdida en un día de 2σ = 0,5 %; coste 1,5 puntos de vol por entrada/rollo; rollo 30 d


def _at(df: pd.DataFrame, t: pd.Timestamp) -> float:
    """Cierre de la vela de 1 h que termina exactamente en t (NaN si no existe)."""
    k = t - pd.Timedelta("1h"); return float(df["close"].get(k, np.nan))


def _last(df: pd.DataFrame, t: pd.Timestamp) -> float:
    """Último cierre disponible de una vela que termina en t o antes (liquidación si falta la última vela del contrato)."""
    x = df["close"][df.index + pd.Timedelta("1h") <= t]; return float(x.iloc[-1]) if len(x) else np.nan


def basis(spot: pd.DataFrame, fut: dict, days: pd.DatetimeIndex, early_exit: bool = False, cm: float = 1.0) -> dict:
    """days: días UTC a evaluar. Decisión a las 00:00 de cada día; vencimiento a las 08:00 (liquidación ≈ cierre de la vela 07:00-08:00
    del futuro, contado vendido al cierre de la misma hora). Devuelve ret diario (indexado por el día), posiciones y operaciones."""
    exps = [e for e in expiries(days[-1] + pd.Timedelta(days=400)) if symbol(e) in fut]
    ret = pd.Series(0.0, index=days); held = pd.Series("", index=days); trades = []
    eq = 1.0; pos = None                                     # pos = dict(sym, exp, q, S0, F0, entrada)
    for d in days:
        t0, t1 = d, d + pd.Timedelta("1D"); e0 = eq
        S = _at(spot, t0)
        if pos is not None and early_exit and t0 < pos["exp"]:
            F = _at(fut[pos["sym"]], t0); left = (pos["exp"] - t0) / pd.Timedelta("1D")
            if np.isfinite(F) and np.isfinite(S) and left > 1 and (F / S - 1) * 365 / left < EXIT_B2:
                eq = pos["cash"] + pos["q"] * S + pos["q"] * (pos["F0"] - F) - pos["q"] * (S * SPOT_C + F * FUT_C) * cm
                trades.append({**_tr(pos), "salida": t0, "px_spot_salida": S, "px_fut_salida": F, "motivo": "basis < 1 %", "ret": eq / pos["eq0"] - 1}); pos = None
        if pos is None and np.isfinite(S):
            for e in exps:
                left = (e - t0) / pd.Timedelta("1D"); F = _at(fut[symbol(e)], t0)
                if left >= MIN_DAYS and np.isfinite(F):
                    if (F / S - 1) * 365 / left > ENTER_B:
                        q = eq / S; cost = q * (S * SPOT_C + F * FUT_C) * cm
                        pos = {"sym": symbol(e), "exp": e, "q": q, "S0": S, "F0": F, "entrada": t0, "eq0": eq, "cash": eq - q * S - cost,
                               "basis_anual": (F / S - 1) * 365 / left}
                    break                                       # solo el trimestral más cercano con ≥ 30 días
        if pos is not None:
            held[d] = pos["sym"]
            if t0 < pos["exp"] <= t1:                           # vence hoy a las 08:00
                Fs, Ss = _last(fut[pos["sym"]], pos["exp"]), _last(spot, pos["exp"])
                eq = pos["cash"] + pos["q"] * Ss + pos["q"] * (pos["F0"] - Fs) - pos["q"] * (Ss * SPOT_C + Fs * FUT_C) * cm
                trades.append({**_tr(pos), "salida": pos["exp"], "px_spot_salida": Ss, "px_fut_salida": Fs, "motivo": "vencimiento", "ret": eq / pos["eq0"] - 1}); pos = None
            else:
                S1, F1 = _at(spot, t1), _at(fut[pos["sym"]], t1)
                if np.isfinite(S1) and np.isfinite(F1):
                    eq = pos["cash"] + pos["q"] * S1 + pos["q"] * (pos["F0"] - F1)
        ret[d] = eq / e0 - 1
    if pos is not None:
        trades.append({**_tr(pos), "salida": None, "px_spot_salida": None, "px_fut_salida": None, "motivo": "abierta", "ret": eq / pos["eq0"] - 1})
    return {"ret": ret, "pos": held, "trades": pd.DataFrame(trades), "n_ops": len(trades)}


def _tr(p):
    return {"contrato": p["sym"], "entrada": p["entrada"], "px_spot": p["S0"], "px_fut": p["F0"], "basis_anual": p["basis_anual"]}


def vrp(close: pd.Series, dvol: pd.Series, days: pd.DatetimeIndex, filt: bool = False, cm: float = 1.0) -> dict:
    """close: precio a las 00:00 de cada día (índice = día). dvol: cierre diario de DVOL (%), índice = día de la vela.
    Día d: IV = DVOL del día d−1; z = r_d / (IV/√365) con r_d = ln(P_{d+1}/P_d); retorno = (RISK_V/3)·(1 − z²) (pérdida RISK_V en un día de 2σ).
    Coste: VOL_COST puntos de vol de vega en cada entrada y cada 30 días en posición = (RISK_V/3)·2·(30/365)·365·VOL_COST/100/IV.
    V02: solo en posición si IV > volatilidad realizada de los 30 días anteriores (ventaja ex ante positiva)."""
    lr = np.log(close.shift(-1) / close)                     # r_d conocido al cierre del día d
    iv = (dvol.shift(1) / 100).reindex(close.index)           # DVOL del día anterior
    rv = np.sqrt((lr.shift(1) ** 2).rolling(30, min_periods=30).mean() * 365)
    ret = pd.Series(0.0, index=days); on = pd.Series(False, index=days); since = None; n_ops = 0
    k = RISK_V / 3
    for d in days:
        I, r = iv.get(d, np.nan), lr.get(d, np.nan)
        want = np.isfinite(I) and np.isfinite(r) and I > 0 and (not filt or (np.isfinite(rv.get(d, np.nan)) and I > rv[d]))
        if not want:
            since = None; continue
        c = 0.0
        if since is None or (d - since).days >= ROLL:
            c = k * 2 * 30 * VOL_COST / 100 / I * cm; since = d; n_ops += 1
        z2 = r ** 2 / (I ** 2 / 365)
        ret[d] = k * (1 - z2) - c; on[d] = True
    return {"ret": ret, "on": on, "n_ops": n_ops}
