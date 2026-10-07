"""Búsqueda v13 swing 1-3 días (config/busqueda_v13_prerregistrada.md). Ejecución única:  python -m src.busqueda.evaluate_v13
Mismo motor que evaluate_v12 con barreras de swing (src/busqueda/v13.py).
Walk-forward anclado por trimestres: entrena con todo lo anterior (purgando etiquetas que acaban dentro de la prueba), predice el trimestre.
3 configuraciones × 4 modelos (logística, boosting, bosque, media) = 12 pruebas. Puertas G0-G6 sobre la MEDIA de los 3 modelos."""
from __future__ import annotations
import hashlib
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
from ..robustness.stats import deflated_sharpe
from . import intradia5 as I
from . import v13 as M
from .sim5 import Costes

D0, D1 = "2020-10-01", I.END
WF0 = "2022-10-01"
N_TRIALS = 300 + 24
PRE = ("2017-10-01", "2019-12-31"); PRE_FUERA = ("2018-02-08", "2018-02-12")
OUT = I.ROOT / "reports"; MOD = I.ROOT / "models" / "v13"
SEED = 12


def modelos() -> dict:
    cal = lambda m: CalibratedClassifierCV(m, method="isotonic", cv=KFold(3, shuffle=False))
    return {"logistica": cal(LogisticRegression(C=0.1, max_iter=3000)),
            "boosting": cal(HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=400, early_stopping=True, min_samples_leaf=200,
                                                           l2_regularization=1.0, random_state=SEED)),
            "bosque": cal(RandomForestClassifier(n_estimators=300, max_depth=6, min_samples_leaf=100, max_samples=0.5, n_jobs=-1, random_state=SEED))}


def _prep(X, pr):
    Z = (X.fillna(pr["med"]) - pr["mu"]) / pr["sd"]
    return Z.fillna(0.0).to_numpy()


def ajustar(X, y, w) -> dict:
    """Mediana para huecos y estandarización con los datos de ENTRENAMIENTO (sin Pipeline, para que los pesos lleguen a cada modelo)."""
    med = X.median(); mu = X.fillna(med).mean(); sd = X.fillna(med).std().replace(0, 1.0).fillna(1.0)
    out = {"_prep": {"med": med, "mu": mu, "sd": sd}}; Z = _prep(X, out["_prep"])
    for k, m in modelos().items():
        m.fit(Z, y, sample_weight=w); out[k] = m
    return out


def predecir(ms: dict, X) -> dict:
    Z = _prep(X, ms["_prep"])
    p = {k: m.predict_proba(Z)[:, 1] for k, m in ms.items() if k != "_prep"}; p["media"] = np.mean(list(p.values()), axis=0)
    return p


def datos(b5, f5, ev, gemelo=False, x2=True) -> dict:
    """Eventos con barrera, variables y etiquetas (neta, bruta y a costes ×2) de cada configuración."""
    s = M.barrera(b5, ev); ok = np.isfinite(s); ev = ev[ok].reset_index(drop=True); s = s[ok]
    X = M.variables(b5, ev, s, gemelo=gemelo); lab = {}
    for c, g in M.CONFIGS.items():
        net = M.etiquetas(b5, f5, ev, s, g); br = M.etiquetas(b5, f5, ev, s, g, M.COSTE_CERO)
        lab[c] = {"R": net["R"].to_numpy(), "salida": net["salida"], "bruta": br["R"].to_numpy(), "motivo": net["motivo"].to_numpy(),
                  "x2": M.etiquetas(b5, f5, ev, s, g, Costes().x(2.0))["R"].to_numpy() if x2 else None}
    return {"ev": ev, "s": s, "X": X, "lab": lab}


def _lu(g) -> float:
    return g.b + g.m * (g.b - g.a) if g.modo == 1 else 1.0


def trimestres():
    q = pd.date_range(WF0, D1, freq="QS-OCT", tz="UTC").union(pd.DatetimeIndex([pd.Timestamp(WF0, tz="UTC")]))
    q = q[q >= pd.Timestamp(WF0, tz="UTC")]
    return list(zip(q, list(q[1:]) + [pd.Timestamp(D1, tz="UTC")]))


