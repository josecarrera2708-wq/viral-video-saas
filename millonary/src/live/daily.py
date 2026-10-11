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
    # funding desde el inicio de la prueba (o 400 días): lo usan el cobro, la corrección de tasas sintéticas y las réplicas de G1
    funding = feed.funding(min(start, now - pd.Timedelta(days=400)) - pd.Timedelta(days=2), now)
    res = process_pending(trader, bars, funding, now, start=start, delayed_feed=True)
    bad = [r for r in res if r["status"] not in ("ok", "ya_procesada")]
    export(store, d)
    out = {"velas_nuevas": sum(r["status"] == "ok" for r in res), "ultima_vela": store.get("last_bar"), "problemas": bad[:1]}
    fund_year = funding[funding["time"] > now - pd.Timedelta(days=400)].reset_index(drop=True)
    ctx = build_context(cfg, store, now, start, bars=bars, funding=fund_year)
    s = sesion(ctx); md = markdown(s); txt = narrate(s)
    if txt: md = md.replace("**Principio:**", f"**Resumen de la Directora (IA):** {txt}\n\n**Principio:**", 1)
    (d / "briefing.md").write_text(md); (d / "briefing.json").write_text(json.dumps(s, indent=1, default=str))
    export_journal(ctx.journal, d)
    if store.rows("equity"):
        rep = forward_report(cfg, store, bars, funding.copy(), start.floor(INTERVAL) - INTERVAL, load_bands())   # vela anterior a la primera procesada (el inicio puede no caer en la rejilla de 4 h)
        (d / "informe_prueba.md").write_text(informe_texto(rep)); (d / "informe_prueba.json").write_text(json.dumps(rep, indent=1, default=str))
        out["puertas"] = rep.get("puertas"); out["equity"] = store.rows("equity")[-1]["equity"]
    out["estado_comite"] = s["estado"]
    # carry de funding junto al núcleo (subcuenta propia): nunca debe tumbar la rutina de la cuenta oficial
    try:
        from src.live.carry import main as carry_main
        c = carry_main(now, funding); out["carry"] = {k: c.get(k) for k in ("equity", "dentro", "velas_nuevas", "problemas", "cartera")}
    except Exception as e:                                           # noqa: BLE001
        out["carry_error"] = f"{type(e).__name__}: {e}"
    # perfeccionamiento continuo, informe semanal y panel: nunca deben tumbar la rutina de la cuenta
    try:
        from src.lab.mejora import update as mejora_update
        led = mejora_update(bars, fund_year, start, now); out["mejoras_en_sombra"] = len(led.get("en_sombra", []))
        out["adoptables"] = [k for k, v in led["candidatas"].items() if v["etapa"].startswith("E4")]
    except Exception as e:                                           # noqa: BLE001
        out["mejoras_error"] = f"{type(e).__name__}: {e}"
    try:
        from src.report.weekly import write_all
        from src.report.panel import build_panel
        write_all(d, now); build_panel(d, now); out["panel"] = str(d / "panel.html")
    except Exception as e:                                           # noqa: BLE001
        out["panel_error"] = f"{type(e).__name__}: {e}"
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1, default=str))
