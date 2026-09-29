"""Evaluación histórica de la mesa intradía (config/intradia_prerregistrada.md). El examen sellado se ejecuta UNA vez.

Salida: reports/intradia_resultados.json / .md
"""
from __future__ import annotations
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.engine import Params, run, REASONS
from src.backtest.funding import align_funding
from src.incubator.factors import holm
from src.intraday.setups import SETUPS, all_specs

ROOT = Path(__file__).resolve().parents[2]
H1 = pd.Timedelta("1h")
PERIODS = {"construccion": ("2020-01-01", "2024-01-01"), "validacion": ("2024-01-01", "2025-07-01"), "examen": ("2025-07-01", "2026-09-01")}
WARM = 300


def load() -> tuple[pd.DataFrame, np.ndarray]:
    d = pd.read_parquet(ROOT / "data" / "raw" / "perp_BTCUSDT_1h.parquet").set_index("time")
    d = d[(d.index >= pd.Timestamp("2019-12-01", tz="UTC")) & (d.index < pd.Timestamp("2026-09-01", tz="UTC"))][["open", "high", "low", "close", "volume"]]
    ev = pd.read_parquet(ROOT / "data" / "raw" / "perp_BTCUSDT_funding.parquet"); ev = ev[ev["time"] < pd.Timestamp("2026-09-01", tz="UTC")]
    return d, align_funding(d.index, H1, ev[["time", "funding_rate"]])


def run_period(df, f, spec, start, end, params: Params) -> dict:
    """Corre el motor sobre [start, end) con calentamiento previo; las señales anteriores a start se anulan."""
    s0, e0 = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    i0 = int(df.index.searchsorted(s0)); i1 = int(df.index.searchsorted(e0)); a = max(0, i0 - WARM)
    sl = slice(a, i1); idx = df.index[sl]; live = np.asarray(idx >= s0)
    ent = np.where(live, spec.entry[sl], 0).astype(np.int8); ex = None if spec.exit is None else np.where(live, spec.exit[sl], 0).astype(np.int8)
    stop = np.nan_to_num(spec.stop[sl], nan=0.0)
    p = replace(params, tp_mult=spec.tp_mult, max_bars=spec.max_bars)
    o = df.iloc[sl]; r = run(o["open"], o["high"], o["low"], o["close"], ent, stop, p, exit_sig=ex, funding=f[sl])
    return {"r": r, "idx": idx, "start_i": int(np.argmax(live))}


def summarize(res: dict, days: float) -> dict:
    r = res["r"]; n = int(r["n_trades"]); R = np.asarray(r["r"], float); pnl = np.asarray(r["pnl"], float)
    eq = pd.Series(r["equity"], index=res["idx"]); eq = eq.iloc[res["start_i"]:]; d = eq.resample("1D").last().pct_change().dropna()
    reasons = np.asarray(r["reason"]); share = {REASONS[k]: float((reasons == k).mean()) if n else 0.0 for k in REASONS}
    t = float(R.mean() / (R.std(ddof=1) / np.sqrt(n))) if n > 2 and R.std(ddof=1) > 0 else 0.0
    return {"n": n, "por_dia": n / days, "acierto": float((R > 0).mean()) if n else 0.0, "R_media": float(R.mean()) if n else 0.0, "t_R": t,
            "p_1s": float(1 - st.t.cdf(t, df=max(n - 1, 1))) if n > 2 else 1.0, "retorno": float(eq.iloc[-1] / eq.iloc[0] - 1) if len(eq) else 0.0,
            "caida_max": float((1 - eq / eq.cummax()).max()) if len(eq) else 0.0, "sharpe": float(d.mean() / d.std(ddof=1) * np.sqrt(365)) if len(d) > 10 and d.std(ddof=1) > 0 else 0.0,
            "salidas": share, "liquidado": bool(r["ruined"]), "saltadas_lote_minimo": int(r["skipped_minlot"])}


def stress(k: float) -> Params:
    b = Params(); return replace(b, taker_fee=b.taker_fee * k, maker_fee=b.maker_fee * k, slippage=b.slippage * k)


def mc_band(R: np.ndarray, risk=0.005, n=2000, seed=0) -> dict:
    if len(R) < 20: return {}
    rng = np.random.default_rng(seed); dd, ret = [], []
    for _ in range(n):
        x = rng.choice(R, len(R), replace=True) * risk; eq = np.cumprod(1 + x); ret.append(eq[-1] - 1); dd.append((1 - eq / np.maximum.accumulate(eq)).max())
    return {"ret_p5": float(np.percentile(ret, 5)), "ret_p50": float(np.percentile(ret, 50)), "ret_p95": float(np.percentile(ret, 95)),
            "dd_p50": float(np.percentile(dd, 50)), "dd_p95": float(np.percentile(dd, 95)), "R_total_p5": float(np.percentile([rng.choice(R, len(R)).sum() for _ in range(n)], 5))}


