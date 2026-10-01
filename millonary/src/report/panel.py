"""Panel web (HTML autocontenido): pestañas Sala, Ranking, Equipos e Informe, a partir de los ficheros de la cuenta de papel.

  python -m src.report.panel --data paper_state      -> <data>/panel.html
El JSON embebido sale de briefing.json, equity.csv, informe_prueba.json y reports/. Sin servidor, sin claves.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from ..desk.chat import feed
from .weekly import _csv, _json, summarize, markdown

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = Path(__file__).with_name("panel_template.html")


def payload(data: Path, now: pd.Timestamp | None = None) -> dict:
    data = Path(data); now = now or pd.Timestamp.now(tz="UTC")
    brief = _json(data / "briefing.json"); s = summarize(data, now); eq = _csv(data / "equity.csv")
    pts = []
    if not eq.empty:
        t = pd.to_datetime(eq["bar"], utc=True); pts = [[int(a.timestamp() * 1000), float(b)] for a, b in zip(t, eq["equity"])]
    inc = next((d for d in (brief or {}).get("departamentos", []) if d["dept"] == "Incubadora de traders"), {}).get("metrics", {})
    idr = _json(data / "intradia" / "resumen.json"); itrades = (_json(data / "intradia" / "trades_detalle.json") or [])[:300]
    core = _csv(data / "diario_ordenes.csv"); core_rows = [] if core.empty else core.sort_values("bar", ascending=False).head(50).to_dict("records")
    chat = (feed(brief) if brief else [])
    ops = []
    for t in itrades:
        who = t["trader"].split(" ")[0]
        ops.append({"hora": str(t["abre"])[5:16].replace("T", " "), "de": t["trader"], "a": "Mesa", "canal": "Operaciones", "ts": str(t["abre"]),
                    "texto": f"Abrió {t['lado']} a {t['px_entrada']:,.0f} · SL {t['sl']:,.0f} · TP {('%.0f' % t['tp']) if t['tp'] else 'sin TP'} · lote {t['lote_btc']} BTC ({t['nocional_usdt']:,.0f} USDT, riesgo {t['riesgo_usdt']:.2f} USDT)"})
        if not t["abierta"]:
            ops.append({"hora": str(t["cierra"])[5:16].replace("T", " "), "de": t["trader"], "a": "Mesa", "canal": "Operaciones", "ts": str(t["cierra"]),
                        "texto": f"Cerró por {t['salida']} a {t['px_salida']:,.0f}: {t['R']:+.2f} R ({t['pnl_usdt']:+.2f} USDT). " + " ".join(t["lecciones"][:2])})
    ops.sort(key=lambda m: m["ts"], reverse=True)
    m15 = _json(data / "mesa15" / "resumen.json"); m15t = (_json(data / "mesa15" / "trades_detalle.json") or [])[:300]; m15l = _json(data / "mesa15" / "aprendices.json")
    return {"m15": m15, "m15_trades": m15t, "m15_aprende": m15l, "intradia": idr, "intradia_trades": itrades, "aprendizaje": _json(data / "intradia" / "aprendizaje.json"), "nucleo_ordenes": core_rows, "chat_ops": ops, "generado": now.isoformat(), "summary": s, "brief": brief, "chat": chat, "equity": pts, "forward": inc.get("forward", {}),
            "hist": _json(ROOT / "reports" / "incubadora_resultados.json"), "mejoras": _json(ROOT / "reports" / "mejoras_registro.json"), "weekly_md": markdown(s)}


def fragment(data: Path, now: pd.Timestamp | None = None) -> str:
    """Página sin <html>/<head>/<body> (formato de artefacto publicable)."""
    js = json.dumps(payload(data, now), default=str, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("__DATA__", js)


def build_panel(data: Path, now: pd.Timestamp | None = None) -> Path:
    html = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
            + fragment(data, now) + "</body></html>")
    out = Path(data) / "panel.html"; out.write_text(html, encoding="utf-8"); return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="paper_state"); ap.add_argument("--fragment", default=None, help="además escribe la página sin <html>/<head>/<body> (para republicarla como artefacto)")
    a = ap.parse_args()
    print(build_panel(Path(a.data)))
    if a.fragment:
        Path(a.fragment).write_text(fragment(Path(a.data)), encoding="utf-8"); print(a.fragment)
