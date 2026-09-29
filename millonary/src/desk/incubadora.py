"""Incubadora de traders + mesa de estrategias minadas (departamento del comité)."""
from __future__ import annotations
import json
from pathlib import Path
from .base import Context, Report, OK, AVISO
from ..incubator.forward import forward_run
from ..incubator.allocate import allocate

ROOT = Path(__file__).resolve().parents[2]


def incubadora(ctx: Context) -> Report:
    res_path = ROOT / "reports" / "incubadora_resultados.json"
    hist = json.loads(res_path.read_text()) if res_path.exists() else None
    fwd = forward_run(ctx.bars, ctx.funding_events, ctx.lab_start)
    notes, shadow = [], []
    if hist:
        cert = hist["certificadas"]
        notes.append(f"Histórico (examen 2024-01→2025-06, 15 traders): certificadas {len(cert)}/15 · PBO del conjunto {hist['pbo_conjunto']:.2f}. "
                     f"Mejor Sharpe en examen ≈ {max(r['sharpe_exam'] for r in hist['setups'].values()):.2f} (buy&hold {hist['referencia_buy_hold']['sharpe_exam']:.2f}); menor p (Holm) del α = {min(r['p_holm'] for r in hist['setups'].values()):.2f}.")
        w = allocate(hist)
        notes.append("Reparto de capital simulado por mérito: " + ", ".join(f"{k} {v:.0%}" for k, v in w.items()) + ".")
        notes.append("Mesa de estrategias minadas: " + (", ".join(cert) if cert else "vacía (ninguna certificada; el capital sigue 100 % en el núcleo)."))
    else:
        notes.append("Sin resultados del examen: ejecutar `python -m src.incubator.evaluate`.")
    dias = max((v["dias"] for v in fwd.values()), default=0)
    if fwd:
        rank = sorted(fwd.items(), key=lambda kv: -kv[1]["retorno"])
        notes.append(f"Ranking hacia delante ({dias} días, sombra; sin capital, sin valor estadístico hasta ≥ 90 días):")
        for k, v in rank[:5]:
            notes.append(f"  {k}: {v['retorno']:+.2%} · caída {v['caida_max']:.1%} · {v['ops']} ops · posición {v['posicion_actual']:+.0f}")
        shadow = [f"{k}: {v['retorno']:+.2%} hacia delante ({v['ops']} ops)" for k, v in rank[:3]]
    return Report("Incubadora de traders", f"15 traders en sombra · {len(hist['certificadas']) if hist else 0} certificadas · {dias} días",
                  OK, {"forward": fwd, "certificadas": hist["certificadas"] if hist else []}, notes, shadow)
