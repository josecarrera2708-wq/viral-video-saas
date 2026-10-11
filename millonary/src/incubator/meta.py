"""Meta-etiquetado con regresión logística y EXAMEN FINAL SELLADO (config/incubadora_prerregistrada.md).

Entrena con las operaciones abiertas en train (2020-2023); umbral fijo 0,5; se ejecuta UNA vez sobre el examen.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.funding import align_funding
from src.core.evaluate_nucleo import load_spot, funding_events, DELTA
from src.signals.indicators import atr, ema, rsi
from src.incubator.setups import all_states
from src.incubator.sim import simulate, simulate_pos, trades, daily
from src.incubator.factors import holm
from src.incubator.evaluate import START, TRAIN_END, ann_sharpe

ROOT = Path(__file__).resolve().parents[2]
MIN_TRAIN_OPS = 40


def features(df: pd.DataFrame) -> pd.DataFrame:
    a = atr(df, 14); c = df["close"]
    return pd.DataFrame({"atr_pct": (a / c).rolling(500, min_periods=100).rank(pct=True),
                         "dist_ema200": (c - ema(c, 200)) / a, "rsi14": rsi(c, 14),
                         "ret10": c.pct_change(10), "hour": df.index.hour.astype(float)}, index=df.index)


def entry_matrix(F: pd.DataFrame, tr: pd.DataFrame) -> pd.DataFrame:
    """Características en la vela de señal (la anterior a la apertura). Firmadas por el lado de la operación."""
    idx = F.index.get_indexer(tr["open"]) - 1
    X = F.iloc[np.clip(idx, 0, len(F) - 1)].copy(); X.index = tr.index
    s = tr["side"].to_numpy()
    X["dist_ema200"] *= s; X["ret10"] *= s
    X["side"] = s
    return X


def boot_p(diff: np.ndarray, block: int = 10, n: int = 4000, seed: int = 0) -> float:
    """p unilateral de que la media de la diferencia diaria sea > 0 (bootstrap de bloques circular, centrado)."""
    rng = np.random.default_rng(seed); T = len(diff); d = diff - diff.mean(); obs = diff.mean(); k = int(np.ceil(T / block)); cnt = 0
    for _ in range(n):
        st_ = rng.integers(0, T, k); ix = ((st_[:, None] + np.arange(block)[None, :]) % T).ravel()[:T]
        cnt += d[ix].mean() >= obs
    return float(cnt / n)


def run(write: bool = True) -> dict:
    df, _ = load_spot(); df = df[df.index >= pd.Timestamp("2019-01-01", tz="UTC")]
    f = align_funding(df.index, DELTA, funding_events(df.index)); S = all_states(df); F = features(df); out = {}
    for k in S:
        base = simulate(df, S[k].to_numpy(), f); tr = trades(base)
        tr_tr = tr[(tr["open"] >= START) & (tr["open"] < TRAIN_END)]
        if len(tr_tr) < MIN_TRAIN_OPS:
            out[k] = {"estado": f"omitido: {len(tr_tr)} ops en train < {MIN_TRAIN_OPS}"}; continue
        Xtr = entry_matrix(F, tr_tr).dropna(); ytr = (tr_tr.loc[Xtr.index, "ret"] > 0).astype(int)
        if ytr.nunique() < 2 or len(Xtr) < MIN_TRAIN_OPS:
            out[k] = {"estado": "omitido: sin variación en la etiqueta"}; continue
        sc = StandardScaler().fit(Xtr); m = LogisticRegression(C=1.0, max_iter=1000).fit(sc.transform(Xtr), ytr)
        tr_ex = tr[tr["open"] >= TRAIN_END]
        Xex = entry_matrix(F, tr_ex); ok = Xex.notna().all(axis=1)
        keep = pd.Series(False, index=tr_ex.index); keep[ok[ok].index] = m.predict_proba(sc.transform(Xex[ok]))[:, 1] > 0.5
        pos = base["pos"].to_numpy().copy()
        for i, row in tr_ex.iterrows():
            if not keep[i]:
                a, b = df.index.get_loc(row["open"]), df.index.get_loc(row["close"])
                pos[a:b + 1] = 0.0
        filt = simulate_pos(df, pos, f)
        d0 = daily(base["ret"]); d1 = daily(filt["ret"]); ex = lambda s: s[s.index >= TRAIN_END]
        diff = (ex(d1) - ex(d0)).to_numpy()
        out[k] = {"ops_train": int(len(tr_tr)), "ops_exam": int(len(tr_ex)), "ops_exam_tomadas": int(keep.sum()),
                  "sharpe_exam_sin_filtro": ann_sharpe(ex(d0)), "sharpe_exam_filtrado": ann_sharpe(ex(d1)),
                  "media_op_sin_filtro": float(tr_ex["ret"].mean()), "media_op_filtrada": float(tr_ex.loc[keep, "ret"].mean()) if keep.any() else float("nan"),
                  "p_boot": boot_p(diff)}
    tested = [k for k, v in out.items() if "p_boot" in v]
    if tested:
        ph = holm(np.array([out[k]["p_boot"] for k in tested]))
        for k, pv in zip(tested, ph):
            out[k]["p_holm"] = float(pv)
            out[k]["gana"] = bool(out[k]["sharpe_exam_filtrado"] > out[k]["sharpe_exam_sin_filtro"] and pv < 0.10)
    res = {"n_probados": len(tested), "ganan": [k for k in tested if out[k]["gana"]], "detalle": out}
    if write:
        (ROOT / "reports" / "incubadora_meta.json").write_text(json.dumps(res, indent=1, default=float))
    return res


if __name__ == "__main__":
    r = run()
    print("probados", r["n_probados"], "ganan", r["ganan"])
    for k, v in r["detalle"].items():
        if "p_boot" in v:
            print(f"{k:36s} ops {v['ops_exam_tomadas']}/{v['ops_exam']}  Sh {v['sharpe_exam_sin_filtro']:.2f} -> {v['sharpe_exam_filtrado']:.2f}  p_boot {v['p_boot']:.2f} p_holm {v['p_holm']:.2f}")
        else:
            print(k, v["estado"])
