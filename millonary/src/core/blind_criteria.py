"""Fija los criterios numéricos del periodo ciego usando SOLO datos < 2025-07-01 (antes de abrirlo)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.funding import align_funding
from src.core.nucleo import CoreParams, run_core
from src.core.evaluate_nucleo import load_spot, funding_events, daily_ret, DELTA

ROOT = Path(__file__).resolve().parents[2]
df, _ = load_spot(); fund = align_funding(df.index, DELTA, funding_events(df.index))
core = run_core(df, fund, CoreParams())
r = daily_ret(core["equity"]).to_numpy(); n = len(r); L = 426               # ≈ 14 meses (2025-07 → 2026-08)
rng = np.random.default_rng(123); S = 5000; dds = np.empty(S)
for s in range(S):                                                          # bootstrap estacionario, bloque medio 30
    idx = np.empty(L, np.int64); idx[0] = rng.integers(n)
    for t in range(1, L):
        idx[t] = rng.integers(n) if rng.random() < 1 / 30 else (idx[t - 1] + 1) % n
    eq = np.cumprod(1 + r[idx]); dds[s] = (1 - eq / np.maximum.accumulate(np.r_[1, eq])[1:]).max()
yrs = (df.index[-1] - df.index[0]).days / 365.25
crit = {"nota": "Fijado antes de abrir el ciego, solo con datos < 2025-07-01",
        "dd_bootstrap_p50": float(np.percentile(dds, 50)), "dd_bootstrap_p95": float(np.percentile(dds, 95)),
        "exposicion_media_ref": float(core["expo"].mean()), "rotacion_anual_ref": float(core["turn"].sum() / yrs),
        "banda_exposicion": [float(core["expo"].mean() * 0.5), float(core["expo"].mean() * 1.5)],
        "banda_rotacion": [float(core["turn"].sum() / yrs * 0.5), float(core["turn"].sum() / yrs * 1.5)],
        "aceptable_si": "DD ciego <= dd_bootstrap_p95 Y exposición media dentro de banda_exposicion Y rotación anual dentro de banda_rotacion"}
(ROOT / "config" / "blind_criteria.json").write_text(json.dumps(crit, indent=1))
print(json.dumps(crit, indent=1))
