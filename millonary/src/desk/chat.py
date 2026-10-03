"""Chat de agentes: mensajes 'emisor → receptor' generados SOLO a partir de los informes reales del comité (sin inventar cifras).

  python -m src.desk.chat feed  [--data paper_state] [--filter Riesgos]
  python -m src.desk.chat ask   <departamento> "pregunta"
`ask` responde con las cifras del último informe del departamento (búsqueda por palabras clave); no hay LLM ni decisiones.
"""
from __future__ import annotations
import argparse, json, unicodedata
from pathlib import Path

CANALES = {"Riesgos": "Riesgos", "Macroeconomía": "Macro", "Análisis de mercados": "Análisis", "Gestión de cartera": "Operaciones",
           "Mesa de trading": "Operaciones", "Derivados y arbitraje": "Análisis", "Laboratorio (cuantitativo / ML)": "Análisis",
           "Escuela": "Charla", "Infraestructura": "Charla", "Incubadora de traders": "Análisis", "Mesa de opciones": "Análisis"}


def _norm(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def feed(session: dict, filtro: str | None = None) -> list:
    """Convierte el JSON de la sesión en mensajes cronológicos. El comité (Dirección) abre y cierra."""
    ts = session["ts"][11:16]; msgs = [{"hora": ts, "de": "Dirección", "a": "Todos", "canal": "Comité", "texto": session["decision"]}]
    for d in session["departamentos"]:
        canal = CANALES.get(d["dept"], "Análisis")
        msgs.append({"hora": ts, "de": d["dept"], "a": "Dirección", "canal": canal, "texto": d["headline"]})
        for n in d["notes"][:3]:
            if n.strip(): msgs.append({"hora": ts, "de": d["dept"], "a": "Dirección", "canal": canal, "texto": n.strip()})
        for s in d.get("shadow", [])[:2]:
            msgs.append({"hora": ts, "de": d["dept"], "a": "Laboratorio", "canal": "Análisis", "texto": f"(sombra) {s}"})
    if session["veto"]:
        msgs.insert(1, {"hora": ts, "de": "Riesgos", "a": "Todos", "canal": "Riesgos", "texto": "VETO activo: exposición 0×."})
    msgs.append({"hora": ts, "de": "Dirección", "a": "Todos", "canal": "Comité",
                 "texto": "Recordad: el núcleo validado manda; los agentes analizan y recomiendan. Solo Riesgos puede vetar."})
    return [m for m in msgs if not filtro or _norm(m["canal"]) == _norm(filtro) or _norm(m["de"]) == _norm(filtro)]


def ask(session: dict, dept: str, question: str) -> str:
    """Responde con las notas del departamento que comparten más palabras con la pregunta; si no hay, resume su titular."""
    d = next((x for x in session["departamentos"] if _norm(dept) in _norm(x["dept"])), None)
    if d is None:
        return f"No conozco el departamento «{dept}». Disponibles: " + ", ".join(x["dept"] for x in session["departamentos"])
    words = {w for w in _norm(question).replace("?", " ").split() if len(w) > 3}
    scored = sorted(d["notes"], key=lambda n: -len(words & set(_norm(n).split())))
    best = [n.strip() for n in scored[:2] if n.strip() and words & set(_norm(n).split())]
    return f"{d['dept']} ({d['status']}): {d['headline']}" + ("\n" + "\n".join(best) if best else "")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    f = sp.add_parser("feed"); f.add_argument("--data", default="paper_state"); f.add_argument("--filter", default=None)
    q = sp.add_parser("ask"); q.add_argument("dept"); q.add_argument("question"); q.add_argument("--data", default="paper_state")
    a = ap.parse_args(); s = json.loads((Path(a.data) / "briefing.json").read_text())
    if a.cmd == "feed":
        for m in feed(s, a.filter): print(f"{m['hora']} {m['de']} → {m['a']} [{m['canal']}]: {m['texto']}")
    else:
        print(ask(s, a.dept, a.question))