def truncation_ok(df: pd.DataFrame, cut: int = 20000) -> dict:
    """La señal en la vela i no debe cambiar si se altera el futuro (i > cut)."""
    d2 = df.copy(); cols = d2.columns.get_indexer(["open", "high", "low", "close"]); d2.iloc[cut + 1:, cols] *= 1.37
    a, b = all_specs(df), all_specs(d2); out = {}
    for k in a:
        out[k] = bool(np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]) and np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True))
    return out


def evaluate(write: bool = True) -> dict:
    df, f = load(); specs = all_specs(df); trunc = truncation_ok(df); rows = {}
    for k, sp in specs.items():
        rows[k] = {"periodos": {}, "costes": {}}
        for per, (a, b) in PERIODS.items():
            days = (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days
            rows[k]["periodos"][per] = summarize(run_period(df, f, sp, a, b, Params()), days)
        a, b = PERIODS["examen"]; days = (pd.Timestamp(b, tz="UTC") - pd.Timestamp(a, tz="UTC")).days
        for m in (1.5, 2.0, 3.0):
            rows[k]["costes"][f"x{m}"] = summarize(run_period(df, f, sp, a, b, stress(m)), days)
        ex = run_period(df, f, sp, a, b, Params())["r"]; R = np.asarray(ex["r"], float)
        rows[k]["montecarlo_examen"] = mc_band(R); rows[k]["R_examen"] = R.tolist() if False else None
        rows[k]["truncamiento_ok"] = trunc[k]
    names = list(rows); p = np.array([rows[k]["periodos"]["examen"]["p_1s"] for k in names]); ph = holm(p)
    for i, k in enumerate(names):
        r = rows[k]; ex, va, c2 = r["periodos"]["examen"], r["periodos"]["validacion"], r["costes"]["x2.0"]; r["p_holm"] = float(ph[i])
        g = {"Q1 ≥0,3 ops/día": ex["por_dia"] >= 0.3, "Q2 R>0 validación y examen": va["R_media"] > 0 and ex["R_media"] > 0,
             "Q3 p Holm<0,10 (examen)": r["p_holm"] < 0.10, "Q4 R>0 con costes ×2": c2["R_media"] > 0, "Q5 truncamiento": r["truncamiento_ok"],
             "Q6 sin liquidación y caída<40 %": (not ex["liquidado"]) and ex["caida_max"] < 0.40, "Q7 Sharpe<6": ex["sharpe"] < 6}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
    out = {"periodos": PERIODS, "n_setups": len(names), "certificadas": [k for k in names if rows[k]["certificada"]], "setups": rows}
    if write:
        (ROOT / "reports" / "intradia_resultados.json").write_text(json.dumps(out, indent=1, default=float)); (ROOT / "reports" / "intradia_resultados.md").write_text(md(out))
    return out


def md(o: dict) -> str:
    L = ["# Mesa intradía · Resultados históricos (examen sellado 2025-07 → 2026-08, ejecución única)", "",
         f"Certificadas: **{len(o['certificadas'])}/{o['n_setups']}** · Capital 1.000 USDT por trader, riesgo 0,5 % por operación, costes reales del motor.", "",
         "| Trader | Ops/día | Acierto | R media constr. | R media valid. | R media examen | t | Retorno examen | Caída | TP / Stop / Tiempo / Señal | R ×2 costes | p Holm | Puertas | Cert. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["setups"].items():
        c, v, e = r["periodos"]["construccion"], r["periodos"]["validacion"], r["periodos"]["examen"]; s = e["salidas"]
        L.append(f"| {k} | {e['por_dia']:.2f} | {e['acierto']:.0%} | {c['R_media']:+.3f} | {v['R_media']:+.3f} | {e['R_media']:+.3f} | {e['t_R']:.1f} | {e['retorno']:+.1%} | {e['caida_max']:.0%} | "
                 f"{s['tp']:.0%}/{s['stop']:.0%}/{s['time']:.0%}/{s['signal']:.0%} | {r['costes']['x2.0']['R_media']:+.3f} | {r['p_holm']:.2f} | {sum(r['puertas'].values())}/7 | {'✔' if r['certificada'] else '—'} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