def walk_forward(Dt: dict, conf: str, barajar: bool = False) -> pd.DataFrame:
    """Probabilidades fuera de muestra de cada evento del periodo 2022-10 → fin, con reentreno trimestral."""
    ev, X, L = Dt["ev"], Dt["X"], Dt["lab"][conf]; g = M.CONFIGS[conf]
    t = pd.DatetimeIndex(ev["t"]); sal = pd.DatetimeIndex(L["salida"]); R = L["R"]; ok = np.isfinite(R)
    y = (R > 0).astype(int)
    if barajar:                                                          # G0: etiquetas barajadas por días
        rng = np.random.default_rng(SEED); day = t.floor("D"); u = day.unique(); perm = dict(zip(u, rng.permutation(u)))
        src = pd.Series(np.arange(len(t)), index=day); y2 = y.copy()
        for d0, d1 in perm.items():
            a = src.loc[[d0]].to_numpy(); b = src.loc[[d1]].to_numpy()
            y2[a] = y[b[np.arange(len(a)) % len(b)]]
        y = y2
    rows = []
    for a, b in trimestres():
        tr = ok & (t >= pd.Timestamp(D0, tz="UTC")) & (sal < a)
        te = ok & (t >= a) & (t < b)
        if te.sum() == 0: continue
        w = M.pesos_unicidad(ev["t"][tr], L["salida"][tr])
        ms = ajustar(X[tr], y[tr], w); P = predecir(ms, X[te])
        W, Lm = M.wl(L["bruta"][tr]); pb = float(np.average(y[tr], weights=w))
        df = pd.DataFrame({"t": t[te], "trimestre": str(a.date()), "y": y[te], "R": R[te], "x2": L["x2"][te], "salida": sal[te], "d": ev["d"][te].to_numpy(),
                           "tf": ev["tf"][te].to_numpy(), "stop_pct": X["stop_pct"][te].to_numpy(), "coste_R": X["coste_R"][te].to_numpy()})
        for k, p in P.items():
            df["p_" + k] = p
            df["ev_" + k] = M.ev_neto(p, W, Lm, df["coste_R"].to_numpy(), _lu(g))
            df["riesgo_" + k] = M.riesgo_kelly(p, pb, W, Lm)
        df["W"] = W; df["L"] = Lm; df["p_base"] = pb; df["brier_base"] = np.mean((pb - y[te]) ** 2)
        rows.append(df)
    return pd.concat(rows, ignore_index=True)


# ---------------- estadística ----------------
def t_dia(t, R) -> float:
    """t de la media de R agrupando por día (las operaciones del mismo día no son independientes)."""
    R = np.asarray(R, float); n = len(R)
    if n < 3: return 0.0
    m = R.mean(); g = pd.Series(R - m, index=pd.DatetimeIndex(t).floor("D")).groupby(level=0).sum()
    se = np.sqrt((g ** 2).sum()) / n
    return float(m / se) if se > 0 else 0.0


def boot_semanas(t_a, R_a, take, reps=2000) -> float:
    """p de que E[R] filtrada ≤ E[R] de tomar todas (bootstrap por semanas)."""
    w = pd.DatetimeIndex(t_a).floor("D") - pd.to_timedelta(pd.DatetimeIndex(t_a).dayofweek, unit="D")
    df = pd.DataFrame({"w": w, "Ra": R_a, "na": 1.0, "Rt": np.where(take, R_a, 0.0), "nt": take.astype(float)}).groupby("w").sum().to_numpy()
    rng = np.random.default_rng(SEED); k = len(df); out = np.empty(reps)
    for i in range(reps):
        s = df[rng.integers(0, k, k)].sum(0)
        out[i] = (s[2] / s[3] if s[3] > 0 else 0.0) - s[0] / s[1]
    return float((out <= 0).mean())


def diario(t, R, a, b) -> np.ndarray:
    idx = pd.date_range(a, b, freq="D", tz="UTC")
    return pd.Series(R, index=pd.DatetimeIndex(t).floor("D")).groupby(level=0).sum().reindex(idx, fill_value=0.0).to_numpy()


