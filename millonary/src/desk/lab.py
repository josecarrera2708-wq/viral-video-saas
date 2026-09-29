"""Laboratorio (cuantitativo / ML): estrategias en SOMBRA evaluadas hacia delante con el mismo simulador validado.

Cada variante arranca PLANA en la fecha de inicio de la prueba y se compara con el núcleo. Ninguna toca capital.
Promoción a capital real (protocolo): ≥ 90 días hacia delante, Sharpe ≥ núcleo + 0,3, caída ≤ 1,2× la del núcleo,
embudo de robustez superado sobre la historia, y anotada como prueba nueva en el registro.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..backtest.funding import align_funding
from ..core.nucleo import CoreParams, compute_targets, _simulate
from .base import Context, Report, OK, AVISO

ROOT = Path(__file__).resolve().parents[2]
H4 = pd.Timedelta("4h")
SHADOWS = {
    "nucleo (referencia)": CoreParams(),
    "solo pata A (momentum diario)": CoreParams(w_a=1.0, w_b=0.0),
    "solo pata B (Donchian 50)": CoreParams(w_a=0.0, w_b=1.0),
    "vol. objetivo 20 %": CoreParams(target_vol=0.20),
    "vol. objetivo 35 %": CoreParams(target_vol=0.35),
    "horizontes cortos (10/20/40/60d)": CoreParams(horizons=(10, 20, 40, 60)),
    "horizontes largos (60/120/250/365d)": CoreParams(horizons=(60, 120, 250, 365)),
}


def run_from(df: pd.DataFrame, funding: np.ndarray, p: CoreParams, start: pd.Timestamp | None) -> pd.Series:
    """Equity (base 1) de la variante arrancando PLANA en el primer cierre >= start (o al inicio si start es None)."""
    n = len(df); ct = compute_targets(df, p); sig, tgt = ct["sig"], ct["tgt"]
    i0 = 0 if start is None else int((df.index + H4).searchsorted(pd.Timestamp(start), side="left"))   # independiente de la resolución de fechas
    i0 = max(i0, 2)
    r = df["close"].pct_change().fillna(0).to_numpy()
    target = np.zeros(n); changed = np.zeros(n, bool)
    if i0 + 1 < n:
        target[i0 + 1:] = tgt[i0:-1]; changed[i0 + 1:] = sig[i0:-1] != sig[i0 - 1:-2]
    eq, *_ = _simulate(r, target, changed, funding, p.cost, p.band)
    s = pd.Series(eq, index=df.index)
    return s[s.index >= df.index[min(i0, n - 1)]] / s.iloc[min(i0, n - 1)]


def _metrics(eq: pd.Series) -> dict:
    d = eq.resample("1D").last().pct_change().dropna()
    days = len(d)
    out = {"dias": days, "retorno": float(eq.iloc[-1] - 1), "caida_max": float((1 - eq / eq.cummax()).max())}
    out["sharpe"] = float(d.mean() / d.std(ddof=1) * np.sqrt(365)) if days >= 10 and d.std(ddof=1) > 0 else None
    return out


def laboratorio(ctx: Context) -> Report:
    if ctx.lab_start is None:
        return Report("Laboratorio (cuantitativo / ML)", "Sin fecha de inicio de prueba", OK)
    df = ctx.bars
    fe = ctx.funding_events if ctx.funding_events is not None else pd.DataFrame(columns=["time", "funding_rate"])
    f = align_funding(df.index, H4, fe) if len(fe) else np.zeros(len(df))
    res = {}
    for name, p in SHADOWS.items():
        try:
            res[name] = _metrics(run_from(df, f, p, ctx.lab_start))
        except Exception as e:                                        # noqa: BLE001
            res[name] = {"error": str(e)}
    ref = res["nucleo (referencia)"]; notes = []
    dias = ref.get("dias", 0)
    notes.append(f"Todas las variantes arrancan planas el {pd.Timestamp(ctx.lab_start):%Y-%m-%d %H:%M} UTC; {dias} días hacia delante.")
    for name, m in res.items():
        if "error" in m or name.startswith("nucleo"): continue
        sh = "n/d" if m["sharpe"] is None else f"{m['sharpe']:.2f}"
        promo = "sin evidencia (faltan días)" if dias < 90 else ("CANDIDATA" if (m["sharpe"] is not None and ref["sharpe"] is not None and m["sharpe"] >= ref["sharpe"] + 0.3 and m["caida_max"] <= 1.2 * ref["caida_max"]) else "no supera al núcleo")
        notes.append(f"  {name}: retorno {m['retorno']:+.1%} · caída {m['caida_max']:.1%} · Sharpe {sh} → {promo}")
    hist = ROOT / "reports" / "lab_historia.json"
    if hist.exists():
        notes.append("Contexto histórico de cada variante (2017-2025-06, solo exploratorio) en reports/lab_historia.json; cada una cuenta como prueba en el registro.")
    notes.append("Regla de promoción: ≥ 90 días hacia delante, Sharpe ≥ núcleo + 0,3, caída ≤ 1,2× la del núcleo, embudo de robustez superado.")
    return Report("Laboratorio (cuantitativo / ML)", f"{len(SHADOWS) - 1} variantes en sombra · {dias} días de prueba", OK,
                  {"variantes": res}, notes)


def lab_history(out: Path | None = None) -> dict:
    """Evalúa las variantes sobre la historia previa al ciego (spot 2017-2025.06). Exploratorio."""
    from ..core.evaluate_nucleo import load_spot, funding_events, daily_ret, sharpe, DELTA
    df, _ = load_spot(); f = align_funding(df.index, DELTA, funding_events(df.index))
    res = {}
    for name, p in SHADOWS.items():
        eq = run_from(df, f, p, None); d = daily_ret(eq)
        yrs = (eq.index[-1] - eq.index[0]).days / 365.25
        res[name] = {"sharpe": sharpe(d), "cagr": float(eq.iloc[-1] ** (1 / yrs) - 1), "caida_max": float((1 - eq / eq.cummax()).max())}
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
    return res
