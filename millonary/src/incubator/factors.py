"""Atribución por factores: r = alfa + beta_BTC * r_BTC + beta_tend * F_tend + e (errores HAC Newey-West)."""
from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st


def trend_factor(btc_daily_close: pd.Series) -> pd.Series:
    """F_tend(t) = signo del retorno a 60 d hasta t-1 × retorno de BTC en t (momentum de series temporales, causal)."""
    r = btc_daily_close.pct_change()
    sgn = np.sign(btc_daily_close.shift(1) / btc_daily_close.shift(61) - 1)
    return (sgn * r).rename("trend")


def regress(strat_daily: pd.Series, btc_daily: pd.Series, trend: pd.Series, lags: int = 5) -> dict:
    d = pd.concat([strat_daily.rename("y"), btc_daily.rename("btc"), trend], axis=1).dropna()
    if len(d) < 60 or d["y"].std() == 0:
        return {"n": len(d), "alpha_anual": float("nan"), "t_alpha": float("nan"), "p_alpha_1s": float("nan"),
                "beta_btc": float("nan"), "beta_tend": float("nan"), "r2": float("nan")}
    X = sm.add_constant(d[["btc", "trend"]])
    m = sm.OLS(d["y"], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    t = float(m.tvalues["const"])
    return {"n": int(len(d)), "alpha_anual": float(m.params["const"] * 365), "t_alpha": t,
            "p_alpha_1s": float(1 - st.t.cdf(t, df=max(len(d) - 3, 1))),
            "beta_btc": float(m.params["btc"]), "beta_tend": float(m.params["trend"]), "r2": float(m.rsquared)}


def holm(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float); n = len(p); order = np.argsort(p); adj = np.empty(n); run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (n - rank) * p[i]); adj[i] = min(1.0, run)
    return adj


def benjamini_hochberg(p: np.ndarray) -> np.ndarray:
    p = np.asarray(p, float); n = len(p); order = np.argsort(p)[::-1]; adj = np.empty(n); prev = 1.0
    for k, i in zip(range(n, 0, -1), order):
        prev = min(prev, p[i] * n / k); adj[i] = prev
    return adj