def resumen(df: pd.DataFrame, k: str) -> dict:
    tk = df["ev_" + k].to_numpy() >= M.EV_MIN; x = df[tk]; R = x["R"].to_numpy(); n = len(x)
    years = (pd.Timestamp(D1, tz="UTC") - pd.Timestamp(WF0, tz="UTC")).days / 365.25
    sin_ex = x[x["t"] < pd.Timestamp("2025-07-01", tz="UTC")]["R"]
    win = R[R > 0]; los = R[R <= 0]
    be = (-los.mean()) / (win.mean() - los.mean()) if len(win) and len(los) else 1.0
    q = x.groupby("trimestre")["R"].mean().reindex(df["trimestre"].unique()).fillna(0.0)
    tt = t_dia(x["t"], R); m = R.mean() if n else 0.0
    return {"n": n, "ops_año": n / years, "tomadas": float(tk.mean()), "acierto": float((R > 0).mean()) if n else 0.0, "empate": float(be),
            "R_media": float(m), "t_dia": tt, "cota95": float(m - 1.645 * (m / tt)) if tt else 0.0,
            "R_sin_2025_07": float(sin_ex.mean()) if len(sin_ex) else 0.0, "trimestres_pos": int((q > 0).sum()), "trimestres": int(len(q)),
            "R_x2": float(x["x2"].mean()) if n else 0.0,
            "auc": float(roc_auc_score(df["y"], df["p_" + k])), "brier_skill": float(1 - np.mean((df["p_" + k] - df["y"]) ** 2) / df["brier_base"].mean()),
            "todas_n": len(df), "todas_acierto": float((df["R"] > 0).mean()), "todas_R": float(df["R"].mean())}


def evaluate(write=True) -> dict:
    b5, f5 = I.load5()
    sig = M.señales(b5); ev = M.agrupar(sig)
    ev = ev[(ev["t"] >= pd.Timestamp(D0, tz="UTC")) & (ev["t"] < pd.Timestamp(D1, tz="UTC"))].reset_index(drop=True)
    Dt = datos(b5, f5, ev); res = {}; wf = {}; daily = {}
    for c in M.CONFIGS:
        wf[c] = walk_forward(Dt, c)
        for k in ("logistica", "boosting", "bosque", "media"):
            r = res[f"{c} | {k}"] = resumen(wf[c], k)
            tk = wf[c]["ev_" + k] >= M.EV_MIN
            daily[f"{c} | {k}"] = diario(wf[c]["t"][tk], wf[c]["R"][tk], WF0, D1)
    var_sr = float(np.var([x.mean() / x.std(ddof=1) for x in daily.values() if x.std() > 0]))
    g0 = walk_forward(Dt, "C1 2R", barajar=True); auc0 = float(roc_auc_score(g0["y"], g0["p_media"]))
    r0 = resumen(g0, "media"); G0 = auc0 <= 0.52 and not (r0["R_media"] > r0["todas_R"] + 0.02)
    for c in M.CONFIGS:
        r = res[f"{c} | media"]; df = wf[c]; tk = (df["ev_media"] >= M.EV_MIN).to_numpy()
        r["p_vs_todas"] = boot_semanas(df["t"], df["R"].to_numpy(), tk)
        dd = daily[f"{c} | media"]; sr = dd.mean() / dd.std(ddof=1) if dd.std() > 0 else 0.0
        r["dsr"] = deflated_sharpe(dd, N_TRIALS, var_sr); r["sharpe_anual"] = float(sr * np.sqrt(365))
        g = {"G0 técnico (barajado AUC≤0,52)": G0,
             "G1 n≥400, t≥3, R>0 sin 2025-07→": r["n"] >= 400 and r["t_dia"] >= 3.0 and r["R_sin_2025_07"] > 0,
             "G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3": r["p_vs_todas"] < 0.10 and r["acierto"] >= r["empate"] + 0.03,
             "G3 ≥10/16 trimestres positivos": r["trimestres_pos"] >= 10,
             "G4 R>0 a costes ×2": r["R_x2"] > 0,
             "G5 DSR≥0,95": r["dsr"] >= 0.95,
             "G6 ≥100 ops/año y Sharpe<5": r["ops_año"] >= 100 and r["sharpe_anual"] < 5}
        r["puertas"] = {a: bool(b) for a, b in g.items()}; r["pasa"] = all(g.values())
        ops = df[tk].assign(riesgo=df["riesgo_media"][tk], lu=_lu(M.CONFIGS[c]))
        r["cartera"] = cartera_resumen(M.cartera(ops))
    pasan = sorted([c for c in M.CONFIGS if res[f"{c} | media"]["pasa"]], key=lambda c: -res[f"{c} | media"]["cota95"])
    out = {"eventos_D": len(Dt["ev"]), "auc_barajado": auc0, "G0": bool(G0), "var_sr": var_sr, "resultados": res,
           "elegida": pasan[0] if pasan else None}
    if pasan and write:
        out["congelado"] = congelar(Dt, pasan[0]); out["premuestra"] = premuestra(pasan[0])
    if write:
        (OUT / "busqueda_v13_resultados.json").write_text(json.dumps(out, indent=1, default=float, ensure_ascii=False))
        (OUT / "busqueda_v13_resultados.md").write_text(md(out))
        for c in M.CONFIGS:
            (I.ROOT / "data" / "cache" / "v13").mkdir(parents=True, exist_ok=True)
            wf[c].to_parquet(I.ROOT / "data" / "cache" / "v13" / f"wf_{c[:2]}.parquet")
    return out


