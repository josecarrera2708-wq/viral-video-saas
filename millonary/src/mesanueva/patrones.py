"""Mesa de patrones (papel): `python -m src.mesanueva.patrones`. Prerregistro y regla: config/busqueda_v4_prerregistrada.md
(mejor variante elegible por familia de la búsqueda v4). Misma maquinaria que la mesa nueva (src/mesanueva/forward.py)."""
from __future__ import annotations
import pandas as pd
from . import forward as M
from ..busqueda import v4

D = M.F.ROOT / "paper_state" / "mesapatrones"
START = pd.Timestamp("2026-10-06T00:00:00Z")
TRADERS = {
    "Y01 Doble suelo 1 h (a favor de tendencia, dejar correr)": ("1h", "1h | B01 Doble suelo | a_favor_tendencia | dejar_correr", v4),
    "Y02 Triple suelo/techo 1 h (TP 3R)": ("1h", "1h | B03 Triple suelo/techo | sin_filtro | TP3", v4),
    "Y03 Rectángulo 1 h (dejar correr)": ("1h", "1h | B08 Rectángulo | sin_filtro | dejar_correr", v4),
    "Y04 Bandera / banderín 4 h (TP 3R)": ("4h", "4h | B09 Bandera / banderín | sin_filtro | TP3", v4),
    "Y05 Martillo / estrella fugaz diario (dejar correr)": ("1d", "1d | V05 Martillo / estrella fugaz en extremo | sin_filtro | dejar_correr", v4),
    "Y06 Cuatro velas seguidas diario (a favor de tendencia, dejar correr)": ("1d", "1d | V06 Cuatro velas seguidas (continuación) | a_favor_tendencia | dejar_correr", v4),
    "Y07 Ineficiencia FVG diario (a favor de tendencia, dejar correr)": ("1d", "1d | I01 Ineficiencia (FVG) 4 h / diario | a_favor_tendencia | dejar_correr", v4),
}


def main(now: pd.Timestamp | None = None, start: pd.Timestamp = START, out=D) -> dict:
    return M.main(now, TRADERS, out, start)


if __name__ == "__main__":
    o = main(); print({k: v for k, v in o.items() if k != "traders"})
    for k, v in o["traders"].items():
        print(f"{k:70s} {v['temporalidad']} ops {v['cerradas']:3d} R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
