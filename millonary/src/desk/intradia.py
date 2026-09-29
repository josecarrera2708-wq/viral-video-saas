"""Mesa intradía (departamento del comité): resume paper_state/intradia/resumen.json (lo actualiza la rutina horaria)."""
from __future__ import annotations
import json
from .base import Context, Report, OK, AVISO


def mesa_intradia(ctx: Context) -> Report:
    p = ctx.cfg.data_dir / "intradia" / "resumen.json"
    if not p.exists():
        return Report("Mesa intradía", "Aún sin datos (la rutina horaria no ha corrido)", OK)
    j = json.loads(p.read_text()); T = j["traders"]; pos = [k for k, v in T.items() if v.get("abierta")]
    pos_ = sorted(T.items(), key=lambda kv: -kv[1]["retorno"])
    notes = [f"14 traders en papel · {j['trades_totales']} operaciones cerradas ({j['por_dia_total']:.1f} al día entre todos) · {len(pos)} posiciones abiertas.",
             f"Datos: {j['fuente']}, última vela cerrada {j['ultima_vela_cerrada'][:16]} UTC."]
    for k, v in pos_[:3]:
        notes.append(f"  {k}: {v['retorno']:+.2%} · {v['cerradas']} ops · R total {v['R_total']:+.2f}")
    notes.append("El histórico 2020-2026 da expectativa negativa tras costes en los 14 (0/14 certificadas): esta prueba mide si se confirma hacia delante.")
    return Report("Mesa intradía", f"{j['trades_totales']} operaciones · {len(pos)} abiertas", OK, {"resumen": j["trades_totales"]}, notes,
                  [f"{k} abierta: {T[k]['abierta']['lado']} @ {T[k]['abierta']['px_entrada']:.0f}" for k in pos[:3]])
