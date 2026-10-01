"""Aprendizaje rápido y causal de la mesa de 15 min (prerregistro: config/mesa15_prerregistrada.md, sección «Aprendizaje»).

Un aprendiz NO cambia las reglas del trader: VETA señales en contextos donde la evidencia ya acumulada (solo operaciones CERRADAS antes de la señal)
dice que el trader pierde. Contexto = 3 dimensiones independientes (9 niveles):
  tendencia (a favor / en contra / sin tendencia de la EMA 3200 ≈ 800 h) · volatilidad (tercil del percentil ATR) · sesión UTC (Asia / Europa / EE. UU.)
Regla de veto (relativa): nivel con n ≥ n_min cuya R media es PEOR que la media global de ese conjunto de operaciones con t ≤ −1 (t = (R media del nivel − R media global) / error típico del nivel).
Una regla absoluta («R media < 0») vetaba casi todo, porque con costes la mayoría de contextos pierde: aprender a no operar nunca no enseña nada.
A (individual): n_min = 6 con las operaciones del propio trader.  C (colectivo): n_min = 15 con las de toda la sala.
Es una hipótesis estadística: con pocas operaciones puede aprender ruido, por eso opera en papel junto a su base.
"""
from __future__ import annotations
from dataclasses import replace
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr
from ..intraday.setups import Spec

N_MIN = {"A": 6, "C": 15}
T_VETO = -1.0
DIMS = ["Tendencia", "Volatilidad", "Sesión"]
LEVELS = [["a favor de la tendencia", "en contra de la tendencia", "sin tendencia clara"], ["volatilidad baja", "volatilidad media", "volatilidad alta"],
          ["sesión Asia (22-08 UTC)", "sesión Europa (08-14 UTC)", "sesión EE. UU. (14-22 UTC)"]]
LABELS = [LEVELS[d][k] for d in range(3) for k in range(3)]


def context15(bars: pd.DataFrame) -> pd.DataFrame:
    """Contexto causal por vela de 15 min: tendencia de fondo (EMA 3200 ≈ 800 h) y percentil de volatilidad (ATR/precio, ventana 2000)."""
    c = bars["close"]
    return pd.DataFrame({"trend": np.sign(c - ema(c, 3200)), "atr_pct": (atr(bars, 14) / c).rolling(2000, min_periods=400).rank(pct=True)}, index=bars.index)


def level_ids(bars: pd.DataFrame, ctx: pd.DataFrame, side: np.ndarray) -> np.ndarray:
    """Matriz (3, n) con el nivel de cada dimensión (0-2) para una señal de lado `side` (+1/−1) en cada vela."""
    tr = ctx["trend"].to_numpy(); ap = ctx["atr_pct"].to_numpy(); hr = bars.index.hour.to_numpy()
    d0 = np.where(tr == 0, 2, np.where(tr == side, 0, 1)); d1 = np.where(np.isnan(ap), 1, np.where(ap < 1 / 3, 0, np.where(ap < 2 / 3, 1, 2)))
    d2 = np.where((hr >= 22) | (hr < 8), 0, np.where(hr < 14, 1, 2))
    return np.vstack([d0, d1, d2]).astype(np.int64)


def _cum_stats(trades: list[tuple], n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """trades = [(exit_idx, levels(3), R)] → acumulados por nivel (9) y por vela de cierre: cnt, sum, sumsq (n+1 columnas)."""
    cnt = np.zeros((9, n + 1)); s = np.zeros((9, n + 1)); ss = np.zeros((9, n + 1))
    for x, lv, r in trades:
        for d in range(3):
            k = d * 3 + int(lv[d]); cnt[k, x] += 1; s[k, x] += r; ss[k, x] += r * r
    return np.cumsum(cnt, 1), np.cumsum(s, 1), np.cumsum(ss, 1)


def veto_state(cnt, s, ss, n_min: int) -> np.ndarray:
    """(9, n+1) booleano: el nivel está vetado con la evidencia acumulada hasta cada vela."""
    with np.errstate(divide="ignore", invalid="ignore"):
        mean = s / cnt; var = (ss - cnt * mean ** 2) / np.maximum(cnt - 1, 1); se = np.sqrt(np.maximum(var, 1e-12) / cnt)
        glob = s[0:3].sum(0) / np.maximum(cnt[0:3].sum(0), 1)              # cada operación cuenta una vez en cada dimensión: la dimensión 0 basta
        t = (mean - glob) / se
    return (cnt >= n_min) & (mean < glob) & (t <= T_VETO)


def base_trades(r: dict, bars: pd.DataFrame, ctx: pd.DataFrame) -> list[tuple]:
    """Operaciones CERRADAS del motor con el contexto de su señal (vela anterior a la entrada)."""
    out = []
    if int(r["n_trades"]) == 0:
        return out
    ei = np.asarray(r["entry_idx"])[: int(r["n_trades"])]; xi = np.asarray(r["exit_idx"])[: int(r["n_trades"])]; d = np.asarray(r["dir"])[: int(r["n_trades"])]
    R = np.asarray(r["r"])[: int(r["n_trades"])]; reason = np.asarray(r["reason"])[: int(r["n_trades"])]
    for e, x, di, rr, why in zip(ei, xi, d, R, reason):
        if why == 5:                                              # sigue abierta: aún no es evidencia
            continue
        sig = max(int(e) - 1, 0)
        tr = ctx["trend"].iloc[sig]; ap = ctx["atr_pct"].iloc[sig]; hr = bars.index[sig].hour
        lv = (2 if tr == 0 else (0 if tr == di else 1), 1 if np.isnan(ap) else (0 if ap < 1 / 3 else (1 if ap < 2 / 3 else 2)), 0 if (hr >= 22 or hr < 8) else (1 if hr < 14 else 2))
        out.append((int(x), lv, float(rr)))
    return out


def gate(spec: Spec, bars: pd.DataFrame, ctx: pd.DataFrame, trades: list[tuple], n_min: int) -> tuple[Spec, np.ndarray]:
    """Spec del aprendiz: las señales vetadas se anulan. Devuelve también la matriz de veto (9, n+1) para el registro de lo aprendido."""
    n = len(bars); cnt, s, ss = _cum_stats(trades, n); vs = veto_state(cnt, s, ss, n_min)
    ent = np.asarray(spec.entry).copy(); idx = np.flatnonzero(ent != 0)
    for side in (1, -1):
        sel = idx[ent[idx] == side]
        if len(sel) == 0:
            continue
        lv = level_ids(bars, ctx, np.full(n, side))
        blocked = np.zeros(len(sel), bool)
        for d in range(3):
            blocked |= vs[d * 3 + lv[d][sel], sel]               # evidencia con operaciones cerradas en velas ≤ señal
        ent[sel[blocked]] = 0
    return replace(spec, entry=ent.astype(np.int8)), vs


def what_learned(vs: np.ndarray, cnt, s, ss, bars: pd.DataFrame, now_i: int) -> list[dict]:
    """Estado actual de cada nivel y cuándo se vetó por primera vez."""
    out = []
    for k in range(9):
        n_ = cnt[k, now_i]; m = s[k, now_i] / n_ if n_ else 0.0
        first = np.flatnonzero(vs[k, : now_i + 1])
        out.append({"contexto": LABELS[k], "n": int(n_), "R_media": float(m), "vetado": bool(vs[k, now_i]),
                    "vetado_desde": str(bars.index[min(int(first[0]), len(bars) - 1)]) if len(first) else None})
    return out
