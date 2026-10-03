"""Genoma de estrategia v2 -> señales.

Diseño: filtro(s) de régimen + regla de entrada + stop + salida.
Familias de entrada: tendencia (cruces, rupturas, momentum de series temporales, retroceso a la
media), osciladores, price action (barras interiores, NR7, falsas rupturas, retest de
soportes/resistencias, ruptura de estructura, patrones de velas) y todas las series exógenas
(funding, open interest, Fear&Greed, VIX, dólar) como filtros. Todo CAUSAL.
"""
from __future__ import annotations
import hashlib, json, random
import numpy as np
import pandas as pd
from ..backtest.engine import Params, run
from ..backtest.metrics import summarize, BARS_PER_YEAR
from .features import Market, CANDLE_COLS

ENTRY_TYPES = ["ma_cross", "breakout", "rsi_rev", "macd_cross", "boll_rev", "boll_break", "candle",
               "struct_break", "inside_break", "nr7_break", "fakey", "sr_retest", "tsmom", "ma_pullback"]
REGIMES = ["none", "price_sma", "ma_pair", "volpct", "htf", "structure", "fng", "funding", "oi", "vix", "usd"]
CHOICES = {
    "tf": ["4h", "1d"], "side": ["both", "long", "short"],
    "ma_kind": ["sma", "ema"], "fast": [5, 8, 10, 12, 20, 25, 30, 50], "slow": [50, 75, 100, 150, 200, 300],
    "don_n": [10, 20, 30, 50, 100], "rsi_n": [7, 14, 21], "rsi_lo": [20, 25, 30, 35], "rsi_hi": [65, 70, 75, 80],
    "macd": [(12, 26, 9), (8, 21, 5), (24, 52, 18)], "bb_n": [20, 30, 50], "bb_k": [1.5, 2.0, 2.5],
    "candle": CANDLE_COLS, "sw_k": [2, 3, 5, 8],
    "reg_n": [50, 100, 150, 200, 300], "vp_lo": [0.0, 0.2, 0.4], "vp_hi": [0.6, 0.8, 1.0],
    "htf_n": [20, 50, 100, 200], "fng_mode": ["trend", "contra"], "fng_x": [30, 40, 50, 60, 70],
    "fund_q": [0.7, 0.8, 0.9], "oi_days": [1, 3, 7], "oi_sign": [1, -1],
    "vix_mode": ["calm", "stress"], "vix_q": [0.3, 0.5, 0.7], "usd_days": [20, 50],
    "fak_n": [10, 20, 30, 50], "sr_tol": [0.2, 0.4, 0.6], "tsmom_days": [10, 20, 40, 60, 90, 120],
    "pb_fast": [10, 20, 50],
    "atr_n": [14, 21], "atr_k": [1.5, 2.0, 2.5, 3.0, 4.0, 5.0], "stop_kind": ["atr", "swing"],
    "swing_cap": [2.0, 3.0, 5.0], "tp": [0.0, 2.0, 3.0, 4.0, 6.0], "max_bars": [0, 24, 48, 96],
    "exit_opp": [True, False],
}
NUMERIC_GENES = ["fast", "slow", "don_n", "rsi_n", "rsi_lo", "rsi_hi", "bb_n", "bb_k", "reg_n", "vp_lo",
                 "vp_hi", "htf_n", "fng_x", "fund_q", "oi_days", "vix_q", "usd_days", "fak_n", "sr_tol",
                 "tsmom_days", "pb_fast", "atr_n", "atr_k", "swing_cap", "tp", "max_bars", "sw_k"]


def random_genome(rng: random.Random) -> dict:
    g = {k: rng.choice(v) for k, v in CHOICES.items()}
    g["entry"] = rng.choice(ENTRY_TYPES)
    g["regime"] = rng.choice(REGIMES); g["regime2"] = rng.choice(REGIMES)
    return fix_grid(g)


def fix_grid(g: dict) -> dict:
    """Todos los valores en la rejilla y fast < slow."""
    g = dict(g)
    g["fast"] = min(CHOICES["fast"], key=lambda x: abs(x - g["fast"]))
    g["slow"] = min(CHOICES["slow"], key=lambda x: abs(x - g["slow"]))
    if g["fast"] >= g["slow"]:
        smaller = [x for x in CHOICES["fast"] if x < g["slow"]]
        g["fast"] = max(smaller) if smaller else min(CHOICES["fast"])
    return g


