"""Evaluación histórica de la mesa de fondos (config/fondos_prerregistrada.md). Se ejecuta UNA vez tras el commit del prerregistro.

  python -m src.fondos.evaluar      → reports/fondos_resultados.{json,md}
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.fondos.data import build_history, _splice_spot, RAW, ROOT
from src.fondos import estrategias as E
from src.robustness.stats import deflated_sharpe, sharpe_pp
from src.incubator.factors import trend_factor, regress, holm

N_PRIOR, N_NEW = 251, 10
FULL0 = pd.Timestamp("2018-09-01", tz="UTC")
PER = {"A 2018-09→2019-12": ("2018-09-01", "2020-01-01"), "B 2020-01→2023-12": ("2020-01-01", "2024-01-01"), "C 2024-01→hoy": ("2024-01-01", None)}
CARRY = "F06 Carry de funding (cash-and-carry)"


def sh(r: pd.Series) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(365)) if len(r) > 20 and sd > 0 else 0.0


def p_mean(r: pd.Series, lags: int = 5) -> float:
    """p unilateral de media diaria > 0 con errores HAC (Newey-West)."""
    y = r.dropna().to_numpy()
    if len(y) < 60 or y.std() == 0:
        return 1.0
    m = sm.OLS(y, np.ones(len(y))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return float(1 - st.t.cdf(float(m.tvalues[0]), df=len(y) - 1))


def dd(r: pd.Series) -> float:
    eq = (1 + r).cumprod(); return float((1 - eq / eq.cummax()).max()) if len(eq) else 0.0


def _ts(x) -> pd.Timestamp:
    t = pd.Timestamp(x); return t.tz_localize("UTC") if t.tzinfo is None else t


def cut(r: pd.Series, a, b=None) -> pd.Series:
    r = r[r.index >= _ts(a)]
    return r[r.index < _ts(b)] if b else r


def rp_mix(a: pd.Series, b: pd.Series, win: int = 90) -> pd.Series:
    """50/50 en riesgo: pesos ∝ 1/σ(90 d) decididos a fin de mes, aplicados desde el día siguiente."""
    R = pd.concat([a.rename("a"), b.rename("b")], axis=1).fillna(0.0); sd = R.rolling(win, min_periods=60).std()
    w = (1 / sd.where(sd > 0)).fillna(0.0); w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0)
    me = (R.index + pd.Timedelta("1D")).month != R.index.month
    W = w.where(pd.Series(me, index=R.index)).ffill().shift(1).fillna(0.5)
    return (W * R).sum(axis=1)


def core_daily(d: pd.DataFrame) -> pd.Series:
    """Núcleo v1 (sin tocar) sobre las mismas fechas: contado 4 h + funding real, retornos diarios."""
    from src.core.nucleo import CoreParams, run_core
    from src.backtest.funding import align_funding
    from src.fondos.data import _append_vision
    from src.live.vision_feed import VisionFeed, SPOT
    now = d.index[-1] + pd.Timedelta("1D")
    s4 = pd.read_parquet(RAW / "spot_BTCUSDT_4h.parquet").set_index("time")[["open", "high", "low", "close"]]
    s4 = _splice_spot(_append_vision(s4, VisionFeed(base=SPOT), now)); s4 = s4[s4.index + pd.Timedelta("4h") <= now]
    fr = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")[["time", "funding_rate"]]; fr["time"] = pd.DatetimeIndex(fr["time"]).round("min")
    ev = pd.concat([fr, VisionFeed().funding(fr["time"].max(), now)[["time", "funding_rate"]]]).drop_duplicates("time", keep="last")
    closes = s4.index + pd.Timedelta("4h")
    syn = closes[(closes.hour % 8 == 0) & (closes < pd.Timestamp("2020-01-01", tz="UTC"))]
    ev = pd.concat([pd.DataFrame({"time": syn, "funding_rate": 0.0001}), ev[ev["time"] >= pd.Timestamp("2020-01-01", tz="UTC")]]).sort_values("time")
    ev = ev[(ev["time"] > s4.index[0]) & (ev["time"] <= s4.index[-1] + pd.Timedelta("4h"))]
    eq = run_core(s4, align_funding(s4.index, pd.Timedelta("4h"), ev), CoreParams())["equity"]
    return eq.resample("1D").last().pct_change().dropna()


def evaluate(write: bool = True, d: pd.DataFrame | None = None) -> dict:
    d = build_history() if d is None else d
    res, res2 = E.run_all(d), E.run_all(d, cm=2.0)
    core = core_daily(d).reindex(d.index).fillna(0.0)
    btc = d["close"].pct_change(); tf = trend_factor(d["close"])
    rows = {}
    for k, v in res.items():
        a0 = pd.Timestamp("2020-01-01", tz="UTC") if k == CARRY else FULL0
        r = cut(v["ret"], a0); r2 = cut(res2[k]["ret"], a0); c = cut(core, a0)
        tr = v["trades"]
        ops = int((tr["entrada"] >= a0).sum()) if (k != CARRY and len(tr)) else int(v["n_ops"])   # exposición continua y carry: nº de reajustes
        per = {p: (sh(cut(v["ret"], a, b)) if not (k == CARRY and p.startswith("A")) else None) for p, (a, b) in PER.items()}
        mix = rp_mix(c, r)
        mu, var = float(r.mean()), float(r.var(ddof=1))
        rows[k] = {"sharpe": sh(r), "sharpe_costes_x2": sh(r2), "por_periodo": per, "cagr": float((1 + r).prod() ** (365 / max(len(r), 1)) - 1),
                   "vol_anual": float(r.std(ddof=1) * np.sqrt(365)), "caida_max": dd(r), "ops": ops, "p": p_mean(r),
                   "alfa": regress(r, cut(btc, a0), cut(tf, a0)), "corr_nucleo": float(r.corr(c)),
                   "sharpe_nucleo_mismo_periodo": sh(c), "sharpe_mezcla_50_50_riesgo": sh(cut(mix, a0)),
                   "kelly_completo": mu / var if var > 0 else 0.0, "exposicion_media": float(cut(v["expo"], a0).abs().mean()),
                   "operaciones": (v["trades"][v["trades"]["entrada"] >= a0].assign(entrada=lambda x: x["entrada"].astype(str), salida=lambda x: x["salida"].astype(str)).to_dict("records")[-12:]
                                   if not v["trades"].empty else [])}
    names = list(rows); ph = holm(np.array([rows[k]["p"] for k in names]))
    full = {k: cut(res[k]["ret"], pd.Timestamp("2020-01-01", tz="UTC") if k == CARRY else FULL0) for k in names}
    var_x = float(np.var([sharpe_pp(full[k].to_numpy()) for k in names], ddof=1))
    for i, k in enumerate(names):
        r = rows[k]; r["p_holm"] = float(ph[i]); T = len(full[k])
        # Varianza del Sharpe bajo la nula (1/T, «False Strategy Theorem»): la dispersión entre estas 10 mezcla familias muy distintas
        # (el carry tiene otra escala de Sharpe) y no mide el azar de la selección. La transversal se informa, no decide.
        r["dsr"] = float(deflated_sharpe(full[k].to_numpy(), N_PRIOR + N_NEW, 1.0 / T))
        r["dsr_transversal"] = float(deflated_sharpe(full[k].to_numpy(), N_PRIOR + N_NEW, var_x))
        g = {"C1 Sharpe>0 y p Holm<0,10": r["sharpe"] > 0 and r["p_holm"] < 0.10,
             "C2 Sharpe>0 en cada periodo": all(x is None or x > 0 for x in r["por_periodo"].values()),
             "C3 Sharpe>0 con costes ×2": r["sharpe_costes_x2"] > 0, "C4 DSR≥0,80": r["dsr"] >= 0.80, "C5 ≥30 operaciones": r["ops"] >= 30}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["certificada"] = all(g.values())
        r["aporta_al_nucleo"] = r["sharpe_mezcla_50_50_riesgo"] > r["sharpe_nucleo_mismo_periodo"]
    out = {"datos": [str(d.index[0].date()), str(d.index[-1].date())], "n_pruebas_previas": N_PRIOR, "n_nuevas": N_NEW,
           "referencias": {"nucleo_v1": {"sharpe": sh(cut(core, FULL0)), "caida_max": dd(cut(core, FULL0))},
                           "comprar_y_mantener": {"sharpe": sh(cut(btc.fillna(0), FULL0)), "caida_max": dd(cut(btc.fillna(0), FULL0))}},
           "estrategias": rows, "certificadas": [k for k in names if rows[k]["certificada"]],
           "aportan_al_nucleo": [k for k in names if rows[k]["aporta_al_nucleo"]]}
    if write:
        (ROOT / "reports" / "fondos_resultados.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False))
        (ROOT / "reports" / "fondos_resultados.md").write_text(md(out))
    return out


def md(o: dict) -> str:
    rf = o["referencias"]
    L = [f"# Mesa de fondos · resultados históricos ({o['datos'][0]} → {o['datos'][1]}; evaluación desde 2018-09, carry desde 2020)", "",
         f"Certificadas: **{len(o['certificadas'])}/{len(o['estrategias'])}** · Aportan al núcleo (mezcla 50/50 en riesgo mejora su Sharpe): **{len(o['aportan_al_nucleo'])}**",
         f"Referencias: núcleo v1 Sharpe {rf['nucleo_v1']['sharpe']:.2f} (caída {rf['nucleo_v1']['caida_max']:.0%}); comprar y mantener Sharpe {rf['comprar_y_mantener']['sharpe']:.2f} (caída {rf['comprar_y_mantener']['caida_max']:.0%})", "",
         "| Estrategia | Sharpe | A | B | C | ×2 costes | CAGR | caída | ops | p Holm | DSR | corr. núcleo | mezcla vs núcleo | Kelly | Puertas | Cert. |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda x: "—" if x is None else f"{x:.2f}"
    for k, r in o["estrategias"].items():
        pp = list(r["por_periodo"].values())
        L.append(f"| {k} | {r['sharpe']:.2f} | {f(pp[0])} | {f(pp[1])} | {f(pp[2])} | {r['sharpe_costes_x2']:.2f} | {r['cagr']:+.1%} | {r['caida_max']:.0%} | {r['ops']} | "
                 f"{r['p_holm']:.3f} | {r['dsr']:.2f} | {r['corr_nucleo']:+.2f} | {r['sharpe_mezcla_50_50_riesgo']:.2f} vs {r['sharpe_nucleo_mismo_periodo']:.2f} | "
                 f"{r['kelly_completo']:.1f}× | {sum(r['puertas'].values())}/5 | {'✔' if r['certificada'] else '—'} |")
    L += ["", "Kelly = apalancamiento de Kelly completo sobre el tamaño de la propia estrategia (μ/σ²); se usa como mucho ¼–½ Kelly por la incertidumbre de μ.",
          "Periodos: A 2018-09→2019-12 · B 2020-01→2023-12 · C 2024-01→hoy. p = media diaria > 0 (HAC), Holm sobre las 10."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
