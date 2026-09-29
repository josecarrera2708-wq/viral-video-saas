"""Evaluación ÚNICA del núcleo prerregistrado (config/nucleo_prerregistrado.md).

Solo usa datos hasta 2025-06-30. El periodo ciego (>= 2025-07-01) NO se carga.
Se ejecuta una vez; los criterios de aceptación están fijados en el documento de prerregistro.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.funding import align_funding
from src.core.nucleo import CoreParams, run_core, reference_bh, ewma_vol

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
END = pd.Timestamp("2025-07-01", tz="UTC")          # exclusivo: el ciego no se carga
DELTA = pd.Timedelta("4h")


def load_spot() -> pd.DataFrame:
    d = pd.read_parquet(RAW / "spot_BTCUSDT_4h.parquet").set_index("time")
    d = d[d.index < END][["open", "high", "low", "close", "volume"]]
    # excluir la caída de servidor de feb-2018 y empalmar sin retorno artificial
    a, b = pd.Timestamp("2018-02-08", tz="UTC"), pd.Timestamp("2018-02-11", tz="UTC")
    pre, post = d[d.index < a], d[d.index >= b]
    k = pre["close"].iloc[-1] / post["open"].iloc[0]
    post = post.copy(); post[["open", "high", "low", "close"]] *= k
    d = pd.concat([pre, post])
    full = pd.date_range(d.index[0], d.index[-1], freq="4h", tz="UTC")
    d = d.reindex(full)
    miss = d["close"].isna()
    d["close"] = d["close"].ffill()
    for c in ("open", "high", "low"):
        d[c] = d[c].fillna(d["close"])
    d["volume"] = d["volume"].fillna(0.0)
    return d, int(miss.sum())


def funding_events(idx: pd.DatetimeIndex, real_from="2020-01-01") -> pd.DataFrame:
    """Sintético 0,01 %/8h antes de 2020 (en cierres de vela 00/08/16 UTC); real desde 2020."""
    closes = idx + DELTA
    syn = closes[(closes.hour % 8 == 0) & (closes.minute == 0) & (closes < pd.Timestamp(real_from, tz="UTC"))]
    ev = pd.DataFrame({"time": syn, "funding_rate": 0.0001})
    real = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet")
    real = real[(real["time"] >= pd.Timestamp(real_from, tz="UTC")) & (real["time"] < END)]
    return pd.concat([ev, real[["time", "funding_rate"]]]).sort_values("time")


def daily_ret(eq: pd.Series) -> pd.Series:
    return eq.resample("1D").last().pct_change().dropna()


def sharpe(r: pd.Series) -> float:
    sd = r.std(ddof=1)
    return float(r.mean() / sd * np.sqrt(365)) if sd > 0 else 0.0


def stats(eq: pd.Series) -> dict:
    r = daily_ret(eq); yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    return {"sharpe": sharpe(r), "cagr": float(eq.iloc[-1] ** (1 / yrs) - 1),
            "maxdd": float((1 - eq / eq.cummax()).max()), "total_ret": float(eq.iloc[-1] - 1),
            "worst_day": float(r.min()), "days": int(len(r))}


SUB = {"2017-08→2019-12": ("2017-08-01", "2020-01-01"), "2020-2021": ("2020-01-01", "2022-01-01"),
       "2022": ("2022-01-01", "2023-01-01"), "2023-01→2025-06": ("2023-01-01", "2025-07-01")}


def subperiods(eq: pd.Series) -> dict:
    r = daily_ret(eq); out = {}
    for k, (a, b) in SUB.items():
        x = r[(r.index >= pd.Timestamp(a, tz="UTC")) & (r.index < pd.Timestamp(b, tz="UTC"))]
        out[k] = {"sharpe": sharpe(x), "ret": float((1 + x).prod() - 1), "dd": float((1 - (1 + x).cumprod() / (1 + x).cumprod().cummax()).max())}
    return out


def stationary_bootstrap(cols: dict, S=5000, mean_block=30, seed=0):
    """Remuestreo pareado por bloques (Politis-Romano). cols: dict de arrays alineados."""
    rng = np.random.default_rng(seed)
    n = len(next(iter(cols.values())))
    idx = np.empty((S, n), np.int64)
    idx[:, 0] = rng.integers(0, n, S)
    restart = rng.random((S, n)) < 1 / mean_block
    starts = rng.integers(0, n, (S, n))
    for t in range(1, n):
        idx[:, t] = np.where(restart[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    def sh(x):  # x: (S, n)
        return x.mean(axis=1) / x.std(axis=1, ddof=1) * np.sqrt(365)
    res = {k: sh(v[idx]) for k, v in cols.items()}
    return res


def plateau(df4: pd.DataFrame) -> dict:
    d = df4["close"].resample("1D").last().ffill()
    r = d.pct_change()
    out = {}
    for L in range(10, 301, 10):
        s = (d / d.shift(L) - 1 > 0).astype(float).shift(1)
        x = (s * r).dropna()
        out[L] = sharpe(x)
    v = np.array(list(out.values()))
    best = max(out, key=out.get)
    rest = np.array([x for L, x in out.items() if L != best])
    return {"sharpe_por_horizonte": out, "frac_positivos": float((v > 0).mean()), "mejor_horizonte": best,
            "media_sin_el_mejor": float(rest.mean()), "mediana": float(np.median(v))}


def main():
    df, n_missing = load_spot()
    print(f"spot 4h: {len(df)} velas, {df.index[0]} → {df.index[-1]} | velas rellenadas por huecos: {n_missing}")
    ev = funding_events(df.index)
    fund = align_funding(df.index, DELTA, ev)
    p = CoreParams()
    res = {}
    core = run_core(df, fund, p)
    bh = reference_bh(df, fund, p, vol_targeted=False)
    bhv = reference_bh(df, fund, p, vol_targeted=True)
    res["core"] = stats(core["equity"]); res["bh"] = stats(bh); res["bh_vt"] = stats(bhv)
    half = pd.Series(np.cumprod(1 + 0.5 * df["close"].pct_change().fillna(0.0).to_numpy()), index=df.index)
    res["mitad_bh_mitad_efectivo"] = stats(half)
    res["core_subperiodos"] = subperiods(core["equity"])
    res["bh_vt_subperiodos"] = subperiods(bhv); res["bh_subperiodos"] = subperiods(bh)
    yrs = (df.index[-1] - df.index[0]).days / 365.25
    res["core_operativa"] = {"exposicion_media": float(core["expo"].mean()), "exposicion_max": float(core["expo"].max()),
                             "rotacion_anual": float(core["turn"].sum() / yrs),
                             "funding_pagado_pct_capital": float(core["fund"].sum()),
                             "porcentaje_tiempo_en_mercado": float((core["expo"] > 0.01).mean())}
    # estrés de costes
    st = run_core(df, fund, CoreParams(cost=0.0015))
    res["core_estres_15pb"] = stats(st["equity"])
    # meseta
    res["meseta"] = plateau(df)
    # bootstrap estacionario y alfa
    rc, rb, rv = daily_ret(core["equity"]), daily_ret(bh), daily_ret(bhv)
    j = rc.index.intersection(rb.index).intersection(rv.index)
    boot = stationary_bootstrap({"core": rc[j].to_numpy(), "bh": rb[j].to_numpy(), "bhv": rv[j].to_numpy()})
    q = lambda x: [float(np.percentile(x, 5)), float(np.percentile(x, 50)), float(np.percentile(x, 95))]
    res["bootstrap_sharpe_p5_p50_p95"] = {"core": q(boot["core"]), "bh": q(boot["bh"]), "bh_vt": q(boot["bhv"]),
                                          "core_menos_bh_vt": q(boot["core"] - boot["bhv"]),
                                          "core_menos_bh": q(boot["core"] - boot["bh"])}
    X = sm.add_constant(rb[j].to_numpy()); m = sm.OLS(rc[j].to_numpy(), X).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    res["alfa_vs_bh"] = {"alfa_anual": float(m.params[0] * 365), "t_alfa": float(m.tvalues[0]),
                         "beta": float(m.params[1]), "t_beta": float(m.tvalues[1])}
    X2 = sm.add_constant(rv[j].to_numpy()); m2 = sm.OLS(rc[j].to_numpy(), X2).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
    res["alfa_vs_bh_vt"] = {"alfa_anual": float(m2.params[0] * 365), "t_alfa": float(m2.tvalues[0]), "beta": float(m2.params[1])}
    # comprobación con el perpetuo (2020-01 → 2025-06) y variante F (filtro de funding)
    pd_ = pd.read_parquet(RAW / "perp_BTCUSDT_4h.parquet").set_index("time")
    pd_ = pd_[(pd_.index < END)][["open", "high", "low", "close", "volume"]]
    fund_real = pd.read_parquet(RAW / "perp_BTCUSDT_funding.parquet"); fund_real = fund_real[fund_real["time"] < END]
    fp = align_funding(pd_.index, DELTA, fund_real)
    # percentil 95 móvil de 365 días del último funding liquidado (causal: solo pasado)
    fr = fund_real.set_index("time")["funding_rate"]
    pct = fr.rolling(365 * 3, min_periods=200).apply(lambda x: (x[:-1] < x[-1]).mean(), raw=True)
    flag = pct.reindex(pd_.index + DELTA, method="ffill").to_numpy() >= 0.95
    flag = np.nan_to_num(flag.astype(float)).astype(bool)
    base = run_core(pd_, fp, p)
    var_f = run_core(pd_, fp, CoreParams(fund_filter=True), fund_flag=flag)
    res["perp_2020_core"] = stats(base["equity"]); res["perp_2020_core_F"] = stats(var_f["equity"])
    res["perp_2020_bh_vt"] = stats(reference_bh(pd_, fp, p, vol_targeted=True)); res["perp_2020_bh"] = stats(reference_bh(pd_, fp, p))
    res["perp_F_tiempo_con_filtro_activo"] = float(flag.mean())
    # ---- criterios prerregistrados ----
    c = res["core"]; sp = res["core_subperiodos"]
    crit = {
        "1_sharpe>=0.50": c["sharpe"] >= 0.50,
        "2_sharpe>0_en_3_de_4_subperiodos": sum(v["sharpe"] > 0 for v in sp.values()) >= 3,
        "3_maxdd<=30%": c["maxdd"] <= 0.30,
        "4_meseta_>=80%_y_positiva_sin_el_mejor": res["meseta"]["frac_positivos"] >= 0.80 and res["meseta"]["media_sin_el_mejor"] > 0,
        "5_maxdd<=60%_del_de_bh_vt": c["maxdd"] <= 0.60 * res["bh_vt"]["maxdd"],
        "6_sharpe_estres_15pb>=0.30": res["core_estres_15pb"]["sharpe"] >= 0.30,
    }
    res["criterios"] = crit; res["todos_pasan"] = bool(all(crit.values()))
    dd_rel = 1 - res["perp_2020_core_F"]["maxdd"] / res["perp_2020_core"]["maxdd"]
    cagr_rel = 1 - res["perp_2020_core_F"]["cagr"] / res["perp_2020_core"]["cagr"] if res["perp_2020_core"]["cagr"] > 0 else float("nan")
    res["variante_F"] = {"reduccion_dd_relativa": float(dd_rel), "caida_cagr_relativa": float(cagr_rel),
                         "se_acepta": bool(dd_rel >= 0.10 and cagr_rel <= 0.10)}
    (ROOT / "reports" / "nucleo_resultados.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k not in ("meseta",)}, indent=1, default=str))
    print("meseta:", {k: v for k, v in res["meseta"].items() if k != "sharpe_por_horizonte"})


if __name__ == "__main__":
    main()
