"""Mesa de 1 h hacia delante (papel): `python -m src.desk1h.forward`. Misma maquinaria que la mesa de 15 min (src/desk15/forward.py) sobre velas de 1 h
construidas desde las de 15 min de Deribit (solo horas completas). Inicio 2026-10-02 00:00 UTC (config/mesa15_start.json)."""
from __future__ import annotations
import pandas as pd
from ..desk15 import forward as F
from ..desk15.learner import context15
from .setups import all_specs
from .data import to_1h, H1

D1 = F.ROOT / "paper_state" / "mesa1h"


def load_bars_1h(now: pd.Timestamp):
    bars, f = F.load_bars(now); return to_1h(bars, f)


DESK1H = {"dir": D1, "iv": H1, "load": load_bars_1h, "specs": all_specs, "ctx": lambda b: context15(b, 800, 500), "fuente": "Deribit BTC-PERPETUAL 1 h (velas cerradas, desde 15 min)"}

if __name__ == "__main__":
    o = F.main(dk=DESK1H); print({k: v for k, v in o.items() if k != "traders"})
    for k, v in o["traders"].items():
        print(f"{k:55s} ops {v['cerradas']:3d} R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
