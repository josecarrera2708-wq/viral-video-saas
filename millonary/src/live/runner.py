"""Ejecutor: bucle en vivo (paper), pasada única y REPRODUCCIÓN histórica por el mismo camino de código.

Uso:
  python -m src.live.runner --loop                 # bucle 24/7 (cada cierre de vela de 4h)
  python -m src.live.runner --once                 # una evaluación ahora
  python -m src.live.runner --status               # resumen del estado
  python -m src.live.runner --replay 2023-01-01 2025-06-30   # reproduce el histórico por el trader real
Kill switch: crea el fichero  <MILLONARY_DATA>/KILL  y en el siguiente cierre se aplana todo y se para.
"""
from __future__ import annotations
import argparse, logging, os, sys, time
from pathlib import Path
import pandas as pd
import requests
from .config import LiveConfig
from .feed import BinanceFeed, BybitFeed, FeedRouter
from .store import Store
from .trader import PaperTrader, INTERVAL

log = logging.getLogger("millonary")


def notify(msg: str):
    """Aviso por Telegram si hay TELEGRAM_TOKEN y TELEGRAM_CHAT; si no, solo log."""
    log.warning(msg)
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT")
    if tok and chat:
        try:
            requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", data={"chat_id": chat, "text": f"Millonary: {msg}"}, timeout=10)
        except requests.RequestException:
            pass


def build(cfg: LiveConfig):
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    return PaperTrader(cfg, Store(cfg.data_dir / "state.db")), FeedRouter([BinanceFeed(cfg.symbol, cfg.interval), BybitFeed(cfg.symbol, cfg.interval)])


def run_once(trader: PaperTrader, feed, now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    bars = feed.bars(trader.cfg.history_bars, now)
    funding = feed.funding(bars.index[-1] - pd.Timedelta(days=3), now)
    res = trader.step(bars, funding, now)
    if res["status"] == "ok":
        for f in res["flags"]:
            if f.startswith(("AVISO", "DD_HALT", "PERDIDA", "KILL", "HALT")):
                notify(f"{f} | equity {res['equity']:.2f}")
        if res["trade"]:
            t = res["trade"]; log.info("OPERACION %s %.4f BTC @ %.1f (%s)", t["side"], t["qty"], t["price"], t["reason"])
    elif res["status"] == "datos_no_fiables":
        notify("Datos no fiables, se mantiene la posición: " + "; ".join(res["problems"]))
    return res


def loop(cfg: LiveConfig):
    trader, feed = build(cfg)
    while True:
        now = pd.Timestamp.now(tz="UTC")
        nxt = now.floor(INTERVAL) + INTERVAL + pd.Timedelta(seconds=cfg.close_delay_s)
        time.sleep(max(1, (nxt - now).total_seconds()))
        for attempt in range(6):                                  # reintentos hasta ~6 min
            try:
                res = run_once(trader, feed)
                log.info("%s", {k: v for k, v in res.items() if k != "trade"})
                if res["status"] in ("ok", "ya_procesada"): break
            except Exception as e:                                # noqa: BLE001
                log.error("fallo en la evaluación: %s", e)
                if attempt == 5: notify(f"No se pudo evaluar la vela tras 6 intentos: {e}")
            time.sleep(60)


def replay(cfg: LiveConfig, bars: pd.DataFrame, funding: pd.DataFrame, start: str, end: str, trader: PaperTrader | None = None):
    """Reproduce el histórico [start, end] llamando al MISMO trader.step que en vivo."""
    trader = trader or PaperTrader(cfg, Store(":memory:"))
    idx = bars.index
    for i in range(len(bars)):
        t = idx[i]
        if t < pd.Timestamp(start, tz="UTC") or t > pd.Timestamp(end, tz="UTC"):
            continue
        trader.step(bars.iloc[: i + 1], funding, t + INTERVAL + pd.Timedelta(seconds=60))
    return trader


def status(cfg: LiveConfig):
    tr, _ = build(cfg); st = tr.st
    eq = st.rows("equity")
    print("equity:", eq[-1]["equity"] if eq else cfg.capital, "| unidades:", st.get("units"), "| parado:", st.get("halted"),
          "| última vela:", st.get("last_bar"), "| operaciones:", len(st.rows("trades")))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true"); ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true"); ap.add_argument("--capital", type=float, default=1000.0)
    a = ap.parse_args()
    cfg = LiveConfig(capital=a.capital)
    if a.status: status(cfg)
    elif a.once:
        tr, fd = build(cfg); print(run_once(tr, fd))
    elif a.loop: loop(cfg)
    else: ap.print_help(); sys.exit(1)
