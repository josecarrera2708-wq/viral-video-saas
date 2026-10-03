"""Reparto de capital SIMULADO por mérito estadístico (config/incubadora_prerregistrada.md)."""
from __future__ import annotations
import numpy as np

CAP = 0.25


def allocate(results: dict, corr: dict | None = None) -> dict:
    """results: salida de evaluate.run(). Devuelve {trader: peso} con el núcleo como miembro base (peso = 1 - suma del resto)."""
    cert = results.get("certificadas", [])
    if not cert:
        return {"núcleo v1": 1.0}
    raw = {}
    for k in cert:
        r = results["setups"][k]; vol = max(abs(r["retorno_anual_full"]) / max(abs(r["sharpe_full"]), 1e-6), 1e-3)   # σ anual implícita
        pen = 1.0 - (corr.get(k, 0.0) if corr else 0.0)
        raw[k] = (1.0 - r["p_holm"]) / vol * max(pen, 0.0)
    tot = sum(raw.values()) or 1.0
    w = {k: min(CAP, v / tot * 0.5) for k, v in raw.items()}       # como mucho la mitad del fondo entre las certificadas
    w["núcleo v1"] = round(1.0 - sum(w.values()), 6)
    return w
