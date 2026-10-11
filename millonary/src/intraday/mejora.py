"""Ciclo de mejora de la mesa intradía (config/intradia_mejoras_prerregistrada.md). Solo construcción y validación; el resto es hacia delante.

  python -m src.intraday.mejora build     # E1+E2 (una vez; queda en reports/intradia_mejoras.json)
"""
from __future__ import annotations
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.engine import Params
from src.incubator.factors import holm
from src.intraday.setups import all_specs, Spec
from src.intraday.evaluate import load, run_period, summarize, PERIODS
from src.signals.indicators import ema

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "reports" / "intradia_mejoras.json"


def m1_tendencia(df, sp: Spec) -> Spec:
    sgn = np.sign(df["close"] - ema(df["close"], 800)).fillna(0).to_numpy()
    return replace(sp, entry=np.where(sp.entry == sgn, sp.entry, 0).astype(np.int8))


def m2_stops_x2(df, sp: Spec) -> Spec:
    return replace(sp, stop=sp.stop * 2.0)


def m3_sesion(df, sp: Spec) -> Spec:
    h = df.index.hour; ok = (h >= 7) & (h < 21)
    return replace(sp, entry=np.where(ok, sp.entry, 0).astype(np.int8))


def m4_stop_minimo(df, sp: Spec) -> Spec:
    ok = np.nan_to_num(sp.stop) >= 0.008 * df["close"].to_numpy()
    return replace(sp, entry=np.where(ok, sp.entry, 0).astype(np.int8))


def m5_dejar_correr(df, sp: Spec) -> Spec:
    return replace(sp, tp_mult=sp.tp_mult * 1.5 if sp.tp_mult > 0 else 0.0, max_bars=sp.max_bars * 2)


OPERADORES = {"M1 a favor de la tendencia": m1_tendencia, "M2 stops ×2": m2_stops_x2, "M3 sesión 07-21 UTC": m3_sesion,
              "M4 stop mínimo 0,8 %": m4_stop_minimo, "M5 dejar correr": m5_dejar_correr}


def _days(per):
    a, b = PERIODS[per]; return (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days


def build(force: bool = False, ledger: Path = LEDGER) -> dict:
    if ledger.exists() and not force:
        return json.loads(ledger.read_text())
    df, f = load(); base = all_specs(df); cand = {}
    for k, sp in base.items():
        b = {per: summarize(run_period(df, f, sp, *PERIODS[per], Params()), _days(per)) for per in ("construccion", "validacion")}
        for on, fn in OPERADORES.items():
            v = {per: summarize(run_period(df, f, fn(df, sp), *PERIODS[per], Params()), _days(per)) for per in ("construccion", "validacion")}
            e1 = v["construccion"]["R_media"] >= b["construccion"]["R_media"] + 0.05
            e2 = v["validacion"]["R_media"] > b["validacion"]["R_media"] and v["validacion"]["R_media"] > 0
            cand[f"{k}|{on}"] = {"trader": k, "operador": on, "base": {p: {x: b[p][x] for x in ("n", "por_dia", "R_media", "retorno")} for p in b},
                                 "variante": {p: {x: v[p][x] for x in ("n", "por_dia", "R_media", "retorno", "caida_max", "acierto", "p_1s")} for p in v},
                                 "etapa": "E3 sombra" if (e1 and e2) else "descartada (E1/E2)"}
    keys = list(cand); ph = holm(np.array([cand[c]["variante"]["validacion"]["p_1s"] for c in keys]))
    for c, p in zip(keys, ph): cand[c]["p_holm_validacion"] = float(p)
    led = {"creado": str(pd.Timestamp.now(tz="UTC")), "n_pruebas": len(cand), "en_sombra": [c for c in keys if cand[c]["etapa"] == "E3 sombra"], "candidatas": cand}
    ledger.write_text(json.dumps(led, indent=1, default=float)); return led


if __name__ == "__main__":
    led = build(); c = led["candidatas"]; print("pruebas", led["n_pruebas"], "en sombra", len(led["en_sombra"]))
    best = sorted(c.items(), key=lambda kv: -kv[1]["variante"]["validacion"]["R_media"])[:12]
    for k, v in best:
        print(f"{k:60s} R constr {v['variante']['construccion']['R_media']:+.3f} (base {v['base']['construccion']['R_media']:+.3f}) | R valid {v['variante']['validacion']['R_media']:+.3f} (base {v['base']['validacion']['R_media']:+.3f}) ops/día {v['variante']['validacion']['por_dia']:.2f} p_holm {v['p_holm_validacion']:.2f} {v['etapa']}")
