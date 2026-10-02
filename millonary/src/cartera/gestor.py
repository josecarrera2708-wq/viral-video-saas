"""Gestor de cartera (Fase 1, config/cartera_prerregistrada.md): HRP, paridad de riesgo, control de caída, CVaR y CPCV.

Todo es causal: los pesos se deciden con datos hasta el cierre del día t y se aplican desde t+1.
"""
from __future__ import annotations
import itertools
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

COST = 0.0015            # 15 pb por unidad de capital que se mueve entre bolsillos (conservador: contado 10+2 pb, perpetuo 5+2 pb)


# ---------------------------------------------------------------- pesos
def hrp_weights(R: pd.DataFrame) -> pd.Series:
    """Hierarchical Risk Parity (López de Prado 2016): enlace simple sobre d = √(½(1−ρ)), cuasi-diagonalización y bisección
    recursiva con la varianza de cada grupo (pesos de mínima varianza ingenua dentro del grupo)."""
    cov, corr = R.cov().to_numpy(copy=True), R.corr().fillna(0.0).to_numpy(copy=True)
    n = len(R.columns)
    if n == 1:
        return pd.Series([1.0], index=R.columns)
    np.fill_diagonal(corr, 1.0)
    dist = np.sqrt(np.clip(0.5 * (1 - corr), 0, None)); np.fill_diagonal(dist, 0.0)
    order = list(leaves_list(linkage(squareform(dist, checks=False), method="single")))
    w = np.ones(n)

    def cvar_(ix):
        c = cov[np.ix_(ix, ix)]; iv = 1 / np.diag(c); iv /= iv.sum(); return float(iv @ c @ iv)

    stack = [order]
    while stack:
        g = stack.pop()
        if len(g) < 2:
            continue
        a, b = g[: len(g) // 2], g[len(g) // 2:]
        va, vb = cvar_(a), cvar_(b); al = 1 - va / (va + vb)
        w[a] *= al; w[b] *= 1 - al
        stack += [a, b]
    return pd.Series(w / w.sum(), index=R.columns)


def inv_vol_weights(R: pd.DataFrame) -> pd.Series:
    s = R.std(ddof=1); w = 1 / s; return w / w.sum()


def month_end(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray((idx + pd.Timedelta("1D")).month != idx.month)


def schedule(R: pd.DataFrame, method: str, win: int = 180, min_obs: int = 90, fixed: dict | None = None) -> pd.DataFrame:
    """Pesos de capital decididos al cierre de cada fin de mes con la ventana [t−win+1, t] y aplicados desde t+1.
    Entra un bolsillo cuando tiene ≥ min_obs días con actividad dentro de la ventana; suma de pesos = 1 (sin apalancamiento)."""
    W = pd.DataFrame(np.nan, index=R.index, columns=R.columns)
    me = month_end(R.index)
    for i in np.flatnonzero(me):
        win_r = R.iloc[max(0, i - win + 1): i + 1]
        ok = [c for c in R.columns if (win_r[c] != 0).sum() >= min_obs and win_r[c].std(ddof=1) > 0]
        if fixed is not None:
            ok = [c for c in fixed if c in ok]
        if not ok:
            W.iloc[i] = 0.0; continue
        if fixed is not None:
            w = pd.Series({c: fixed[c] for c in ok}); w = w / w.sum()
        elif method == "hrp":
            w = hrp_weights(win_r[ok])
        else:
            w = inv_vol_weights(win_r[ok])
        W.iloc[i] = 0.0; W.loc[R.index[i], w.index] = w.values
    return W.ffill().shift(1).fillna(0.0)


def combine(R: pd.DataFrame, W: pd.DataFrame, cm: float = 1.0) -> tuple[pd.Series, pd.Series]:
    """Retorno diario de la cartera (pesos de capital fijos dentro del mes) menos el coste de mover capital entre bolsillos."""
    W = W.reindex(R.index).fillna(0.0)
    turn = W.diff().abs().sum(axis=1); turn.iloc[0] = W.iloc[0].abs().sum()
    return (W * R.fillna(0.0)).sum(axis=1) - turn * COST * cm, turn


def dd_overlay(r: pd.Series, dmax: float = 0.20, floor: float = 0.25, step: float = 0.25, cm: float = 1.0) -> tuple[pd.Series, pd.Series]:
    """Control de caída (Grossman-Zhou 1993, versión por escalones): multiplicador m_t = max(floor, ⌊(1 − DD_{t−1}/dmax)/step⌋·step)
    donde DD es la caída de la cartera SIN control (la «sombra»), para que la exposición se recupere cuando la estrategia se recupera.
    Coste: |Δm| × COST. Lo que no se usa queda en USDT sin rendimiento."""
    eq = (1 + r.fillna(0.0)).cumprod(); dd = 1 - eq / eq.cummax()
    m = np.maximum(floor, np.floor((1 - dd / dmax) / step + 1e-9) * step).clip(upper=1.0)
    m = m.shift(1).fillna(1.0)
    return m * r.fillna(0.0) - m.diff().abs().fillna(0.0) * COST * cm, m


# ---------------------------------------------------------------- medidas
def sharpe(r: pd.Series) -> float:
    sd = r.std(ddof=1); return float(r.mean() / sd * np.sqrt(365)) if len(r) > 20 and sd > 0 else 0.0


def max_dd(r: pd.Series) -> float:
    eq = (1 + r).cumprod(); return float((1 - eq / eq.cummax()).max()) if len(eq) else 0.0


def cagr(r: pd.Series) -> float:
    return float((1 + r).prod() ** (365 / max(len(r), 1)) - 1)


def cvar(r: pd.Series, a: float = 0.05) -> float:
    """CVaR (expected shortfall) diario al 95 %: media del 5 % de peores días (en positivo = pérdida)."""
    x = np.sort(r.dropna().to_numpy()); k = max(1, int(np.floor(a * len(x)))); return float(-x[:k].mean())


def boot_sharpe_diff(a: pd.Series, b: pd.Series, n: int = 2000, block: int = 20, seed: int = 0) -> float:
    """p unilateral de Sharpe(a) > Sharpe(b) con bootstrap estacionario por bloques (Politis-Romano) de los días emparejados,
    centrado en la diferencia observada (Ledoit-Wolf 2008)."""
    X = pd.concat([a, b], axis=1).dropna().to_numpy(); T = len(X); rng = np.random.default_rng(seed)
    f = lambda Y: (Y[:, 0].mean() / Y[:, 0].std(ddof=1) - Y[:, 1].mean() / Y[:, 1].std(ddof=1)) * np.sqrt(365)
    obs = f(X); d = np.empty(n)
    for k in range(n):
        idx = np.empty(T, int); t = 0
        while t < T:
            s = rng.integers(T); L = rng.geometric(1 / block); seg = (s + np.arange(L)) % T
            idx[t: t + L] = seg[: T - t]; t += L
        d[k] = f(X[idx])
    return float(((d - obs) >= obs).mean())


# ---------------------------------------------------------------- CPCV (para la Fase 2)
def cpcv_splits(T: int, n_groups: int = 6, k_test: int = 2, embargo: int = 5):
    """Combinatorial Purged Cross-Validation (López de Prado 2018, cap. 12): C(n_groups, k_test) particiones; en cada una los k grupos
    de prueba y un embargo de `embargo` observaciones tras cada grupo de prueba se quitan del entrenamiento. Devuelve (train, test) por partición."""
    g = np.array_split(np.arange(T), n_groups)
    for c in itertools.combinations(range(n_groups), k_test):
        test = np.concatenate([g[i] for i in c]); ban = set(test.tolist())
        for i in c:
            e = g[i][-1]; ban.update(range(e + 1, min(T, e + 1 + embargo)))
        train = np.array([t for t in range(T) if t not in ban])
        yield train, np.sort(test)
