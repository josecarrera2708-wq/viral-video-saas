"""Incubadora hacia delante: los 15 traders operan en SOMBRA desde el inicio de la prueba (arrancan planos)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..backtest.funding import align_funding
from .setups import all_states
from .sim import simulate, trades, daily

H4 = pd.Timedelta("4h")


def forward_run(bars: pd.DataFrame, funding_events: pd.DataFrame | None, start: pd.Timestamp | None) -> dict:
    """Devuelve por trader: retorno, caída, nº de operaciones y P&L hacia delante desde `start` (plano al inicio)."""
    if start is None or len(bars) < 300:
        return {}
    S = all_states(bars)
    f = align_funding(bars.index, H4, funding_events) if funding_events is not None and len(funding_events) else np.zeros(len(bars))
    closes = bars.index + H4
    live = np.asarray(closes >= pd.Timestamp(start))                 # el estado solo cuenta desde el primer cierre de la prueba
    out = {}
    for k in S:
        st = np.where(live, S[k].to_numpy(), 0.0)
        r = simulate(bars, st, f); ret = r["ret"][np.asarray(closes > pd.Timestamp(start))]
        eq = (1 + ret).cumprod() if len(ret) else pd.Series([1.0])
        d = daily(ret) if len(ret) else pd.Series(dtype=float)
        tr = trades(r); tr = tr[tr["open"] + H4 >= pd.Timestamp(start)] if len(tr) else tr
        sh = float(d.mean() / d.std(ddof=1) * np.sqrt(365)) if len(d) >= 10 and d.std(ddof=1) > 0 else None
        out[k] = {"retorno": float(eq.iloc[-1] - 1), "caida_max": float((1 - eq / eq.cummax()).max()), "ops": int(len(tr)),
                  "dias": int(len(d)), "sharpe": sh, "posicion_actual": float(S[k].iloc[-1])}
    return out