def genome_key(g: dict) -> str:
    """Solo los genes que INFLUYEN en la estrategia (colapsa redundancias)."""
    return hashlib.md5(json.dumps(active(g), sort_keys=True, default=str).encode()).hexdigest()[:12]


def _regimes_eff(g: dict) -> list:
    """Lista normalizada de filtros de régimen efectivos (sin duplicados ni inertes)."""
    out = []
    for r in (g["regime"], g.get("regime2", "none")):
        if r == "none": continue
        if r == "ma_pair" and g["entry"] == "ma_cross": continue          # coincide con el propio cruce
        if r == "volpct" and g["vp_lo"] <= 0.0 and g["vp_hi"] >= 1.0: continue
        if r == "htf" and g["tf"] == "1d": r = "price_sma"                # en diario htf == price_sma
        if r not in out: out.append(r)
    return sorted(out)


def _norm_side(g: dict) -> str:
    side, e = g["side"], g["entry"]
    if e == "candle" and side == "both":
        if g["candle"] in ("hammer", "inv_hammer"): return "long"
        if g["candle"] in ("hanging_man", "shooting_star"): return "short"
    return side


def active(g: dict) -> dict:
    regs = _regimes_eff(g)
    a = {"tf": g["tf"], "side": _norm_side(g), "entry": g["entry"], "regimes": regs,
         "stop_kind": g["stop_kind"], "atr_n": g["atr_n"], "tp": g["tp"], "max_bars": g["max_bars"],
         "exit_opp": g["exit_opp"]}
    if g["stop_kind"] == "atr": a["atr_k"] = g["atr_k"]
    else: a.update(sw_k=g["sw_k"], swing_cap=g["swing_cap"])
    e = g["entry"]
    if e == "ma_cross": a.update(ma_kind=g["ma_kind"], fast=g["fast"], slow=g["slow"])
    elif e == "breakout": a["don_n"] = g["don_n"]
    elif e == "rsi_rev": a.update(rsi_n=g["rsi_n"], rsi_lo=g["rsi_lo"], rsi_hi=g["rsi_hi"])
    elif e == "macd_cross": a["macd"] = g["macd"]
    elif e in ("boll_rev", "boll_break"): a.update(bb_n=g["bb_n"], bb_k=g["bb_k"])
    elif e == "candle": a["candle"] = g["candle"]
    elif e == "struct_break": a["sw_k"] = g["sw_k"]
    elif e == "fakey": a["fak_n"] = g["fak_n"]
    elif e == "sr_retest": a.update(sw_k=g["sw_k"], sr_tol=g["sr_tol"])
    elif e == "tsmom": a["tsmom_days"] = g["tsmom_days"]
    elif e == "ma_pullback": a.update(pb_fast=g["pb_fast"], slow=g["slow"])
    for r in regs:
        if r == "price_sma": a["reg_n"] = g["reg_n"] if g["regime"] == "price_sma" or g.get("regime2") == "price_sma" else g["htf_n"]
        elif r == "ma_pair": a.update(ma_kind=g["ma_kind"], fast=g["fast"], slow=g["slow"])
        elif r == "volpct": a.update(vp_lo=g["vp_lo"], vp_hi=g["vp_hi"])
        elif r == "htf": a["htf_n"] = g["htf_n"]
        elif r == "structure": a["sw_k"] = g["sw_k"]
        elif r == "fng": a.update(fng_mode=g["fng_mode"], fng_x=g["fng_x"])
        elif r == "funding": a["fund_q"] = g["fund_q"]
        elif r == "oi": a.update(oi_days=g["oi_days"], oi_sign=g["oi_sign"])
        elif r == "vix": a.update(vix_mode=g["vix_mode"], vix_q=g["vix_q"])
        elif r == "usd": a["usd_days"] = g["usd_days"]
    return a


def _cross_up(a, b): return (a > b) & (a.shift(1) <= b.shift(1))
def _cross_dn(a, b): return (a < b) & (a.shift(1) >= b.shift(1))