def cartera_resumen(p: pd.DataFrame, capital=1000.0) -> dict:
    if not len(p): return {"ops": 0}
    eq = p.sort_values("salida").set_index("salida")["capital"]; eq = pd.concat([pd.Series([capital]), eq.reset_index(drop=True)])
    m = p.assign(mes=pd.DatetimeIndex(p["salida"]).strftime("%Y-%m")).groupby("mes")["pnl"].sum()
    cap_ini = capital + p.sort_values("salida")["pnl"].cumsum().shift(1).fillna(0.0)
    mens = (p.sort_values("salida").assign(r=lambda x: x["pnl"] / cap_ini.values, mes=lambda x: pd.DatetimeIndex(x["salida"]).strftime("%Y-%m"))
            .groupby("mes")["r"].sum())
    return {"ops": len(p), "capital_final": float(eq.iloc[-1]), "caida_max": float((1 - eq / eq.cummax()).max()),
            "mes_medio": float(mens.mean()), "mes_mediano": float(mens.median()), "meses_neg": int((mens < 0).sum()), "meses": int(len(mens)),
            "apal_medio": {tf: float(x["apal"].mean()) for tf, x in p.groupby("tf")}, "apal_max": float(p["apal"].max()), "riesgo_medio": float(p["riesgo"].mean())}


def congelar(Dt: dict, conf: str) -> dict:
    """Reentrena con TODO D y congela (pickle + sha256)."""
    MOD.mkdir(parents=True, exist_ok=True); L = Dt["lab"][conf]; ok = np.isfinite(L["R"]); y = (L["R"] > 0).astype(int)
    w = M.pesos_unicidad(Dt["ev"]["t"][ok], L["salida"][ok]); ms = ajustar(Dt["X"][ok], y[ok], w)
    W, Lm = M.wl(L["bruta"][ok]); obj = {"conf": conf, "modelos": ms, "W": W, "L": Lm, "p_base": float(np.average(y[ok], weights=w)),
                                            "columnas": list(Dt["X"].columns)}
    b = pickle.dumps(obj); (MOD / "modelo.pkl").write_bytes(b); h = hashlib.sha256(b).hexdigest()
    (MOD / "modelo.sha256").write_text(h + "\n")
    return {"conf": conf, "sha256": h, "W": W, "L": Lm}


def premuestra(conf: str) -> dict:
    """Gemelo (solo precio, volumen y flujo taker; sin setups de OI/prima) entrenado con todo D y aplicado UNA vez a 2017-10→2019-12 (contado)."""
    b5, f5 = I.load5(); g = M.CONFIGS[conf]
    ev = M.agrupar(M.señales(b5, con_oi=False))
    ev = ev[(ev["t"] >= pd.Timestamp(D0, tz="UTC")) & (ev["t"] < pd.Timestamp(D1, tz="UTC"))].reset_index(drop=True)
    Dt = datos(b5, f5, ev, gemelo=True, x2=False); L = Dt["lab"][conf]; ok = np.isfinite(L["R"]); y = (L["R"] > 0).astype(int)
    ms = ajustar(Dt["X"][ok], y[ok], M.pesos_unicidad(Dt["ev"]["t"][ok], L["salida"][ok])); W, Lm = M.wl(L["bruta"][ok])
    p5 = pd.read_parquet(I.RAW / "spot_BTCUSDT_5m_2017_2019.parquet").set_index("time")[I.COLS]; p5.index = p5.index.astype("datetime64[ns, UTC]")
    pf = np.zeros(len(p5)); evp = M.agrupar(M.señales(p5, con_oi=False)); t = evp["t"]
    evp = evp[(t >= pd.Timestamp(PRE[0], tz="UTC")) & (t < pd.Timestamp(PRE[1], tz="UTC")) &
              ~((t >= pd.Timestamp(PRE_FUERA[0], tz="UTC")) & (t < pd.Timestamp(PRE_FUERA[1], tz="UTC")))].reset_index(drop=True)
    P = datos(p5, pf, evp, gemelo=True, x2=False); Lp = P["lab"][conf]; okp = np.isfinite(Lp["R"])
    p = predecir(ms, P["X"][okp])["media"]; e = M.ev_neto(p, W, Lm, P["X"]["coste_R"][okp].to_numpy(), _lu(g)); tk = e >= M.EV_MIN
    R = Lp["R"][okp][tk]; tt = pd.DatetimeIndex(P["ev"]["t"][okp][tk])
    w = tt.floor("D") - pd.to_timedelta(tt.dayofweek, unit="D"); wk = pd.Series(R, index=w).groupby(level=0).agg(["sum", "count"]).to_numpy()
    rng = np.random.default_rng(SEED); bs = np.array([(lambda s: s[0] / s[1])(wk[rng.integers(0, len(wk), len(wk))].sum(0)) for _ in range(2000)]) if len(wk) else np.zeros(1)
    m = float(R.mean()) if len(R) else 0.0; pval = float((bs <= 0).mean())
    veredicto = "falsado" if m <= -0.05 else ("apoyo" if m > 0 and pval < 0.05 else "no concluyente")
    return {"n": int(len(R)), "acierto": float((R > 0).mean()) if len(R) else 0.0, "R_media": m, "p": pval, "veredicto": veredicto,
            "todas_n": int(okp.sum()), "todas_R": float(np.nanmean(Lp["R"][okp]))}


