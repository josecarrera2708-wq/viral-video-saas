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
    idr = _json(data / "intradia" / "resumen.json"); itr = _csv(data / "intradia" / "trades.csv"); itrades = []
    if not itr.empty:
        itrades = itr[~itr["abierta"].astype(bool)].sort_values("cierra", ascending=False).head(30).to_dict("records")
    return {"intradia": idr, "intradia_trades": itrades, "generado": now.isoformat(), "summary": s, "brief": brief, "chat": feed(brief) if brief else [], "equity": pts, "forward": inc.get("forward", {}),
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
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="paper_state"); a = ap.parse_args()
    print(build_panel(Path(a.data)))