def _regime_masks(r: str, g: dict, m: Market):
    """(okL, okS) como Series booleanas (NaN -> False)."""
    c = m.df["close"]
    if r == "price_sma":
        n = g["reg_n"] if g["regime"] == "price_sma" or g.get("regime2") == "price_sma" else g["htf_n"]
        ma = m.sma(n); return c > ma, c < ma
    if r == "ma_pair":
        f = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["fast"])
        s = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["slow"]); return f > s, f < s
    if r == "volpct":
        v = m.volpct(); ok = (v >= g["vp_lo"]) & (v <= g["vp_hi"]); return ok, ok
    if r == "htf":
        ma = m.htf_sma(g["htf_n"]); return c > ma, c < ma
    if r == "structure":
        st = m.structure(g["sw_k"]); return st.up, st.dn
    if r == "fng":
        f = m.ex("fng"); x = g["fng_x"]
        return ((f >= x, f < x) if g["fng_mode"] == "trend" else (f <= x, f > x))
    if r == "funding":
        rk = m.ex_rank("funding", 60); q = g["fund_q"]
        return rk <= q, rk >= 1 - q
    if r == "oi":
        ch = m.ex_chg("oi_value", g["oi_days"]); ok = (ch > 0) if g["oi_sign"] == 1 else (ch < 0); return ok, ok
    if r == "vix":
        rk = m.ex_rank("vix", 250); ok = (rk <= g["vix_q"]) if g["vix_mode"] == "calm" else (rk >= g["vix_q"]); return ok, ok
    if r == "usd":
        ch = m.ex_chg("usd", g["usd_days"]); return ch < 0, ch > 0            # dólar débil favorece largos
    t = pd.Series(True, index=c.index); return t, t


def build_signals(g: dict, m: Market):
    """Devuelve (entry_sig, exit_sig, stop_dist) para toda la serie. CAUSAL."""
    df = m.df; c, o, h, l = df["close"], df["open"], df["high"], df["low"]
    e = g["entry"]
    if e == "ma_cross":
        f = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["fast"])
        s = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["slow"])
        L, S = _cross_up(f, s), _cross_dn(f, s)
    elif e == "breakout":
        d = m.donch(g["don_n"]); L, S = c > d.hh, c < d.ll
        L = L & ~L.shift(1, fill_value=False); S = S & ~S.shift(1, fill_value=False)
    elif e == "rsi_rev":
        r = m.rsi(g["rsi_n"]); L = _cross_up(r, pd.Series(g["rsi_lo"], index=r.index))
        S = _cross_dn(r, pd.Series(g["rsi_hi"], index=r.index))
    elif e == "macd_cross":
        x = m.macd(*g["macd"]); L, S = _cross_up(x.macd, x.signal), _cross_dn(x.macd, x.signal)
    elif e == "boll_rev":
        b = m.boll(g["bb_n"], g["bb_k"]); L, S = _cross_up(c, b.lo), _cross_dn(c, b.up)
    elif e == "boll_break":
        b = m.boll(g["bb_n"], g["bb_k"]); L, S = _cross_up(c, b.up), _cross_dn(c, b.lo)
    elif e == "candle":
        p = m.candles()[g["candle"]]; L, S = p == 1, p == -1
    elif e == "struct_break":
        sb = m.sbreak(g["sw_k"]); L, S = sb.break_up == 1, sb.break_dn == 1
    elif e == "inside_break":
        inside = (h.shift(1) < h.shift(2)) & (l.shift(1) > l.shift(2))
        L, S = inside & (c > h.shift(1)), inside & (c < l.shift(1))
    elif e == "nr7_break":
        rg = (h - l).shift(1); nr = rg <= rg.rolling(7, min_periods=7).min()
        L, S = nr & (c > h.shift(1)), nr & (c < l.shift(1))
    elif e == "fakey":
        d = m.donch(g["fak_n"])
        L = (l.shift(1) < d.ll.shift(1)) & (c > d.ll.shift(1))            # falsa ruptura bajista
        S = (h.shift(1) > d.hh.shift(1)) & (c < d.hh.shift(1))            # falsa ruptura alcista
    elif e == "sr_retest":
        sw = m.swings(g["sw_k"]); a = m.atr(g["atr_n"]); tol = g["sr_tol"] * a
        L = (l <= sw.last_low + tol) & (l >= sw.last_low - tol) & (c > o) & (c > sw.last_low)
        S = (h >= sw.last_high - tol) & (h <= sw.last_high + tol) & (c < o) & (c < sw.last_high)
    elif e == "tsmom":
        n = max(2, g["tsmom_days"] * m.bpd); mom = c / c.shift(n) - 1
        L, S = (mom > 0) & (mom.shift(1) <= 0), (mom < 0) & (mom.shift(1) >= 0)
    else:  # ma_pullback
        ef, sm = m.ema(g["pb_fast"]), m.sma(g["slow"])
        L = (ef > sm) & (l <= ef) & (c > ef) & (c > o)
        S = (ef < sm) & (h >= ef) & (c < ef) & (c < o)
    L0, S0 = L.fillna(False).to_numpy(bool), S.fillna(False).to_numpy(bool)   # señales brutas
    okL = np.ones(len(c), bool); okS = np.ones(len(c), bool)
    for r in _regimes_eff(g):
        a_, b_ = _regime_masks(r, g, m)
        okL &= a_.fillna(False).to_numpy(bool); okS &= b_.fillna(False).to_numpy(bool)
    Lb, Sb = L0 & okL, S0 & okS
    side = _norm_side(g)
    if side == "long": Sb = np.zeros_like(Sb)
    if side == "short": Lb = np.zeros_like(Lb)
    entry = np.where(Lb, 1, np.where(Sb, -1, 0)).astype(np.int8)
    exit_sig = (np.where(L0, 1, np.where(S0, -1, 0)).astype(np.int8) if g["exit_opp"]
                else np.zeros(len(c), np.int8))
    return entry, exit_sig, stop_distance(g, m, entry)


