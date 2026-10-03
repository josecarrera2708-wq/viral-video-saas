"""Dirección: reúne el comité de departamentos y redacta el informe de la sesión.

La decisión operativa NO la toman los agentes: es el objetivo de exposición del núcleo validado, filtrado por la
capa de riesgo determinista. Los departamentos aportan análisis, avisos y recomendaciones en modo sombra.
"""
from __future__ import annotations
import json, os
import requests
import pandas as pd
from .base import Context, Report, OK, AVISO, ALERTA
from .departments import riesgos, macro, analisis, cartera, mesa, derivados, infra
from .lab import laboratorio
from .school import escuela
from .incubadora import incubadora
from .opciones import opciones
from .intradia import mesa_intradia

DEPTS = [("Riesgos", riesgos), ("Macroeconomía", macro), ("Análisis de mercados", analisis), ("Gestión de cartera", cartera),
         ("Mesa de trading", mesa), ("Derivados y arbitraje", derivados), ("Laboratorio (cuantitativo / ML)", laboratorio),
         ("Incubadora de traders", incubadora), ("Mesa de opciones", opciones), ("Mesa intradía", mesa_intradia),
         ("Escuela", escuela), ("Infraestructura", infra)]

ROSTER = [  # el organigrama de Conesa, con el estado REAL de cada departamento
    ("Dirección (comité)", "ACTIVO", "Reúne los informes y redacta la sesión. No decide la operativa."),
    ("Riesgos", "ACTIVO · con VETO", "Capa determinista: exposición máx., pérdida diaria, caída máx., kill switch, datos no fiables."),
    ("Macroeconomía", "ACTIVO (informa)", "Fear&Greed, VIX, curva, dólar, funding y calendario FOMC. CPI/empleo: falta fuente (BLS bloquea el acceso automático)."),
    ("Vigilancia de noticias (Fed, Trump, cuentas clave)", "PENDIENTE", "Requiere un proceso 24/7 y fuentes: los RSS de la Fed son accesibles; X/Truth Social exigen API de pago. Entrará en modo sombra."),
    ("Análisis de mercados", "ACTIVO (informa)", "Tendencia por horizonte, estructura, volatilidad, patrones de velas (sin ventaja probada)."),
    ("Mesa de trading", "ACTIVO en papel", "Ejecución simulada con costes, diario de lotes y posiciones. Dinero real: solo tras el protocolo."),
    ("Gestión de cartera", "ACTIVO", "Volatility targeting, banda de rebalanceo, coste de funding."),
    ("Derivados y arbitraje", "INVESTIGACIÓN", "Carry teórico cash-and-carry. No se opera."),
    ("Coberturas", "NO APLICA por ahora", "El sistema se 'cubre' saliendo a efectivo; las estrategias con cortos no mejoraron fuera de muestra."),
    ("Mesa intradía (papel)", "ACTIVO en papel", "14 traders con stop/TP/tiempo sobre velas de 1 h (Deribit), 1.000 USDT virtuales cada uno; actualización horaria. Histórico: 0/14 certificadas."),
    ("Opciones", "ACTIVO (solo informa)", "Deribit público: IV vs RV, sesgo 25Δ y coste de un put 10 % OTM. No se opera con opciones; protección de cola desactivada (sin histórico)."),
    ("Incubadora de traders / Estrategias minadas", "ACTIVO en sombra", "15 traders-estrategia con atribución alfa/beta, corrección por comparaciones múltiples y examen sellado; capital simulado solo por mérito. 0/15 certificadas en el examen."),
    ("Cuantitativo / Machine learning", "ACTIVO en sombra (Laboratorio)", "Minero + embudo de robustez; 7 variantes hacia delante. Sin ventaja probada del ranking del minero."),
    ("Escuela / Academia", "ACTIVO", "Post-mortem de cada lote y marcador por contexto; no cambia parámetros."),
    ("Laboratorio de mejoras", "ACTIVO en sombra", "Regla de promoción: ≥ 90 días, Sharpe ≥ núcleo+0,3, caída ≤ 1,2×, embudo superado."),
    ("Infraestructura", "ACTIVO", "Frescura de datos, integridad de la base de datos, incidencias, disco."),
    ("Bienestar del equipo (salud del sistema)", "ACTIVO", "Se traduce en salud operativa (Infraestructura) y en la calidad medida de cada agente (Laboratorio y Escuela)."),
]


