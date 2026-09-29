"""Núcleo prerregistrado v1 (ver config/nucleo_prerregistrado.md). NO cambiar parámetros tras ejecutar.

Simulación por velas de 4h con EXPOSICIÓN CONTINUA (fracción del capital en BTC):
  * Señal calculada al cierre de la vela i -> posición durante la vela i+1 (sin look-ahead).
  * Entre rebalanceos la posición (en unidades) es constante: la exposición DERIVA con el precio.
  * Se reajusta si cambia la señal o si la exposición se sale de una banda del 20 % del objetivo.
  * Costes por rotación (comisión + deslizamiento) y funding (los largos pagan si es positivo).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
try:
    from numba import njit
except ImportError:                       # el ejecutor en vivo puede correr sin numba (más lento, mismo resultado)
    def njit(*a, **k):
        return (lambda f: f)

BPY4H = 6 * 365.25


@dataclass(frozen=True)
class CoreParams:
    horizons: tuple = (20, 60, 120, 250)
    donchian: int = 50
    w_a: float = 0.5
    w_b: float = 0.5
    target_vol: float = 0.25
    cap: float = 2.0
    vol_span_days: int = 45
    band: float = 0.20
    cost: float = 0.0007            # 5 pb comisión + 2 pb deslizamiento por unidad de rotación
    fund_filter: bool = False       # variante F prerregistrada
    fund_filter_scale: float = 0.5
    use_vol_target: bool = True


def daily_from_4h(df: pd.DataFrame) -> pd.Series:
    return df["close"].resample("1D").last()


def signal_a(df: pd.DataFrame, horizons=(20, 60, 120, 250)) -> np.ndarray:
    """Pata A: media de s_L = 1[retorno a L días > 0], evaluada al cierre diario y APLICADA desde el
    día siguiente. Devuelve un valor por vela de 4h."""
    d = daily_from_4h(df).ffill()                      # días sin datos: se arrastra el último cierre
    s = sum((d / d.shift(L) - 1 > 0).astype(float) for L in horizons) / len(horizons)   # NaN -> 0
    s = s.shift(1)                                     # el día D usa el cierre de D-1
    return s.reindex(df.index.floor("1D")).fillna(0.0).to_numpy()


@njit(cache=True)
def _donchian_state(close, high, low, n):
    """Estado al cierre de la vela i (vale para la vela i+1). Largo si cierra sobre el máximo de las n
    velas anteriores; sale si cierra bajo el mínimo de las n anteriores."""
    m = len(close)
    st = np.zeros(m)
    cur = 0.0
    for i in range(n, m):
        hh = -1e300; ll = 1e300
        for j in range(i - n, i):
            if high[j] > hh: hh = high[j]
            if low[j] < ll: ll = low[j]
        if close[i] > hh: cur = 1.0
        elif close[i] < ll: cur = 0.0
        st[i] = cur
    return st


def signal_b(df: pd.DataFrame, n: int = 50) -> np.ndarray:
    return _donchian_state(df["close"].to_numpy(), df["high"].to_numpy(), df["low"].to_numpy(), n)


def ewma_vol(df: pd.DataFrame, span_days: int = 45) -> np.ndarray:
    r = df["close"].pct_change()
    return (r.ewm(span=span_days * 6, min_periods=60).std() * np.sqrt(BPY4H)).to_numpy()


@njit(cache=True)
def _simulate(r, target, sig_changed, funding, cost, band):
    """r[i]: retorno de la vela i (cierre a cierre). target[i], sig_changed[i]: decididos al cierre de
    la vela i-1 (aplican a la vela i). Devuelve capital, exposición, rotación, coste de funding."""
    n = len(r)
    eq = np.ones(n); expo = np.zeros(n); turn = np.zeros(n); fcost = np.zeros(n)
    e = 0.0; cur = 1.0
    for i in range(n):
        # 1) rebalanceo al inicio de la vela i (información hasta el cierre de i-1)
        t = target[i]
        need = sig_changed[i] or (t > 0 and abs(e - t) > band * t) or (t == 0 and e > 0)
        if need:
            tv = abs(t - e)
            cur *= (1.0 - tv * cost)
            turn[i] = tv
            e = t
        expo[i] = e
        # 2) retorno y funding durante la vela i
        g = 1.0 + e * r[i]
        f = e * funding[i]
        cur *= (g - f)
        fcost[i] = e * funding[i]
        eq[i] = cur
        # 3) deriva de la exposición (unidades constantes)
        if g > 0: e = e * (1.0 + r[i]) / g
        else: e = 0.0
    return eq, expo, turn, fcost


def compute_targets(df: pd.DataFrame, p: CoreParams = CoreParams(), fund_flag: np.ndarray | None = None) -> dict:
    """Señal y exposición objetivo decididas AL CIERRE de cada vela (código compartido por backtest y vivo)."""
    n = len(df)
    A = signal_a(df, p.horizons); B = signal_b(df, p.donchian)
    sig = p.w_a * A + p.w_b * B                       # decidido al cierre de la vela i
    vol = ewma_vol(df, p.vol_span_days)
    if p.use_vol_target:
        scale = np.where(np.isfinite(vol) & (vol > 0), np.minimum(p.cap, p.target_vol / vol), 0.0)
    else:
        scale = np.ones(n)
    tgt = sig * scale
    if p.fund_filter and fund_flag is not None:
        tgt = np.where(fund_flag, tgt * p.fund_filter_scale, tgt)
    return {"A": A, "B": B, "sig": sig, "vol": vol, "scale": scale, "tgt": tgt}


def run_core(df: pd.DataFrame, funding: np.ndarray, p: CoreParams = CoreParams(),
             fund_flag: np.ndarray | None = None) -> dict:
    """df: velas 4h (open,high,low,close). funding: tasa por vela (suma de pagos dentro de la vela)."""
    n = len(df)
    ct = compute_targets(df, p, fund_flag)
    sig, vol, tgt = ct["sig"], ct["vol"], ct["tgt"]
    # lo decidido al cierre de i aplica a la vela i+1
    target = np.r_[0.0, tgt[:-1]]
    raw_change = np.r_[False, sig[1:] != sig[:-1]]        # la señal cambió al cierre de i
    changed = np.r_[False, raw_change[:-1]]               # ... y se aplica en la vela i+1
    r = df["close"].pct_change().fillna(0.0).to_numpy()
    eq, expo, turn, fcost = _simulate(r, target, changed, funding, p.cost, p.band)
    return {"equity": pd.Series(eq, index=df.index), "expo": pd.Series(expo, index=df.index),
            "turn": pd.Series(turn, index=df.index), "fund": pd.Series(fcost, index=df.index),
            "sig": pd.Series(sig, index=df.index), "vol": pd.Series(vol, index=df.index)}


def reference_bh(df: pd.DataFrame, funding: np.ndarray, p: CoreParams = CoreParams(), vol_targeted=False):
    """Comprar y mantener (1x) o con el MISMO volatility targeting/tope/banda/costes."""
    n = len(df); r = df["close"].pct_change().fillna(0.0).to_numpy()
    if not vol_targeted:
        return pd.Series(np.cumprod(1 + r), index=df.index)
    vol = ewma_vol(df, p.vol_span_days)
    tgt = np.where(np.isfinite(vol) & (vol > 0), np.minimum(p.cap, p.target_vol / vol), 0.0)
    target = np.r_[0.0, tgt[:-1]]
    changed = np.zeros(n, bool)
    eq, expo, turn, fc = _simulate(r, target, changed, funding, p.cost, p.band)
    return pd.Series(eq, index=df.index)
