"""Puesta al día del paper trading SIN VPS: procesa, una a una y por el mismo trader.step que en vivo,
todas las velas cerradas nuevas disponibles en Binance Vision (retraso ≤ 1 día).

  python -m src.live.catchup --start 2026-09-29T16:00:00Z --data paper_state
Idempotente: se puede ejecutar cuantas veces se quiera. Exporta equity.csv, trades.csv y events.csv.
"""
from __future__ import annotations
import argparse, csv
from pathlib import Path
import pandas as pd
from .config import LiveConfig
from .pipeline import process_pending
from .store import Store
from .trader import PaperTrader


def export(store: Store, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    for table in ("equity", "trades", "events"):
        rows = store.rows(table)
        with open(out / f"{table}.csv", "w", newline="") as f:
            if rows:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def catchup(cfg: LiveConfig, feed, start: pd.Timestamp, now: pd.Timestamp | None = None,
            trader: PaperTrader | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    trader = trader or PaperTrader(cfg, Store(cfg.data_dir / "state.db"))
    bars = feed.bars(cfg.history_bars + 400, now)
    since = trader.st.get("last_funding_event")
    funding = feed.funding((pd.Timestamp(since) if since else bars.index[0]) - pd.Timedelta(hours=1), now)
    results = process_pending(trader, bars, funding, now, start=start, delayed_feed=True)
    bad = [r for r in results if r["status"] not in ("ok", "ya_procesada")]
    export(trader.st, cfg.data_dir)
    eq = trader.st.rows("equity")
    out = {"status": "ok" if not bad else "detenido", "velas_procesadas": sum(r["status"] == "ok" for r in results),
           "ultima_vela": trader.st.get("last_bar"), "equity": eq[-1]["equity"] if eq else cfg.capital,
           "unidades": trader.st.get("units"), "operaciones_total": len(trader.st.rows("trades")),
           "parado": trader.st.get("halted"), "funding_sintetico_en_el_mes_en_curso": True}
    if bad:
        out["detalle"] = bad[0]
    return out


if __name__ == "__main__":
    from .vision_feed import VisionFeed
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="cierre de vela desde el que se considera la cuenta (UTC)")
    ap.add_argument("--data", default="paper_state"); ap.add_argument("--capital", type=float, default=1000.0)
    a = ap.parse_args()
    cfg = LiveConfig(capital=a.capital, data_dir=Path(a.data), min_history_bars=1800)
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    print(catchup(cfg, VisionFeed(), pd.Timestamp(a.start)))
