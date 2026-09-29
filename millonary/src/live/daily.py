"""Proceso diario de la prueba en papel OFICIAL (sin VPS): actualiza la cuenta con Binance Vision, convoca al comité
y genera el informe matemático. Idempotente. Uso:  python -m src.live.daily"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.desk.briefing import build_context
from src.desk.committee import sesion, markdown, narrate
from src.live.catchup import export
from src.live.config import LiveConfig
from src.live.forward_eval import forward_report, informe_texto, load_bands
from src.live.journal import build_journal, export_journal
from src.live.pipeline import process_pending
from src.live.store import Store
from src.live.trader import PaperTrader, INTERVAL
from src.live.vision_feed import VisionFeed


def main(now: pd.Timestamp | None = None) -> dict:
    cfgj = json.loads((ROOT / "config" / "paper_start.json").read_text())
    start = pd.Timestamp(cfgj["start"]); d = ROOT / cfgj["data_dir"]; d.mkdir(parents=True, exist_ok=True)
    cfg = LiveConfig(capital=cfgj["capital"], data_dir=d)
    now = now or pd.Timestamp.now(tz="UTC")
    feed = VisionFeed(); bars = feed.bars(cfg.history_bars + 400, now)
    since = None
    store = Store(d / "state.db"); trader = PaperTrader(cfg, store)
    lf = store.get("last_funding_event")
    funding = feed.funding((pd.Timestamp(lf) if lf else start) - pd.Timedelta(days=2), now)
    res = process_pending(trader, bars, funding, now, start=start, delayed_feed=True)
    bad = [r for r in res if r["status"] not in ("ok", "ya_procesada")]
    export(store, d)
    out = {"velas_nuevas": sum(r["status"] == "ok" for r in res), "ultima_vela": store.get("last_bar"), "problemas": bad[:1]}
    fund_year = feed.funding(now - pd.Timedelta(days=400), now)
    ctx = build_context(cfg, store, now, start, bars=bars, funding=fund_year)
    s = sesion(ctx); md = markdown(s); txt = narrate(s)
    if txt: md = md.replace("**Principio:**", f"**Resumen de la Directora (IA):** {txt}\n\n**Principio:**", 1)
    (d / "briefing.md").write_text(md); (d / "briefing.json").write_text(json.dumps(s, indent=1, default=str))
    export_journal(ctx.journal, d)
    if store.rows("equity"):
        rep = forward_report(cfg, store, bars, funding.copy() if len(funding) else fund_year, start - INTERVAL, load_bands())
        (d / "informe_prueba.md").write_text(informe_texto(rep)); (d / "informe_prueba.json").write_text(json.dumps(rep, indent=1, default=str))
        out["puertas"] = rep.get("puertas"); out["equity"] = store.rows("equity")[-1]["equity"]
    out["estado_comite"] = s["estado"]
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
