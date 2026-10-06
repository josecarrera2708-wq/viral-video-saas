"""Simulador intradía en velas de 5 min, con «entrada de protección» de un solo uso (petición del dueño, 2026-10-06).

Las señales se generan al CIERRE de una vela de 15 min / 1 h; la orden se activa en la apertura de la primera vela de 5 min posterior.
Toda la gestión (stop, objetivo, segunda entrada, tiempo) se recorre vela a vela de 5 min.

Modos (un solo uso por operación):
  0 base       stop a 1R (sd), objetivo k·R, salida por tiempo.
  1 promediar  sin stop inicial a 1R: si el precio llega a E − d·a·sd se añade m·q en la MISMA dirección (orden límite, maker);
               stop común en E − d·b·sd; tras activarse, el objetivo pasa a A + d·hh·sd (A = precio medio). hh < 0 → se mantiene el objetivo original.
  2 girar      en E − d·a·sd se cierra la posición y se abre la CONTRARIA con m·q (equivale a una cobertura opuesta de (1+m)·q en modo hedge);
               stop de la nueva en P + d·b·sd, objetivo en P − d·k2·sd.

Comparación justa: el tamaño q se fija para que la pérdida MÁXIMA (si salta todo) sea el mismo % del capital en todos los modos.
R de cada operación = resultado neto / pérdida máxima nominal (sin costes): en el modo 0 coincide con la R del motor.

Orden dentro de una vela (conservador): primero lo adverso. En la vela en que cambia el estado (entrada, activación, giro) solo cuentan las
salidas adversas del nuevo estado; los objetivos se comprueban desde la vela siguiente (salvo en la vela de entrada del modo 0, como el motor).
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd
from numba import njit


@dataclass(frozen=True)
class Gestion:
    k: float = 2.0            # objetivo en R
    horas: float = 4.0        # salida por tiempo
    modo: int = 0             # 0 base · 1 promediar · 2 girar
    a: float = 1.0            # nivel de la segunda entrada / giro, en R contra la entrada
    m: float = 1.0            # tamaño de la segunda pata respecto a la primera
    b: float = 2.0            # modo 1: stop común (R desde la entrada) · modo 2: stop de la pata girada (R desde el giro)
    hh: float = 0.0           # modo 1: objetivo tras activarse, en R desde el precio medio (<0: mantener el original)
    k2: float = 2.0           # modo 2: objetivo de la pata girada, en R desde el giro


@dataclass(frozen=True)
class Costes:
    taker: float = 0.0005
    maker: float = 0.0002
    slip: float = 0.0002
    pen: float = 0.0001       # el objetivo límite solo se llena si el precio lo supera en 1 pb
    riesgo: float = 0.005
    apal: float = 5.0
    capital: float = 1000.0

    def x(self, k: float) -> "Costes":
        return Costes(self.taker * k, self.maker * k, self.slip * k, self.pen, self.riesgo, self.apal, self.capital)


@njit(cache=True)
def _sim(o, h, l, c, fu, si, sd_, sl_, sdir, k, maxb, modo, a, m, b, hh, k2, lim_bars,
         taker, maker, slip, pen, riesgo, apal, capital):
    n = len(o); ns = len(si)
    t_e = np.zeros(ns, np.int64); t_x = np.zeros(ns, np.int64); t_d = np.zeros(ns, np.int8)
    t_r = np.zeros(ns); t_pnl = np.zeros(ns); t_eq = np.zeros(ns); t_act = np.zeros(ns, np.int8); t_why = np.zeros(ns, np.int8)
    nt = 0; eq = capital; libre = 0
    # unidades de pérdida máxima por unidad de q (en múltiplos de sd)
    if modo == 1:
        lu = b + m * (b - a)
    elif modo == 2:
        lu = a + m * b
    else:
        lu = 1.0
    for s in range(ns):
        i0 = si[s]
        if i0 < libre or i0 >= n or eq <= 0:
            continue
        d = sdir[s]; sd = sd_[s]
        if not (sd > 0):
            continue
        # --- entrada: a mercado en la apertura o límite durante lim_bars velas
        lim = sl_[s]; j = i0; ent = -1; E = 0.0; fee_rate = taker
        if np.isnan(lim):
            ent = i0; E = o[i0] * (1.0 + d * slip)
        else:
            jj = i0
            while jj < n and jj < i0 + lim_bars:
                if (d == 1 and l[jj] < lim) or (d == -1 and h[jj] > lim):
                    ent = jj; E = min(o[jj], lim) if d == 1 else max(o[jj], lim); fee_rate = maker
                    break
                jj += 1
            if ent < 0:
                libre = i0 + 1
                continue
        q = riesgo * eq / (lu * sd + E * (taker + slip + taker) * (1.0 + m * (modo > 0)))
        qcap = apal * eq / E
        if q > qcap:
            q = qcap
        eq_pre = eq
        cash = -q * E * fee_rate                   # comisiones y funding acumulados (negativos = coste)
        pos = d * q                                # posición neta (BTC, con signo)
        cost_basis = q * E                         # para precio medio
        stop = E - d * sd * (b if modo == 1 else (a if modo == 2 else 1.0))
        tgt = E + d * k * sd
        trig = E - d * a * sd
        act = 0; why = 0; j = ent; held = 0; done = False; realized = 0.0; xj = ent
        first = True; limite = not np.isnan(lim)
        while j < n:
            changed = first and limite               # vela de llenado de una orden límite: el objetivo, desde la siguiente
            # 1) adverso: activación (modo 1) o giro (modo 2) o stop
            if act == 0 and modo == 1 and ((d == 1 and l[j] <= trig) or (d == -1 and h[j] >= trig)):
                px = min(o[j], trig) if d == 1 else max(o[j], trig)
                q2 = m * q
                cash -= q2 * px * maker
                cost_basis += q2 * px; pos += d * q2; act = 1; changed = True
                A = cost_basis / abs(pos)
                if hh >= 0:
                    tgt = A + d * hh * sd
            elif act == 0 and modo == 2 and ((d == 1 and l[j] <= trig) or (d == -1 and h[j] >= trig)):
                px = (min(o[j], trig) * (1.0 - slip)) if d == 1 else (max(o[j], trig) * (1.0 + slip))
                # cerrar la primera pata
                realized += d * q * (px - E); cash -= q * px * taker
                q2 = m * q; act = 1; changed = True
                if q2 > 0:
                    pos = -d * q2; cash -= q2 * px * taker; cost_basis = q2 * px
                    stop = trig + d * b * sd; tgt = trig - d * k2 * sd; d = -d
                else:
                    pos = 0.0
                    xj = j; why = 1; done = True
            if not done:
                pdir = 1 if pos > 0 else -1
                hit_stop = (pdir == 1 and (l[j] <= stop or o[j] <= stop)) or (pdir == -1 and (h[j] >= stop or o[j] >= stop))
                if hit_stop:
                    px = (min(o[j], stop) * (1.0 - slip)) if pdir == 1 else (max(o[j], stop) * (1.0 + slip))
                    A = cost_basis / abs(pos)
                    realized += pos * (px - A); cash -= abs(pos) * px * taker
                    pos = 0.0; xj = j; why = 1; done = True
                elif not changed:
                    hit_tp = (pdir == 1 and h[j] > tgt * (1.0 + pen)) or (pdir == -1 and l[j] < tgt * (1.0 - pen))
                    if hit_tp:
                        A = cost_basis / abs(pos)
                        realized += pos * (tgt - A); cash -= abs(pos) * tgt * maker
                        pos = 0.0; xj = j; why = 2; done = True
            if done:
                break
            # 2) funding al cierre de la vela y tiempo
            cash -= pos * c[j] * fu[j]
            held += 1; first = False
            if held >= maxb:
                if j + 1 >= n:
                    xj = j; px = c[j]
                else:
                    xj = j + 1; px = o[j + 1] * (1.0 - slip) if pos > 0 else o[j + 1] * (1.0 + slip)
                A = cost_basis / abs(pos)
                realized += pos * (px - A); cash -= abs(pos) * px * taker
                pos = 0.0; why = 3; done = True
                break
            j += 1
        if not done:                                # datos acabados con la operación abierta: se cierra al último cierre
            A = cost_basis / abs(pos); xj = n - 1
            realized += pos * (c[n - 1] - A); cash -= abs(pos) * c[n - 1] * taker; why = 4
        pnl = realized + cash
        eq += pnl
        t_e[nt] = ent; t_x[nt] = xj; t_d[nt] = sdir[s]; t_pnl[nt] = pnl; t_eq[nt] = eq_pre
        t_r[nt] = pnl / (q * lu * sd); t_act[nt] = act; t_why[nt] = why
        nt += 1
        libre = xj + 1 if why != 3 else xj
    return t_e[:nt], t_x[:nt], t_d[:nt], t_r[:nt], t_pnl[:nt], t_eq[:nt], t_act[:nt], t_why[:nt]


def simulate(b5: pd.DataFrame, f5: np.ndarray, t_act: pd.DatetimeIndex, d: np.ndarray, sd: np.ndarray, g: Gestion,
             costes: Costes = Costes(), lim: np.ndarray | None = None, lim_bars: int = 0) -> pd.DataFrame:
    """b5: velas de 5 min (índice = apertura UTC). t_act: momento en que se activa cada orden (= cierre de la vela de señal).
    d: +1/−1. sd: distancia de stop en precio. lim: precio límite de entrada (NaN = a mercado)."""
    idx = b5.index
    si = np.searchsorted(idx.asi8, pd.DatetimeIndex(t_act).asi8, side="left").astype(np.int64)
    order = np.argsort(si, kind="stable")
    lim = np.full(len(si), np.nan) if lim is None else np.asarray(lim, float)
    out = _sim(b5["open"].to_numpy(float), b5["high"].to_numpy(float), b5["low"].to_numpy(float), b5["close"].to_numpy(float),
               np.asarray(f5, float), si[order], np.asarray(sd, float)[order], lim[order], np.asarray(d, np.int8)[order],
               g.k, int(round(g.horas * 12)), g.modo, g.a, g.m, g.b, g.hh, g.k2, int(lim_bars),
               costes.taker, costes.maker, costes.slip, costes.pen, costes.riesgo, costes.apal, costes.capital)
    e, x, dd, r, pnl, eqp, act, why = out
    return pd.DataFrame({"entrada": idx[e], "salida": idx[np.minimum(x, len(idx) - 1)], "dir": dd, "R": r, "pnl": pnl, "eq_pre": eqp,
                         "activada": act.astype(bool), "motivo": pd.Categorical.from_codes(why, ["?", "stop", "objetivo", "tiempo", "fin"])})