def sesion(ctx: Context) -> dict:
    reports = []
    for name, fn in DEPTS:
        try:
            reports.append(fn(ctx))
        except Exception as e:                                       # noqa: BLE001
            reports.append(Report(name, "FALLO DEL DEPARTAMENTO", ALERTA, notes=[f"{type(e).__name__}: {e}"]))
    by = {r.dept: r for r in reports}
    rk = by.get("Riesgos"); cp = by.get("Gestión de cartera")
    objetivo = cp.metrics.get("objetivo") if cp and cp.metrics else None
    veto = bool(rk and rk.veto)
    final = 0.0 if veto else objetivo
    alerts = [r.dept for r in reports if r.status == ALERTA]; warns = [r.dept for r in reports if r.status == AVISO]
    shadow = [(r.dept, s) for r in reports for s in r.shadow]
    dec = (f"VETO de Riesgos: exposición 0× (sistema parado)." if veto else
           (f"Mantener el objetivo del núcleo: {final:.2f}× de exposición." if final is not None else "Sin objetivo calculado."))
    return {"ts": str(ctx.now), "decision": dec, "objetivo_nucleo": objetivo, "objetivo_final": final, "veto": veto,
            "estado": ALERTA if alerts else AVISO if warns else OK, "alertas": alerts, "avisos": warns,
            "recomendaciones_en_sombra": shadow, "departamentos": [r.as_dict() for r in reports], "organigrama": ROSTER}


def markdown(s: dict) -> str:
    icon = {OK: "🟢", AVISO: "🟡", ALERTA: "🔴"}
    L = [f"# Sesión del comité · {s['ts'][:16]} UTC", "", f"**Estado general:** {icon[s['estado']]} {s['estado']}", f"**Decisión:** {s['decision']}",
         "**Principio:** los agentes analizan y recomiendan; la operativa la fija el núcleo validado y solo Riesgos puede vetar.", ""]
    if s["alertas"]: L.append("**Alertas:** " + ", ".join(s["alertas"]))
    if s["avisos"]: L.append("**Avisos:** " + ", ".join(s["avisos"]))
    L.append("")
    for d in s["departamentos"]:
        L += [f"## {icon[d['status']]} {d['dept']} — {d['headline']}"] + [f"- {n}" if n and not n.startswith("  ") else f"  {n.strip()}" if n else "" for n in d["notes"]] + [""]
    L += ["## Organigrama (estado real frente a la idea original)", "", "| Departamento | Estado | Qué hace realmente |", "|---|---|---|"]
    for n, e, w in s["organigrama"]: L.append(f"| {n} | {e} | {w} |")
    return "\n".join(L)


def narrate(s: dict, api_key: str | None = None, model: str | None = None) -> str | None:
    """Capa OPCIONAL de redacción con un LLM (Claude). Solo redacta con las cifras del JSON; no decide nada."""
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = model or os.environ.get("MILLONARY_LLM_MODEL", "claude-sonnet-5-5")
    slim = {k: s[k] for k in ("ts", "decision", "estado", "alertas", "avisos", "recomendaciones_en_sombra")}
    slim["departamentos"] = [{"dept": d["dept"], "headline": d["headline"], "status": d["status"], "notes": d["notes"][:6]} for d in s["departamentos"]]
    system = ("Eres la Directora del fondo Millonary. Redacta el informe diario en español claro, máximo 180 palabras, "
              "usando SOLO las cifras del JSON. No recomiendes operar ni cambiar límites; destaca riesgos, vetos y avisos. "
              "Recuerda que un mes de datos no demuestra rentabilidad.")
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=60,
                          headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                          json={"model": model, "max_tokens": 500, "system": system,
                                "messages": [{"role": "user", "content": json.dumps(slim, ensure_ascii=False, default=str)}]})
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    except Exception:                                                # noqa: BLE001
        return None
