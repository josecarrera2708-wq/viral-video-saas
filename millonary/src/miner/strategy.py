"""Genoma de estrategia -> señales. Diseño: filtro de régimen + regla de entrada + stop + salida."""
from __future__ import annotations
import hashlib, json, random
import numpy as np
import pandas as pd
from ..backtest.engine import Params, run
from ..backtest.metrics import summarize
from .features import Market, CANDLE_COLS

ENTRY_TYPES = ["ma_cross", "breakout", "rsi_rev", "macd_cross", "boll_rev", "boll_break",
               "candle", "struct_break"]
REGIMES = ["none", "price_sma", "ma_pair", "volpct"]
CHOICES = {
    "tf": ["1h", "4h"], "side": ["both", "long", "short"],
    "ma_kind": ["sma", "ema"], "fast": [5, 8, 10, 12, 20, 25, 30, 50], "slow": [50, 75, 100, 150, 200, 300],
    "don_n": [10, 20, 30, 50, 100], "rsi_n": [7, 14, 21], "rsi_lo": [20, 25, 30, 35], "rsi_hi": [65, 70, 75, 80],
    "macd": [(12, 26, 9), (8, 21, 5), (24, 52, 18)], "bb_n": [20, 30, 50], "bb_k": [1.5, 2.0, 2.5],
    "candle": CANDLE_COLS, "sw_k": [2, 3, 5, 8],
    "reg_n": [50, 100, 150, 200, 300], "vp_lo": [0.0, 0.2, 0.4], "vp_hi": [0.6, 0.8, 1.0],
    "atr_n": [14, 21], "atr_k": [1.0, 1.5, 2.0, 2.5, 3.0, 4.0], "stop_kind": ["atr", "swing"],
    "swing_cap": [2.0, 3.0, 5.0], "tp": [0.0, 1.5, 2.0, 3.0, 4.0], "max_bars": [0, 12, 24, 48, 96],
    "exit_opp": [True, False],
}


def random_genome(rng: random.Random) -> dict:
    g = {k: rng.choice(v) for k, v in CHOICES.items()}
    g["entry"] = rng.choice(ENTRY_TYPES); g["regime"] = rng.choice(REGIMES)
    if g["fast"] >= g["slow"]:
        g["fast"] = min(CHOICES["fast"], key=lambda x: abs(x - g["slow"] / 4))
    return g


def genome_key(g: dict) -> str:
    """Solo los genes que INFLUYEN en la estrategia (evita contar como distintos los inertes)."""
    return hashlib.md5(json.dumps(active(g), sort_keys=True, default=str).encode()).hexdigest()[:12]


def active(g: dict) -> dict:
    a = {"tf": g["tf"], "side": g["side"], "entry": g["entry"], "regime": g["regime"],
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
    r = g["regime"]
    if r == "price_sma": a["reg_n"] = g["reg_n"]
    elif r == "ma_pair": a.update(ma_kind=g["ma_kind"], fast=g["fast"], slow=g["slow"])
    elif r == "volpct": a.update(vp_lo=g["vp_lo"], vp_hi=g["vp_hi"])
    return a


def _cross_up(a, b): return (a > b) & (a.shift(1) <= b.shift(1))
def _cross_dn(a, b): return (a < b) & (a.shift(1) >= b.shift(1))


def build_signals(g: dict, m: Market):
    """Devuelve (entry_sig, exit_sig, stop_dist) para toda la serie. CAUSAL."""
    c = m.df["close"]
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
    else:  # struct_break
        sb = m.sbreak(g["sw_k"]); L, S = sb.break_up == 1, sb.break_dn == 1
    # filtro de régimen
    r = g["regime"]
    if r == "price_sma":
        ma = m.sma(g["reg_n"]); okL, okS = c > ma, c < ma
    elif r == "ma_pair":
        f = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["fast"])
        s = (m.sma if g["ma_kind"] == "sma" else m.ema)(g["slow"]); okL, okS = f > s, f < s
    elif r == "volpct":
        v = m.volpct(); okL = okS = (v >= g["vp_lo"]) & (v <= g["vp_hi"])
    else:
        okL = okS = pd.Series(True, index=c.index)
    L = (L & okL).to_numpy(); S = (S & okS).to_numpy()
    side = g["side"]
    if side == "long": S = np.zeros_like(S)
    if side == "short": L = np.zeros_like(L)
    entry = np.where(L, 1, np.where(S, -1, 0)).astype(np.int8)
    exit_sig = np.where(L, 1, np.where(S, -1, 0)).astype(np.int8) if g["exit_opp"] else np.zeros(len(c), np.int8)
    sd = stop_distance(g, m, entry)
    return entry, exit_sig, sd


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
    return len(active(g)) - 6


def evaluate(g: dict, m: Market, a: int, b: int, params: Params | None = None) -> dict:
    """Evalúa el genoma en el tramo [a, b) de la serie (las señales se calculan con TODA la serie
    anterior, sin mirar más allá de cada vela)."""
    params = params or Params(capital=1000.0, risk_frac=0.01, max_bars=g["max_bars"], tp_mult=g["tp"])
    params = Params(**{**params.__dict__, "max_bars": g["max_bars"], "tp_mult": g["tp"]})
    ent, ex, sd = build_signals(g, m)
    res = run(m.o[a:b], m.h[a:b], m.l[a:b], m.c[a:b], ent[a:b], sd[a:b], params,
              exit_sig=ex[a:b], funding=m.funding[a:b])
    out = summarize(res, m.tf); out["_res"] = res
    return out
