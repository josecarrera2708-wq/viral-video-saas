"""Mesa de patrones (papel) = la ÚNICA mesa de trading activa desde 2026-10-06: `python -m src.mesanueva.patrones`.
Composición fijada en config/busqueda_v5_prerregistrada.md (consolidación decidida por el dueño): traders de la v4 (Y), de la mesa nueva (X07, X08)
y de la v5 (Z) que ganaron en el examen 2025-07 → 2026-09. Misma maquinaria que src/mesanueva/forward.py."""
from __future__ import annotations
import pandas as pd
from . import forward as M
from ..busqueda import v3, v4, v5

D = M.F.ROOT / "paper_state" / "mesapatrones"
START = pd.Timestamp("2026-10-06T00:00:00Z")
TRADERS = {
    "Y01 Doble suelo 1 h (a favor de tendencia, dejar correr)": ("1h", "1h | B01 Doble suelo | a_favor_tendencia | dejar_correr", v4),
    "Y02 Triple suelo/techo 1 h (TP 3R)": ("1h", "1h | B03 Triple suelo/techo | sin_filtro | TP3", v4),
    "Y04 Bandera / banderín 4 h (TP 3R)": ("4h", "4h | B09 Bandera / banderín | sin_filtro | TP3", v4),
    "Y07 Ineficiencia FVG diario (a favor de tendencia, dejar correr)": ("1d", "1d | I01 Ineficiencia (FVG) 4 h / diario | a_favor_tendencia | dejar_correr", v4),
    "X07 Conjunto de tendencias CTA 4 h": ("4h", "4h | N11 Conjunto de tendencias CTA | ambos", v3),
    "X08 MAX de 20 días (Quantpedia)": ("1d", "1d | N05 MAX de n días (Quantpedia) | n=20", v3),
    "Z01 Doble suelo 1 h + tendencia superior (dejar correr)": ("1h", "1h | C01 Doble suelo | K3 tendencia superior (EMA 50 días) | dejar_correr", v5),
    "Z02 Triple suelo/techo 1 h + tendencia superior (dejar correr)": ("1h", "1h | C03 Triple suelo/techo | K3 tendencia superior (EMA 50 días) | dejar_correr", v5),
}


def main(now: pd.Timestamp | None = None, start: pd.Timestamp = START, out=D) -> dict:
    return M.main(now, TRADERS, out, start)


if __name__ == "__main__":
    o = main(); print({k: v for k, v in o.items() if k != "traders"})
    for k, v in o["traders"].items():
        print(f"{k:70s} {v['temporalidad']} ops {v['cerradas']:3d} R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
