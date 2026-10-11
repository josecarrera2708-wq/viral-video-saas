"""Prueba de anchura del stop (prerregistro: config/mesa15_stops_prerregistrada.md). Solo traders BASE; el stop de cada señal se multiplica por m.
  python -m src.desk15.stops 15   |   python -m src.desk15.stops 1h
El TP en múltiplos de R se escala con el stop (misma geometría); el tamaño de la posición baja con el stop porque el riesgo es fijo (0,5 %)."""
from __future__ import annotations
import sys
from dataclasses import replace
import numpy as np
import pandas as pd
from ..backtest.engine import Params
from ..intraday.evaluate import summarize, run_period
from .evaluate import PERIODS, _days
from .setups import all_specs
from ..desk1h.setups import all_specs as specs1h
from ..desk1h.data import load_history_1h
from .data import load_history

MULTS = (1.0, 1.5, 2.0)


def table(df, f, specs_fn) -> dict:
    out = {}
    for k, sp in specs_fn(df).items():
        out[k] = {}
        for m in MULTS:
            s2 = replace(sp, stop=sp.stop * m); out[k][m] = {}
            for per in ("validacion", "examen"):
                a, b = PERIODS[per]; out[k][m][per] = summarize(run_period(df, f, s2, a, b, Params()), _days(a, b))
    return out


def report(t: dict, titulo: str) -> str:
    L = [f"# {titulo} · anchura del stop (R media por operación; ops entre paréntesis)", "", "| Trader | " + " | ".join(f"×{m} valid. | ×{m} examen" for m in MULTS) + " |", "|---|" + "---|" * (2 * len(MULTS))]
    for k, v in t.items():
        L.append(f"| {k} | " + " | ".join(f"{v[m][p]['R_media']:+.3f} ({v[m][p]['n']})" for m in MULTS for p in ("validacion", "examen")) + " |")
    L += ["", "Agregado (media de las 13 R medias; nº de traders mejores que ×1,0):", ""]
    for m in MULTS:
        for p in ("validacion", "examen"):
            r = np.mean([v[m][p]["R_media"] for v in t.values()]); better = sum(v[m][p]["R_media"] > v[1.0][p]["R_media"] for v in t.values())
            L.append(f"- ×{m} {p}: R media {r:+.3f}; mejor que ×1,0 en {better}/13")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    from ..desk15.data import ROOT
    which = sys.argv[1]
    df, f = load_history() if which == "15" else load_history_1h(); df = df[df.index < pd.Timestamp("2026-09-29", tz="UTC")]; f = f[: len(df)]
    t = table(df, f, all_specs if which == "15" else specs1h); txt = report(t, "Mesa de 15 min" if which == "15" else "Mesa de 1 h")
    (ROOT / "reports" / f"mesa{which}_stops.md").write_text(txt); print(txt)