def stop_distance(g: dict, m: Market, entry: np.ndarray) -> np.ndarray:
    """Distancia de stop en precio para cada vela, según la dirección de entrada. CAUSAL."""
    c = m.df["close"]
    a = m.atr(g["atr_n"]).to_numpy()
    if g["stop_kind"] == "atr":
        sd = g["atr_k"] * a
    else:
        sw = m.swings(g["sw_k"]); cl = c.to_numpy()
        d_long = cl - sw.last_low.to_numpy(); d_short = sw.last_high.to_numpy() - cl
        raw = np.where(entry == 1, d_long, d_short)
        sd = np.clip(raw, 0.5 * a, g["swing_cap"] * a)
        sd = np.where(np.isnan(raw), np.nan, sd)
    return np.nan_to_num(sd, nan=0.0)


def n_params(g: dict) -> int:
    a = active(g)
    return len(a) - 6 + max(0, len(a["regimes"]) - 1)


def block_sharpes(eq: np.ndarray, tf: str, k: int = 4) -> list:
    r = np.diff(eq) / np.where(eq[:-1] > 0, eq[:-1], np.nan); r = np.nan_to_num(r)
    ann = BARS_PER_YEAR[tf]; out = []
    for x in np.array_split(r, k):
        sd = x.std()
        out.append(float(x.mean() / sd * np.sqrt(ann)) if sd > 0 else 0.0)
    return out


def evaluate(g: dict, m: Market, a: int, b: int, params: Params | None = None) -> dict:
    """Evalúa el genoma en [a, b). Las señales se calculan con TODA la serie previa (causal)."""
    params = params or Params(capital=1000.0, risk_frac=0.01)
    params = Params(**{**params.__dict__, "max_bars": g["max_bars"], "tp_mult": g["tp"]})
    ent, ex, sd = build_signals(g, m)
    res = run(m.o[a:b], m.h[a:b], m.l[a:b], m.c[a:b], ent[a:b], sd[a:b], params,
              exit_sig=ex[a:b], funding=m.funding[a:b])
    out = summarize(res, m.tf)
    bs = block_sharpes(res["equity"], m.tf)
    out["bsh_mean"] = float(np.mean(bs)); out["bsh_std"] = float(np.std(bs)); out["bsh_min"] = float(np.min(bs))
    out["_res"] = res
    return out
