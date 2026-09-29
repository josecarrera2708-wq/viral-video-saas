"""Métricas de una simulación (todas netas de costes, calculadas sobre el capital marcado a mercado)."""
from __future__ import annotations
import numpy as np

BARS_PER_YEAR = {"1h": 24 * 365.25, "4h": 6 * 365.25}


def max_drawdown(eq: np.ndarray) -> float:
    peak = np.maximum.accumulate(eq)
    with np.errstate(divide="ignore", invalid="ignore"):
        dd = 1 - eq / peak
    return float(np.nanmax(dd)) if len(dd) else 0.0


def summarize(res: dict, tf: str = "1h") -> dict:
    eq = res["equity"]; cap = res["params"].capital; n = len(eq)
    r = np.diff(eq) / np.where(eq[:-1] > 0, eq[:-1], np.nan)
    r = np.nan_to_num(r)
    ann = BARS_PER_YEAR[tf]
    sd = r.std()
    sharpe = float(r.mean() / sd * np.sqrt(ann)) if sd > 0 else 0.0
    dn = r[r < 0]; dsd = np.sqrt((dn ** 2).mean()) if len(dn) else 0.0
    sortino = float(r.mean() / dsd * np.sqrt(ann)) if dsd > 0 else 0.0
    years = n / ann
    tot = eq[-1] / cap
    cagr = float(tot ** (1 / years) - 1) if tot > 0 and years > 0 else -1.0
    dd = max_drawdown(res["equity_low"])
    pnl = res["pnl"]; nt = len(pnl)
    gp = pnl[pnl > 0].sum(); gl = -pnl[pnl < 0].sum()
    pf = float(gp / gl) if gl > 0 else (float("inf") if gp > 0 else 0.0)
    return {"trades": int(nt), "ret": float(tot - 1), "cagr": cagr, "sharpe": sharpe,
            "sortino": sortino, "maxdd": dd, "calmar": float(cagr / dd) if dd > 0 else 0.0,
            "pf": pf, "win": float((pnl > 0).mean()) if nt else 0.0,
            "exp_r": float(res["r"].mean()) if nt else 0.0,
            "avg_hold": float((res["exit_idx"] - res["entry_idx"]).mean()) if nt else 0.0,
            "fees": float(res["fees"].sum()), "funding": float(res["funding"].sum()),
            "ruined": bool(res["ruined"]), "skipped": int(res["skipped_minlot"] + res["skipped_badstop"])}
