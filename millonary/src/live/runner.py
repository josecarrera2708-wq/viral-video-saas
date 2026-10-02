"""Ejecutor: bucle en vivo (paper), pasada única y REPRODUCCIÓN histórica por el mismo camino de código.

Uso:
  python -m src.live.runner --loop          # 24/7: evalúa AL ARRANCAR y en cada cierre de vela de 4h
  python -m src.live.runner --once          # una evaluación ahora (procesa todas las velas pendientes)
  python -m src.live.runner --status        # resumen del estado
  python -m src.live.runner --reset-halt    # reanuda tras una parada (retira antes el archivo KILL)
Kill switch: crea <MILLONARY_DATA>/KILL  -> en el siguiente cierre se aplana todo y se para.
"""
from __future__ import annotations
import argparse, logging, os, sys, time
from pathlib import Path
import pandas as pd
import requests
from .config import LiveConfig
from .feed import BinanceFeed, BybitFeed, FeedRouter
from .pipeline import process_pending, is_up_to_date
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


def notify_once(trader: PaperTrader, key: str, msg: str):
    """Evita repetir el mismo aviso: una vez por clave y día UTC."""
    day = str(pd.Timestamp.now(tz="UTC").floor("D"))
    if trader.st.get("notified:" + key) != day:
        trader.st.set("notified:" + key, day); notify(msg)


def build(cfg: LiveConfig):
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    return PaperTrader(cfg, Store(cfg.data_dir / "state.db")), FeedRouter([BinanceFeed(cfg.symbol, cfg.interval), BybitFeed(cfg.symbol, cfg.interval)])


def run_once(trader: PaperTrader, feed, now: pd.Timestamp | None = None) -> list:
    now = now or pd.Timestamp.now(tz="UTC")
    bars = feed.bars(trader.cfg.history_bars + 50, now)
    since = min((pd.Timestamp(x) for x in (trader.st.get("last_funding_event"), trader.st.oldest_synthetic_funding()) if x),
                default=bars.index[-1] - pd.Timedelta(days=3))
    funding = feed.funding(since - pd.Timedelta(hours=1), now)
    results = process_pending(trader, bars, funding, now)
    for res in results:
        if res["status"] == "ok":
            if res.get("new_halt"):
                notify("SISTEMA PARADO: " + ",".join(f for f in res["flags"]) + f" | equity {res['equity']:.2f}")
            for f in res["flags"]:
                if f.startswith("AVISO"): notify_once(trader, f.split("_")[0] + f.split("_")[1] if "_" in f else f, f"{f} | equity {res['equity']:.2f}")
                if f == "OMITIDA_MIN_ORDEN": notify_once(trader, "min_orden", "Orden omitida por tamaño mínimo (cuenta pequeña)")
                if f.startswith("SALTO"): notify_once(trader, "salto", "Movimiento de precio muy grande en las últimas velas")
            if res["trade"]:
                t = res["trade"]; log.info("OPERACION %s %.4f BTC @ %.1f (%s)", t["side"], t["qty"], t["price"], t["reason"])
        elif res["status"] == "datos_no_fiables":
            notify_once(trader, "datos:" + res["bar"], "Datos no fiables, se mantiene la posición: " + "; ".join(res["problems"]))
    return results


def loop(cfg: LiveConfig):
    trader, feed = build(cfg)
    log.info("Millonary paper arrancado. Datos en %s | capital %.0f | última vela procesada: %s",
             cfg.data_dir, cfg.capital, trader.st.get("last_bar"))
    while True:
        ok = False
        for attempt in range(8):                                    # arranque inmediato + reintentos ~8 min
            try:
                res = run_once(trader, feed)
                log.info("procesadas %d velas | al día: %s", sum(r["status"] == "ok" for r in res),
                         is_up_to_date(trader, pd.Timestamp.now(tz="UTC")))
                if is_up_to_date(trader, pd.Timestamp.now(tz="UTC")):
                    ok = True; break
            except Exception as e:                                  # noqa: BLE001
                log.error("fallo en la evaluación (intento %d): %s", attempt + 1, e)
            time.sleep(60)
        if not ok:
            notify_once(trader, "sin_datos", "No se pudo dejar el sistema al día tras 8 intentos; sigo reintentando en el próximo ciclo")
        now = pd.Timestamp.now(tz="UTC")
        nxt = now.floor(INTERVAL) + INTERVAL + pd.Timedelta(seconds=cfg.close_delay_s)
        time.sleep(max(1, (nxt - now).total_seconds()))


def status(cfg: LiveConfig):
    tr, _ = build(cfg); st = tr.st
    eq = st.rows("equity")
    print("equity:", round(eq[-1]["equity"], 2) if eq else cfg.capital, "| unidades BTC:", st.get("units"),
          "| parado:", st.get("halted"), "| última vela:", st.get("last_bar"), "| operaciones:", len(st.rows("trades")),
          "| KILL presente:", tr.risk.kill_file.exists())


def reset_halt(cfg: LiveConfig):
    tr, _ = build(cfg); print(tr.reset_halt(pd.Timestamp.now(tz="UTC")))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--loop", action="store_true"); ap.add_argument("--once", action="store_true")
    ap.add_argument("--status", action="store_true"); ap.add_argument("--reset-halt", action="store_true")
    ap.add_argument("--capital", type=float, default=1000.0)
    a = ap.parse_args()
    cfg = LiveConfig(capital=a.capital)
    if a.status: status(cfg)
    elif a.reset_halt: reset_halt(cfg)
    elif a.once:
        tr, fd = build(cfg); print([{k: v for k, v in r.items() if k != "trade"} for r in run_once(tr, fd)])
    elif a.loop: loop(cfg)
    else: ap.print_help(); sys.exit(1)
