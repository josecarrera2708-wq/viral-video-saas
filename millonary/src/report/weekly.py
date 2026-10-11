"""Informe semanal: Markdown + CSV de operaciones + Excel, a partir de los ficheros de la cuenta de papel.

  python -m src.report.weekly --data paper_state
Salida en <data>/semanal/: informe_semanal.md, operaciones.csv, diario.xlsx. Robusto ante cuentas vacías.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def _csv(p: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(p) if p.exists() and p.stat().st_size > 2 else pd.DataFrame()
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def _json(p: Path):
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except Exception:                                                # noqa: BLE001
        return None


def _dept(brief: dict | None, name: str) -> dict:
    return next((d for d in (brief or {}).get("departamentos", []) if d["dept"] == name), {})


def summarize(data: Path, now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    eq = _csv(data / "equity.csv"); tr = _csv(data / "diario_ordenes.csv"); pos = _csv(data / "diario_posiciones.csv")
    lots = _csv(data / "diario_lotes.csv"); brief = _json(data / "briefing.json"); prueba = _json(data / "informe_prueba.json")
    out = {"generado": str(now), "tiene_datos": not eq.empty}
    if not eq.empty:
        eq["bar"] = pd.to_datetime(eq["bar"], utc=True); e = eq.set_index("bar")["equity"]
        wk0 = now - pd.Timedelta(days=7); prev = e[e.index <= wk0]; base = float(prev.iloc[-1]) if len(prev) else float(e.iloc[0])
        w = e[e.index > wk0]
        out.update({"equity_inicial": float(e.iloc[0]), "equity_actual": float(e.iloc[-1]), "retorno_total": float(e.iloc[-1] / e.iloc[0] - 1),
                    "retorno_semana": float(e.iloc[-1] / base - 1), "caida_max": float((1 - e / e.cummax()).max()), "caida_actual": float(1 - e.iloc[-1] / e.cummax().iloc[-1]),
                    "dias": int((e.index[-1] - e.index[0]).days), "velas": int(len(e)), "exposicion_actual": float(eq["expo"].iloc[-1]),
                    "velas_semana": int(len(w))})
    if not tr.empty:
        tr["bar"] = pd.to_datetime(tr["bar"], utc=True); ws = tr[tr["bar"] > now - pd.Timedelta(days=7)]
        out.update({"ordenes_total": int(len(tr)), "ordenes_semana": int(len(ws)), "comisiones_total": float(tr["fee"].sum()), "comisiones_semana": float(ws["fee"].sum())})
    if not pos.empty:
        cl = pos[pos["estado"] == "CERRADA"]
        out["posiciones"] = {"cerradas": int(len(cl)), "ganan": int((cl["resultado"] == "GANA").sum()), "pierden": int((cl["resultado"] == "PIERDE").sum()),
                             "abiertas": int((pos["estado"] != "CERRADA").sum())}
    if not lots.empty:
        cl = lots[lots["estado"] == "CERRADO"]
        out["lotes"] = {"cerrados": int(len(cl)), "ganan": int((cl["resultado"] == "GANA").sum()), "pierden": int((cl["resultado"] == "PIERDE").sum()), "abiertos": int((lots["estado"] != "CERRADO").sum())}
    if prueba and prueba.get("puertas"): out["puertas"] = prueba["puertas"]; out["posterior_sharpe"] = prueba.get("posterior_sharpe")
    out["estado_comite"] = (brief or {}).get("estado"); out["decision"] = (brief or {}).get("decision")
    inc = _dept(brief, "Incubadora de traders").get("metrics", {})
    out["incubadora"] = {"certificadas": inc.get("certificadas", []), "forward": inc.get("forward", {})}
    led = _json(ROOT / "reports" / "mejoras_registro.json")
    if led:
        c = led["candidatas"]; etapas = {}
        for v in c.values(): etapas[v["etapa"]] = etapas.get(v["etapa"], 0) + 1
        fw = sorted(((k, v["forward"]) for k, v in c.items() if v.get("forward") and v["forward"].get("delta_sharpe") is not None), key=lambda kv: -kv[1]["delta_sharpe"])
        out["mejoras"] = {"n_pruebas": led["n_pruebas"], "etapas": etapas, "adoptables": [k for k, v in c.items() if v["etapa"].startswith("E4")],
                          "top_forward": [(k, v) for k, v in fw[:5]], "ultima_actualizacion": led.get("ultima_actualizacion")}
    return out


def _pct(x): return "n/d" if x is None else f"{x:+.2%}"


def markdown(s: dict) -> str:
    L = [f"# Informe semanal de Millonary · {s['generado'][:10]}", ""]
    if not s["tiene_datos"]:
        L += ["La cuenta de papel aún no ha procesado velas. El primer cierre oficial es el 2026-09-29 20:00 UTC.", ""]
    else:
        L += ["## Resumen", "",
              f"- Patrimonio: **{s['equity_actual']:,.2f} USDT** (inicio {s['equity_inicial']:,.2f}) · retorno de la prueba {_pct(s['retorno_total'])} · **esta semana {_pct(s['retorno_semana'])}**",
              f"- Caída máxima de la prueba {s['caida_max']:.2%} · caída actual {s['caida_actual']:.2%} · exposición actual {s['exposicion_actual']:.2f}×",
              f"- Día {s['dias']} de la prueba · {s['velas']} velas de 4h procesadas ({s['velas_semana']} esta semana)"]
        if "ordenes_total" in s: L.append(f"- Órdenes: {s['ordenes_total']} en total, {s['ordenes_semana']} esta semana · comisiones {s['comisiones_total']:.2f} USDT ({s['comisiones_semana']:.2f} esta semana)")
        if "posiciones" in s:
            p = s["posiciones"]; L.append(f"- Registro de entradas · posiciones cerradas {p['cerradas']}: **ganan {p['ganan']} / pierden {p['pierden']}** · abiertas {p['abiertas']}")
        if "lotes" in s:
            l = s["lotes"]; L.append(f"- Lotes (cada compra) cerrados {l['cerrados']}: ganan {l['ganan']} / pierden {l['pierden']} · abiertos {l['abiertos']}")
        L += ["", f"Decisión del comité: {s.get('decision')} · Estado: {s.get('estado_comite')}", ""]
        if s.get("puertas"):
            L += ["## Puertas del protocolo (paso a dinero real mínimo)", ""] + [f"- [{'OK' if v else 'NO'}] {k}" for k, v in s["puertas"].items()] + [""]
        L += ["> Un mes no demuestra rentabilidad: el sistema tiene ~0,46 posiciones cerradas al mes y ~27 % de acierto con ganancias ~9× la pérdida media; con ventaja real, 5 de cada 10 meses terminan en pérdida.", ""]
    inc = s.get("incubadora", {})
    L += ["## Incubadora de traders (sombra, sin capital)", "", f"Certificadas en el examen: {len(inc.get('certificadas', []))}/15."]
    fw = inc.get("forward", {})
    if fw:
        L += ["", "| Trader | Retorno hacia delante | Caída | Ops | Posición |", "|---|---|---|---|---|"]
        for k, v in sorted(fw.items(), key=lambda kv: -kv[1]["retorno"]):
            L.append(f"| {k} | {v['retorno']:+.2%} | {v['caida_max']:.1%} | {v['ops']} | {v['posicion_actual']:+.0f} |")
    m = s.get("mejoras")
    L += ["", "## Perfeccionamiento continuo (Laboratorio)", ""]
    if m:
        L.append(f"Pruebas acumuladas en el ciclo de mejora: {m['n_pruebas']}. Candidatas por etapa: " + ", ".join(f"{k}: {v}" for k, v in sorted(m["etapas"].items())) + ".")
        L.append("Adoptables (E4, solo en sombra): " + (", ".join(m["adoptables"]) if m["adoptables"] else "ninguna todavía (exigen ≥ 90 días hacia delante, ΔSharpe ≥ +0,3, caída ≤ 1,2× y p < 0,10 con Holm)."))
        if m["top_forward"]:
            L += ["", "| Candidata | Días | ΔSharpe hacia delante | Retorno base → variante |", "|---|---|---|---|"]
            for k, v in m["top_forward"]:
                L.append(f"| {k} | {v['dias']} | {v['delta_sharpe']:+.2f} | {v['ret_base']:+.2%} → {v['ret_var']:+.2%} |")
    else:
        L.append("Sin registro de mejoras: ejecutar `python -m src.lab.mejora build`.")
    L += ["", "*Todo lo anterior es simulación en papel. Ningún agente ni candidata toca capital; solo el núcleo validado opera y solo Riesgos puede vetar.*"]
    return "\n".join(L) + "\n"


def write_all(data: Path, now: pd.Timestamp | None = None) -> dict:
    data = Path(data); out = data / "semanal"; out.mkdir(parents=True, exist_ok=True)
    s = summarize(data, now); (out / "informe_semanal.md").write_text(markdown(s))
    (out / "resumen.json").write_text(json.dumps(s, indent=1, default=str))
    tr = _csv(data / "diario_ordenes.csv"); tr.to_csv(out / "operaciones.csv", index=False)
    try:
        with pd.ExcelWriter(out / "diario.xlsx", engine="openpyxl") as xw:
            pd.DataFrame([(k, json.dumps(v, default=str) if isinstance(v, (dict, list)) else v) for k, v in s.items()], columns=["campo", "valor"]).to_excel(xw, sheet_name="Resumen", index=False)
            for name, f in (("Equity", "equity.csv"), ("Ordenes", "diario_ordenes.csv"), ("Posiciones", "diario_posiciones.csv"), ("Lotes", "diario_lotes.csv")):
                d = _csv(data / f)
                for c in d.columns:                                    # Excel no admite fechas con zona horaria
                    if d[c].dtype == object and c in ("bar", "abre", "cierra"):
                        d[c] = pd.to_datetime(d[c], utc=True, errors="coerce").dt.tz_localize(None)
                (d if not d.empty else pd.DataFrame({"info": ["sin datos todavía"]})).to_excel(xw, sheet_name=name, index=False)
            fw = s["incubadora"].get("forward", {})
            pd.DataFrame([{"trader": k, **v} for k, v in fw.items()] or [{"info": "sin datos"}]).to_excel(xw, sheet_name="Incubadora", index=False)
            m = s.get("mejoras") or {}
            pd.DataFrame([{"candidata": k, **v} for k, v in m.get("top_forward", [])] or [{"info": "sin datos hacia delante"}]).to_excel(xw, sheet_name="Mejoras", index=False)
    except ImportError:
        pass
    return s


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--data", default="paper_state"); a = ap.parse_args()
    s = write_all(Path(a.data)); print(markdown(s))
