"""Ciclo de mejora continua (config/mejoras_prerregistrada.md): candidatas de mejora por etapas, siempre en sombra.

  python -m src.lab.mejora build      # E1+E2 (construcción y validación); se ejecuta UNA vez y queda en el registro
  python -m src.lab.mejora update     # E3-E5 con datos hacia delante (lo llama la rutina semanal)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ..backtest.funding import align_funding
from ..incubator.setups import all_states
from ..incubator.sim import simulate, daily
from ..incubator.factors import holm
from ..incubator.meta import boot_p
from ..signals.indicators import ema, atr

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "reports" / "mejoras_registro.json"
H4 = pd.Timedelta("4h")
TRAIN_START, TRAIN_END = pd.Timestamp("2020-01-01", tz="UTC"), pd.Timestamp("2024-01-01", tz="UTC")
MIN_DELTA_TRAIN, MIN_DAYS, MIN_DELTA_ADOPT, DD_RATIO = 0.15, 90, 0.30, 1.2


# ---- operadores (estado deseado al cierre de la vela i, causal) --------------------------------------------------
def o1_f200(df, s):
    e = ema(df["close"], 200); c = df["close"]
    return np.where((s > 0) & (c > e), 1.0, np.where((s < 0) & (c < e), -1.0, 0.0))


def o2_solo_largos(df, s):
    return np.where(s > 0, s, 0.0)


def o3_tamano_vol(df, s):
    sig = df["close"].pct_change().ewm(span=45 * 6, min_periods=60).std() * np.sqrt(6 * 365.25)
    return s * np.clip(0.25 / sig.replace(0, np.nan), 0.25, 2.0).fillna(0.0).to_numpy()


def o4_stop_chandelier(df, s, mult=3.0):
    c = df["close"].to_numpy(); a = atr(df, 14).to_numpy(); out = np.zeros(len(s)); cur = 0.0; ext = 0.0; blocked = 0.0
    for i in range(len(s)):
        raw = s[i]
        if blocked != 0.0 and raw != blocked: blocked = 0.0             # una señal distinta libera el bloqueo
        want = 0.0 if blocked != 0.0 else raw
        if want != cur:
            cur = want; ext = c[i]
        elif cur != 0.0 and not np.isnan(a[i]):
            ext = max(ext, c[i]) if cur > 0 else min(ext, c[i])
            if (cur > 0 and c[i] < ext - mult * a[i]) or (cur < 0 and c[i] > ext + mult * a[i]):
                blocked = cur; cur = 0.0
        out[i] = cur
    return out


def o5_canal(df, s):
    hh = df["high"].rolling(20).max(); ll = df["low"].rolling(20).min()
    p = ((df["close"] - ll) / (hh - ll).replace(0, np.nan)).to_numpy()
    return np.where((s > 0) & (p > 2 / 3), 1.0, np.where((s < 0) & (p < 1 / 3), -1.0, 0.0))


OPERADORES = {"O1 filtro EMA200": o1_f200, "O2 solo largos": o2_solo_largos, "O3 tamaño por volatilidad": o3_tamano_vol,
              "O4 stop 3×ATR": o4_stop_chandelier, "O5 parte fuerte del canal": o5_canal}


def _sh(d: pd.Series) -> float:
    sd = d.std(ddof=1)
    return float(d.mean() / sd * np.sqrt(365)) if len(d) > 10 and sd > 0 else 0.0


def _dd(d: pd.Series) -> float:
    eq = (1 + d).cumprod(); return float((1 - eq / eq.cummax()).max()) if len(eq) else 0.0


def _load():
    from ..core.evaluate_nucleo import load_spot, funding_events, DELTA
    df, _ = load_spot(); df = df[df.index >= pd.Timestamp("2019-01-01", tz="UTC")]
    return df, align_funding(df.index, DELTA, funding_events(df.index))


def build(force: bool = False, ledger: Path = LEDGER) -> dict:
    if ledger.exists() and not force:
        return json.loads(ledger.read_text())
    df, f = _load(); S = all_states(df); cand = {}
    ex = lambda s: s[s.index >= TRAIN_END]; tr = lambda s: s[(s.index >= TRAIN_START) & (s.index < TRAIN_END)]
    for k in S:
        base = daily(simulate(df, S[k].to_numpy(), f)["ret"]); s0 = S[k].to_numpy()
        for on, fn in OPERADORES.items():
            v = daily(simulate(df, np.asarray(fn(df, s0), float), f)["ret"])
            d_tr = _sh(tr(v)) - _sh(tr(base)); d_ex = _sh(ex(v)) - _sh(ex(base))
            diff = (ex(v) - ex(base)).to_numpy()
            cand[f"{k}|{on}"] = {"trader": k, "operador": on, "delta_train": d_tr, "delta_exam": d_ex, "p_boot_exam": boot_p(diff, n=2000),
                                 "caida_exam_base": _dd(ex(base)), "caida_exam_var": _dd(ex(v)),
                                 "etapa": "E3 sombra" if (d_tr >= MIN_DELTA_TRAIN and d_ex > 0) else "descartada (E1/E2)"}
    keys = list(cand); ph = holm(np.array([cand[k]["p_boot_exam"] for k in keys]))
    for k, p in zip(keys, ph): cand[k]["p_holm_exam"] = float(p)
    led = {"creado": str(pd.Timestamp.now(tz="UTC")), "n_pruebas": len(cand), "operadores": list(OPERADORES),
           "en_sombra": [k for k in keys if cand[k]["etapa"] == "E3 sombra"], "candidatas": cand, "historial": []}
    ledger.write_text(json.dumps(led, indent=1, default=float)); return led


def _fwd_ret(df, state, f, start):
    r = simulate(df, state, f)["ret"]; closes = df.index + H4
    live = np.asarray(closes >= pd.Timestamp(start)); st = np.where(live, state, 0.0)
    r = simulate(df, st, f)["ret"]
    return daily(r[np.asarray(closes > pd.Timestamp(start))])


def update(bars: pd.DataFrame, funding_events: pd.DataFrame | None, start: pd.Timestamp | None, now: pd.Timestamp | None = None,
           ledger: Path = LEDGER) -> dict:
    """Actualiza E3-E5 de las candidatas en sombra. Nunca toca capital."""
    led = build(ledger=ledger)
    if start is None or len(bars) < 600:
        return led
    f = align_funding(bars.index, H4, funding_events) if funding_events is not None and len(funding_events) else np.zeros(len(bars))
    S = all_states(bars); shadow = led["en_sombra"]; stats = {}
    for key in shadow:
        c = led["candidatas"][key]; s0 = S[c["trader"]].to_numpy(); fn = OPERADORES[c["operador"]]
        b = _fwd_ret(bars, s0, f, start); v = _fwd_ret(bars, np.asarray(fn(bars, s0), float), f, start)
        n = min(len(b), len(v)); b, v = b.iloc[-n:], v.iloc[-n:]
        diff = (v - b).to_numpy(); stats[key] = {"dias": n, "delta_sharpe": _sh(v) - _sh(b) if n >= 10 else None,
                                                  "caida_base": _dd(b), "caida_var": _dd(v), "ret_base": float((1 + b).prod() - 1), "ret_var": float((1 + v).prod() - 1),
                                                  "p_boot": boot_p(diff, n=2000) if n >= MIN_DAYS else None}
    ready = [k for k, v in stats.items() if v["dias"] >= MIN_DAYS and v["p_boot"] is not None]
    if ready:
        ph = holm(np.array([stats[k]["p_boot"] for k in ready]))
        for k, p in zip(ready, ph): stats[k]["p_holm"] = float(p)
    for k, v in stats.items():
        c = led["candidatas"][k]
        if v["dias"] < MIN_DAYS: c["etapa"] = "E3 sombra"
        elif v["delta_sharpe"] is not None and v["delta_sharpe"] <= 0: c["etapa"] = "E5 retirada"
        elif (v["delta_sharpe"] >= MIN_DELTA_ADOPT and v["caida_var"] <= DD_RATIO * max(v["caida_base"], 1e-9) and v.get("p_holm", 1) < 0.10): c["etapa"] = "E4 adoptable"
        else: c["etapa"] = "E3 sombra (sin cumplir E4 aún)"
        c["forward"] = v
    led["ultima_actualizacion"] = str(now or pd.Timestamp.now(tz="UTC"))
    led.setdefault("historial", []).append({"fecha": led["ultima_actualizacion"][:10], "etapas": {k: v["etapa"] for k, v in led["candidatas"].items() if k in shadow}})
    led["historial"] = led["historial"][-60:]
    ledger.write_text(json.dumps(led, indent=1, default=float)); return led


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        led = build(); c = led["candidatas"]
        print("pruebas", led["n_pruebas"], "en sombra", len(led["en_sombra"]))
        for k in led["en_sombra"]:
            print(f"{k:50s} Δtrain {c[k]['delta_train']:+.2f} Δexam {c[k]['delta_exam']:+.2f} p_holm {c[k]['p_holm_exam']:.2f} caída {c[k]['caida_exam_base']:.0%}->{c[k]['caida_exam_var']:.0%}")
