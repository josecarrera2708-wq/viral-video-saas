"""Procesado ORDENADO de todas las velas pendientes (compartido por el bucle en vivo y la puesta al día).

Garantiza que ninguna vela se salta tras una caída, un arranque tardío o un dato atrasado: cada vela
cerrada posterior a la última procesada pasa por trader.step en orden cronológico.
"""
from __future__ import annotations
import pandas as pd
from .config import LiveConfig
from .store import Store
from .trader import PaperTrader, INTERVAL


def pending_indices(trader: PaperTrader, bars: pd.DataFrame, now: pd.Timestamp, start: pd.Timestamp | None = None):
    last = trader.st.get("last_bar"); last = pd.Timestamp(last) if last else None
    sel = []
    for i, t_open in enumerate(bars.index):
        t_close = t_open + INTERVAL
        if t_close > now:
            break
        if last is not None and t_open <= last:
            continue
        if start is not None and t_close <= start:
            continue
        sel.append(i)
    if last is None and start is None:
        sel = sel[-1:]                       # cuenta nueva sin fecha de inicio: solo la última vela cerrada
    return sel


def process_pending(trader: PaperTrader, bars: pd.DataFrame, funding: pd.DataFrame, now: pd.Timestamp,
                    start: pd.Timestamp | None = None, delayed_feed: bool = False) -> list:
    """delayed_feed=True (Binance Vision, ≤ 1 día de retraso por diseño): la frescura se mide respecto a
    cada vela y no al reloj. En vivo (False) la última vela se valida contra la hora real."""
    out = []
    for i in pending_indices(trader, bars, now, start):
        t_close = bars.index[i] + INTERVAL
        step_now = now if (i == len(bars) - 1 and not delayed_feed) else t_close + pd.Timedelta(seconds=60)
        res = trader.step(bars.iloc[: i + 1], funding, step_now)
        out.append(res)
        if res["status"] not in ("ok", "ya_procesada"):
            break                                # datos no fiables: se para aquí y se reintenta más tarde
    return out


def is_up_to_date(trader: PaperTrader, now: pd.Timestamp) -> bool:
    last = trader.st.get("last_bar")
    return bool(last) and pd.Timestamp(last) >= now.floor(INTERVAL) - INTERVAL


def replay(cfg: LiveConfig, bars: pd.DataFrame, funding: pd.DataFrame, start: str, end: str, trader: PaperTrader | None = None):
    """Reproduce el histórico [start, end] llamando al MISMO trader.step que en vivo."""
    trader = trader or PaperTrader(cfg, Store(":memory:"))
    for i in range(len(bars)):
        t = bars.index[i]
        if t < pd.Timestamp(start, tz="UTC") or t > pd.Timestamp(end, tz="UTC"):
            continue
        trader.step(bars.iloc[: i + 1], funding, t + INTERVAL + pd.Timedelta(seconds=60))
    return trader