def md(o) -> str:
    L = ["# Búsqueda v13 · swing 1-3 días con filtro estadístico", "",
         f"Eventos en desarrollo (2020-10→2026-09): **{o['eventos_D']}** · G0 (etiquetas barajadas): AUC {o['auc_barajado']:.3f} → {'OK' if o['G0'] else 'FALLA'}", "",
         "## Fuera de muestra (walk-forward trimestral 2022-10→2026-09), riesgo unitario", "",
         "| Configuración · modelo | Tomadas | Ops/año | Acierto | Empate | R media | t (día) | Trim. + | ×2 costes | AUC | Brier skill |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k, r in o["resultados"].items():
        L.append(f"| {k} | {r['tomadas']:.0%} | {r['ops_año']:.0f} | {r['acierto']:.0%} | {r['empate']:.0%} | {r['R_media']:+.3f} | {r['t_dia']:.2f} | "
                 f"{r['trimestres_pos']}/{r['trimestres']} | {r['R_x2']:+.3f} | {r['auc']:.3f} | {r['brier_skill']:+.3f} |")
    L += ["", "Referencia «tomar todas»: " + " · ".join(f"{c}: {o['resultados'][c + ' | media']['todas_n']} ops, acierto {o['resultados'][c + ' | media']['todas_acierto']:.0%}, "
                                                     f"R {o['resultados'][c + ' | media']['todas_R']:+.3f}" for c in M.CONFIGS), "",
          "## Puertas (media de los 3 modelos)", ""]
    for c in M.CONFIGS:
        r = o["resultados"][c + " | media"]
        L.append(f"**{c}** — {sum(r['puertas'].values())}/7 · p frente a tomar todas {r['p_vs_todas']:.3f} · DSR {r['dsr']:.2f} · Sharpe anual {r['sharpe_anual']:.2f}")
        L += [f"- {'✅' if v else '❌'} {a}" for a, v in r["puertas"].items()]
        cp = r["cartera"]
        if cp.get("ops"):
            L.append(f"- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento 3x (≤2 h) / 2x (4 h)): {cp['ops']} ops, "
                     f"final {cp['capital_final']:.0f} USDT, mes medio {cp['mes_medio']:+.1%} (mediana {cp['mes_mediano']:+.1%}), meses negativos {cp['meses_neg']}/{cp['meses']}, "
                     f"caída máx. {cp['caida_max']:.0%}, riesgo medio {cp['riesgo_medio']:.2%}, apalancamiento medio " +
                     ", ".join(f"{tf} {v:.1f}x" for tf, v in cp["apal_medio"].items()) + f" (máx. {cp['apal_max']:.1f}x)")
        L.append("")
    L += ["## Decisión", "", f"- Elegida: **{o['elegida'] or 'ninguna'}**"]
    if o.get("congelado"): L.append(f"- Modelo congelado: sha256 `{o['congelado']['sha256']}`")
    if o.get("premuestra"):
        p = o["premuestra"]; L.append(f"- Pre-muestra 2017-10→2019-12 (gemelo): {p['n']} ops, acierto {p['acierto']:.0%}, R {p['R_media']:+.3f}, p {p['p']:.3f} → **{p['veredicto']}**")
    if not o["elegida"]: L.append("- Ninguna configuración pasa todas las puertas: no hay papel (regla prerregistrada).")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    o = evaluate(); print(md(o))
