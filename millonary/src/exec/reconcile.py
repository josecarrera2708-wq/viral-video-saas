"""Conciliación: mide el deslizamiento real frente al modelado y compara las ejecuciones con las de la simulación."""
from __future__ import annotations
import numpy as np
from .base import Fill, BUY


def slippage_bps(fills: list[Fill]) -> list[float]:
    """Coste en pb (positivo = peor que el precio de referencia) de las ejecuciones que traen precio de referencia."""
    out = []
    for f in fills:
        if f.intended_price:
            sign = 1.0 if f.side == BUY else -1.0
            out.append(sign * (f.price - f.intended_price) / f.intended_price * 1e4)
    return out


def slippage_report(fills: list[Fill], modeled_bps: float = 2.0) -> dict:
    s = np.asarray(slippage_bps(fills), float)
    if len(s) == 0:
        return {"n": 0}
    return {"n": int(len(s)), "media_pb": float(s.mean()), "mediana_pb": float(np.median(s)), "p95_pb": float(np.percentile(s, 95)),
            "modelado_pb": modeled_bps, "peor_que_modelo": bool(s.mean() > modeled_bps)}


def compare_to_sim(sim: list[Fill], real: list[Fill]) -> dict:
    """Empareja por client_id. diff_pb > 0: el exchange ejecutó peor que la simulación."""
    r = {f.client_id: f for f in real}; d = []; missing = []
    for f in sim:
        g = r.get(f.client_id)
        if g is None:
            missing.append(f.client_id); continue
        sign = 1.0 if f.side == BUY else -1.0
        d.append(sign * (g.price - f.price) / f.price * 1e4)
    return {"emparejadas": len(d), "sin_ejecucion_real": missing, "diff_media_pb": float(np.mean(d)) if d else None,
            "diff_p95_pb": float(np.percentile(d, 95)) if d else None, "comisiones_sim": float(sum(f.fee for f in sim)), "comisiones_real": float(sum(f.fee for f in real))}
