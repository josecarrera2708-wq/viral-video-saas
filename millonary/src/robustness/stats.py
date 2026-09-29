"""Estadística de selección: Deflated Sharpe Ratio, PBO (CSCV), Monte Carlo de operaciones."""
from __future__ import annotations
import itertools
import numpy as np
from scipy import stats as st

EULER = 0.5772156649015329


def expected_max_sr(n_trials: int, var_sr: float) -> float:
    """SR esperado del MEJOR de n_trials estrategias sin habilidad (Bailey & López de Prado 2014)."""
    if n_trials <= 1:
        return 0.0
    sd = np.sqrt(max(var_sr, 1e-12))
    return float(sd * ((1 - EULER) * st.norm.ppf(1 - 1 / n_trials) +
                       EULER * st.norm.ppf(1 - 1 / (n_trials * np.e))))


def sharpe_pp(r: np.ndarray) -> float:
    """Sharpe por periodo (no anualizado)."""
    sd = r.std(ddof=1)
    return float(r.mean() / sd) if sd > 0 else 0.0


def deflated_sharpe(r: np.ndarray, n_trials: int, var_sr: float) -> float:
    """Probabilidad de que el SR verdadero sea > 0 tras corregir por n_trials pruebas y por
    asimetría/curtosis. r: retornos por periodo (p. ej. diarios) de la estrategia elegida."""
    T = len(r)
    if T < 30:
        return 0.0
    sr = sharpe_pp(r); sk = st.skew(r); ku = st.kurtosis(r, fisher=False)
    sr0 = expected_max_sr(n_trials, var_sr)
    den = np.sqrt(max(1e-12, 1 - sk * sr + (ku - 1) / 4 * sr ** 2))
    return float(st.norm.cdf((sr - sr0) * np.sqrt(T - 1) / den))


def pbo_cscv(R: np.ndarray, s: int = 16, max_comb: int = 3000, seed: int = 0) -> float:
    """Probabilidad de sobreajuste (CSCV). R: matriz (T x N) de retornos de N candidatas.
    Para cada partición IS/OOS de los bloques: la mejor en IS, ¿queda bajo la mediana en OOS?"""
    T, N = R.shape
    if N < 4:
        return float("nan")
    T = (T // s) * s
    blocks = np.array_split(R[:T], s)
    combos = list(itertools.combinations(range(s), s // 2))
    rng = np.random.default_rng(seed)
    if len(combos) > max_comb:
        combos = [combos[i] for i in rng.choice(len(combos), max_comb, replace=False)]
    below = 0
    for c in combos:
        ins = np.vstack([blocks[i] for i in c]); oos = np.vstack([blocks[i] for i in range(s) if i not in c])
        def sr(x):
            sd = x.std(axis=0, ddof=1); sd = np.where(sd > 0, sd, np.inf); return x.mean(axis=0) / sd
        best = int(np.argmax(sr(ins)))
        rank = (sr(oos) < sr(oos)[best]).mean()        # rango relativo de la mejor IS en OOS
        below += rank < 0.5
    return below / len(combos)


def monte_carlo(trade_ret: np.ndarray, n_sims: int = 5000, seed: int = 0, skip: float = 0.0):
    """Remuestreo (bootstrap) de retornos por operación. Devuelve (p5 del retorno final, p95 del
    drawdown máximo, prob. de perder)."""
    rng = np.random.default_rng(seed)
    n = len(trade_ret)
    idx = rng.integers(0, n, size=(n_sims, n))
    x = trade_ret[idx]
    if skip > 0:
        x = np.where(rng.random(x.shape) < skip, 0.0, x)
    eq = np.cumprod(1 + x, axis=1)
    final = eq[:, -1] - 1
    peak = np.maximum.accumulate(np.concatenate([np.ones((n_sims, 1)), eq], axis=1), axis=1)[:, 1:]
    dd = (1 - eq / peak).max(axis=1)
    return float(np.percentile(final, 5)), float(np.percentile(dd, 95)), float((final < 0).mean())
