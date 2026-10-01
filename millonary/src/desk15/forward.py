"""Mesa de 15 min hacia delante (papel). Rutina horaria: `python -m src.desk15.forward`.

Histórico congelado en paper_state/mesa15/hist.parquet (velas y funding hasta el inicio) + las velas nuevas de Deribit desde entonces.
Se recalcula TODO desde el inicio en cada ejecución (idempotente): las decisiones son idénticas a ejecutarlo cada 15 min, porque el papel entra en la
apertura de la vela siguiente. Los aprendices siguen aprendiendo con las operaciones de la base (histórico + nuevas), solo con operaciones ya CERRADAS.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from scipy.stats import norm
from ..backtest.engine import Params, run
from ..intraday.postmortem import detail, learning
from .data import ROOT, M15, fetch_bars, fetch_funding
from .setups import all_specs
from .learner import context15, base_trades, gate, N_MIN, _cum_stats, veto_state, what_learned, LABELS

D = ROOT / "paper_state" / "mesa15"
COLS = ["trader", "abre", "cierra", "lado", "px_entrada", "sl", "tp", "lote_btc", "nocional_usdt", "riesgo_usdt", "stop_pct", "px_salida", "salida", "R", "pnl_usdt",
        "comision_usdt", "funding_usdt", "barras", "max_barras", "mfe_R", "mae_R", "post_stop_R", "tendencia_a_favor", "vol_percentil", "hora_utc", "abierta", "lecciones"]


def load_bars(now: pd.Timestamp) -> tuple[pd.DataFrame, np.ndarray]:
    h = pd.read_parquet(D / "hist.parquet"); bars = h[["open", "high", "low", "close", "volume"]]; f = h["f"].to_numpy()
    a = bars.index[-1] + M15
    if now - a >= M15:
        new = fetch_bars(a, now)
        if len(new):
            fn = fetch_funding(new.index, now); bars = pd.concat([bars, new]); f = np.r_[f, fn]
    return bars, f


def _eng(bars, f, sp, entry=None):
    ent = sp.entry if entry is None else entry
    return run(bars["open"], bars["high"], bars["low"], bars["close"], ent, np.nan_to_num(sp.stop, nan=0.0), Params(tp_mult=sp.tp_mult, max_bars=sp.max_bars), exit_sig=sp.exit, funding=f)


DESK15 = {"dir": D, "iv": M15, "load": load_bars, "specs": all_specs, "ctx": context15, "fuente": "Deribit BTC-PERPETUAL 15 min (velas cerradas)"}


def run_all(now: pd.Timestamp | None = None, start: str | None = None, dk: dict | None = None) -> dict:
    dk = dk or DESK15; iv = dk["iv"]
    cfg = json.loads((ROOT / "config" / "mesa15_start.json").read_text()); start = pd.Timestamp(start or cfg["start"]); now = now or pd.Timestamp.now(tz="UTC")
    bars, f = dk["load"](now); specs = dk["specs"](bars); ctx = dk["ctx"](bars)
    live = np.asarray(bars.index + iv >= start); i0 = int(np.argmax(live)) if live.any() else len(bars)
    tb = {k: base_trades(_eng(bars, f, sp), bars, ctx) for k, sp in specs.items()}                 # base sobre TODO el histórico: material de aprendizaje (solo operaciones cerradas)
    pooled = [t for v in tb.values() for t in v]; variants = {}; veto_info = {}
    n = len(bars); ccnt, cs, css = _cum_stats(pooled, n)
    for k, sp in specs.items():
        variants[k] = sp; variants[f"{k} · A"], vA = gate(sp, bars, ctx, tb[k], N_MIN["A"]); variants[f"{k} · C"], vC = gate(sp, bars, ctx, pooled, N_MIN["C"])
        acnt, as_, ass = _cum_stats(tb[k], n)
        veto_info[k] = {"A": what_learned(vA, acnt, as_, ass, bars, n - 1), "C": what_learned(vC, ccnt, cs, css, bars, n - 1)}
    summ, frames = {}, []; days = max((now - start).total_seconds() / 86400, 1e-9)
    for name, sp in variants.items():
        ent = np.where(live, sp.entry, 0).astype(np.int8); ex = None if sp.exit is None else np.where(live, sp.exit, 0).astype(np.int8)
        from dataclasses import replace
        r = run(bars["open"], bars["high"], bars["low"], bars["close"], ent, np.nan_to_num(sp.stop, nan=0.0), Params(tp_mult=sp.tp_mult, max_bars=sp.max_bars), exit_sig=ex, funding=f)
        rows = [detail(bars, ctx, name, sp, r, i, sp.tp_mult, sp.max_bars) for i in range(int(r["n_trades"]))]
        t = pd.DataFrame(rows, columns=COLS); t["duracion_min"] = t["barras"] * int(iv.total_seconds() // 60); frames.append(t); cl = t[~t["abierta"]] if len(t) else t
        R = cl["R"].to_numpy() if len(cl) else np.array([]); m = len(R); eq = np.asarray(r["equity"])[i0:]; sd = float(R.std(ddof=1)) if m > 2 else 0.0; mean = float(R.mean()) if m else 0.0
        summ[name] = {"cerradas": m, "por_dia": m / days, "ganan": int((R > 0).sum()), "pierden": int((R <= 0).sum()), "R_media": mean, "R_total": float(R.sum()) if m else 0.0,
                      "pnl_usdt": float(cl["pnl_usdt"].sum()) if m else 0.0, "equity": float(eq[-1]) if len(eq) else 1000.0, "retorno": float(eq[-1] / 1000 - 1) if len(eq) else 0.0,
                      "caida_max": float((1 - eq / np.maximum.accumulate(eq)).max()) if len(eq) else 0.0, "p_R_positiva": float(norm.cdf(mean / (sd / np.sqrt(m)))) if m > 10 and sd > 0 else None,
                      "salidas": {s: int((cl["salida"] == s).sum()) for s in ("tp", "stop", "time", "signal", "liq")} if m else {},
                      "abierta": (t[t["abierta"]].iloc[-1].drop("lecciones").to_dict() if len(t) and t["abierta"].any() else None)}
    allt = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=COLS)
    return {"bars": bars, "now": now, "start": start, "summ": summ, "trades": allt, "veto": veto_info, "days": days, "funding_ok": bool(np.any(f[-200:] != 0))}


def main(now: pd.Timestamp | None = None, dk: dict | None = None) -> dict:
    dk = dk or DESK15; D = dk["dir"]; iv = dk["iv"]; D.mkdir(parents=True, exist_ok=True); o = run_all(now, dk=dk); allt, summ = o["trades"], o["summ"]
    if len(allt):
        allt.assign(lecciones=allt["lecciones"].map(lambda x: " | ".join(x))).to_csv(D / "trades.csv", index=False)
        (D / "trades_detalle.json").write_text(json.dumps(allt.sort_values("abre", ascending=False).head(400).to_dict("records"), default=str, ensure_ascii=False, indent=1))
        (D / "aprendizaje.json").write_text(json.dumps(learning(allt[~allt["trader"].str.contains(" · ")].to_dict("records")), ensure_ascii=False, indent=1))
    else:
        (D / "trades.csv").write_text("")
    # lo aprendido: contextos vetados ahora, con la evidencia
    learned = {k: {tag: [x for x in v[tag] if x["vetado"]] for tag in ("A", "C")} for k, v in o["veto"].items()}
    (D / "aprendices.json").write_text(json.dumps({"generado": str(o["now"]), "reglas": {"A": f"n ≥ {N_MIN['A']} con operaciones propias", "C": f"n ≥ {N_MIN['C']} con operaciones de toda la sala", "t": "t ≤ −1 frente a la media global"},
                                                   "vetado": learned, "estado": o["veto"]}, ensure_ascii=False, indent=1, default=str))
    bars = o["bars"]
    out = {"generado": str(o["now"]), "ultima_vela_cerrada": str(bars.index[-1] + iv), "inicio": str(o["start"]), "fuente": dk["fuente"], "funding_disponible": o["funding_ok"],
           "precio_actual": float(bars["close"].iloc[-1]), "traders": summ, "trades_totales": int(sum(v["cerradas"] for k, v in summ.items() if " · " not in k)),
           "por_dia_total": float(sum(v["por_dia"] for k, v in summ.items() if " · " not in k))}
    (D / "resumen.json").write_text(json.dumps(out, indent=1, default=str)); return out


if __name__ == "__main__":
    o = main(); print({k: v for k, v in o.items() if k != "traders"})
    for k, v in o["traders"].items():
        print(f"{k:55s} ops {v['cerradas']:3d} ({v['por_dia']:.1f}/día) R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
