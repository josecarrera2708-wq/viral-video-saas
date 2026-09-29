"""Sesión diaria del comité con datos REALES.

  python -m src.desk.briefing --data paper_state --start 2026-09-29T20:00:00Z
Reúne velas (Binance Vision), macro (alternative.me + FRED), calendario FOMC (Fed) y la cuenta de papel, convoca a los
departamentos y escribe briefing.md / briefing.json / diario_*.csv en la carpeta de datos.
"""
from __future__ import annotations
import argparse, io, json
from pathlib import Path
import pandas as pd
import requests
from ..live.config import LiveConfig
from ..live.journal import build_journal, export_journal
from ..live.store import Store
from ..live.vision_feed import VisionFeed
from .base import Context
from .committee import sesion, markdown, narrate
from .events import load_events, FOMC_URL


def fetch_macro() -> dict:
    out = {}
    try:
        j = requests.get("https://api.alternative.me/fng/?limit=0&format=json", timeout=30).json()["data"]
        d = pd.DataFrame(j); d["t"] = pd.to_datetime(pd.to_numeric(d["timestamp"]), unit="s", utc=True).dt.floor("D")
        out["fng"] = pd.Series(pd.to_numeric(d["value"]).to_numpy(), index=d["t"]).sort_index()
    except Exception:                                                # noqa: BLE001
        pass
    for name, col in (("vix", "VIXCLS"), ("y10", "DGS10"), ("y2", "DGS2"), ("usd", "DTWEXBGS")):
        try:
            t = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={col}", timeout=30).text
            d = pd.read_csv(io.StringIO(t), na_values="."); d.columns = ["date", "v"]
            out[name] = pd.Series(pd.to_numeric(d["v"]).to_numpy(), index=pd.to_datetime(d["date"], utc=True)).dropna()
        except Exception:                                            # noqa: BLE001
            pass
    return out


def build_context(cfg: LiveConfig, store: Store, now: pd.Timestamp, lab_start: pd.Timestamp | None, bars=None, funding=None,
                  macro=None, events=None, source="Binance Vision") -> Context:
    feed = VisionFeed()
    bars = bars if bars is not None else feed.bars(cfg.history_bars + 50, now)
    funding = funding if funding is not None else feed.funding(now - pd.Timedelta(days=400), now)
    if macro is None: macro = fetch_macro()
    if events is None:
        try: events = load_events(requests.get(FOMC_URL, timeout=30).text)
        except Exception: events = load_events(None)                 # noqa: BLE001
    return Context(now=now, bars=bars, cfg=cfg, store=store, journal=build_journal(store, cfg.capital), funding_events=funding,
                   macro=macro, events=events, feed_source=source, lab_start=lab_start)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="paper_state"); ap.add_argument("--start", default=None)
    ap.add_argument("--capital", type=float, default=1000.0)
    a = ap.parse_args()
    d = Path(a.data); d.mkdir(parents=True, exist_ok=True)
    cfg = LiveConfig(capital=a.capital, data_dir=d); st = Store(d / "state.db")
    now = pd.Timestamp.now(tz="UTC"); start = pd.Timestamp(a.start) if a.start else None
    ctx = build_context(cfg, st, now, start)
    s = sesion(ctx); md = markdown(s); txt = narrate(s)
    if txt: md = md.replace("**Principio:**", f"**Resumen de la Directora (IA):** {txt}\n\n**Principio:**", 1)
    (d / "briefing.md").write_text(md); (d / "briefing.json").write_text(json.dumps(s, indent=1, default=str))
    export_journal(ctx.journal, d)
    print(md)
