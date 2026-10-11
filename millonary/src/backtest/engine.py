"""Motor de backtest de Millonary (perpetuo USDT-M, BTC).

Convenciones (para que no haya look-ahead):
  * Una señal se evalúa con la información hasta el CIERRE de la vela i y se ejecuta en la
    APERTURA de la vela i+1.
  * El stop y el TP se comprueban dentro de la vela usando high/low. Si en la misma vela se
    tocan el stop y el TP, se asume que se tocó PRIMERO el stop (lado conservador).
  * Si la vela abre más allá del stop (hueco), se ejecuta en la apertura (peor que el stop).
  * Funding: se paga/cobra al cierre de la vela cuyo cierre coincide con la marca de funding, si
    la posición sigue abierta. Largos pagan con funding positivo.
  * Tamaño por riesgo fijo: qty = riesgo% * capital / distancia_stop, con tope de apalancamiento,
    redondeo a paso de lote y lote mínimo.
  * Liquidación modelada (margen cruzado, margen de mantenimiento mmr). Si ocurre, el capital
    queda en 0 (conservador) y se detiene la simulación.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit

STOP, TP, SIGNAL, TIME, LIQ, END = 0, 1, 2, 3, 4, 5
REASONS = {0: "stop", 1: "tp", 2: "signal", 3: "time", 4: "liq", 5: "end"}


@dataclass(frozen=True)
class Params:
    capital: float = 1000.0
    risk_frac: float = 0.005          # riesgo por operación (fracción del capital)
    max_leverage: float = 5.0         # nocional máximo = max_leverage * capital
    taker_fee: float = 0.0005         # 0,05 % por lado (stop, salidas a mercado, entradas)
    maker_fee: float = 0.0002         # 0,02 % (take-profit como orden límite)
    slippage: float = 0.0002          # 2 pb en entradas/stops/salidas a mercado
    lot_step: float = 0.001           # BTC
    min_qty: float = 0.001            # BTC
    max_minlot_risk: float = 0.02     # si el lote mínimo arriesga > 2 % del capital, se omite
    min_notional: float = 100.0       # nocional mínimo de orden (USDT). VERIFICAR en el exchange real
    tp_pen: float = 0.0001            # el TP solo se llena si el precio lo SUPERA en 1 pb (cola de la orden)
    stress_range_frac: float = 0.0    # estrés: deslizamiento de stop >= esta fracción del rango de la vela
    mmr: float = 0.005                # margen de mantenimiento (0,5 %)
    tp_mult: float = 0.0              # take-profit en múltiplos de R (0 = sin TP)
    max_bars: int = 0                 # salida por tiempo (0 = sin límite)
    allow_short: bool = True


@njit(cache=True)
def _run(o, h, l, c, entry_sig, exit_sig, stop_dist, funding,
         capital, risk_frac, max_lev, taker, maker, slip, lot, min_qty,
         max_minlot_risk, mmr, tp_mult, max_bars, allow_short, min_notional, tp_pen,
         stress_range_frac):
    n = len(o)
    eq_close = np.empty(n)
    eq_low = np.empty(n)
    # registro de operaciones
    t_entry = np.zeros(n, np.int64); t_exit = np.zeros(n, np.int64)
    t_dir = np.zeros(n, np.int8); t_epx = np.zeros(n); t_xpx = np.zeros(n)
    t_qty = np.zeros(n); t_pnl = np.zeros(n); t_fee = np.zeros(n)
    t_fund = np.zeros(n); t_reason = np.zeros(n, np.int8); t_r = np.zeros(n)
    t_risk = np.zeros(n); t_eqpre = np.zeros(n)
    nt = 0
    eq = capital
    pos = 0            # +1 largo, -1 corto, 0 plano
    qty = 0.0; epx = 0.0; stop_px = 0.0; tp_px = 0.0; liq_px = 0.0
    bars_held = 0; e_idx = 0; e_fee = 0.0; e_fund = 0.0; e_risk = 0.0; eq_pre = 0.0
    pend_dir = 0; pend_stop = 0.0; pend_exit = False; pend_reason = SIGNAL
    ruined = False
    skipped_minlot = 0
    skipped_badstop = 0
    for i in range(n):
        if ruined:
            eq_close[i] = 0.0
            eq_low[i] = 0.0
            continue
        # 1) salida pendiente (señal o tiempo) a la apertura
        if pos != 0 and pend_exit:
            px = o[i] * (1.0 - pos * slip)
            fee = qty * px * taker
            pnl = pos * qty * (px - epx)
            eq += pnl - fee
            t_entry[nt] = e_idx; t_exit[nt] = i; t_dir[nt] = pos; t_epx[nt] = epx
            t_xpx[nt] = px; t_qty[nt] = qty; t_pnl[nt] = pnl - fee - e_fee + e_fund
            t_fee[nt] = fee + e_fee; t_fund[nt] = e_fund; t_reason[nt] = pend_reason
            t_risk[nt] = e_risk; t_eqpre[nt] = eq_pre
            t_r[nt] = (pnl - fee - e_fee + e_fund) / e_risk if e_risk > 0 else 0.0
            nt += 1
            pos = 0; qty = 0.0; pend_exit = False
        pend_exit = False
        # 2) entrada pendiente a la apertura
        if pos == 0 and pend_dir != 0 and eq > 0:
            d = pend_dir
            px = o[i] * (1.0 + d * slip)
            sd = pend_stop
            if not (sd > 0):
                skipped_badstop += 1
            else:
                cost = px * (taker + slip + taker)          # coste de ida y vuelta dentro del riesgo
                eff = sd + cost
                q = (risk_frac * eq) / eff
                q_cap = (max_lev * eq) / px
                if q > q_cap:
                    q = q_cap
                q = np.floor(q / lot + 1e-9) * lot
                if q < min_qty or q * px < min_notional:
                    # cantidad mínima válida (respeta lote mínimo y nocional mínimo)
                    q_min = np.ceil(min_notional / px / lot - 1e-9) * lot
                    if q_min < min_qty:
                        q_min = min_qty
                    if (q_min * (sd + cost) / eq <= max_minlot_risk
                            and q_min * px <= max_lev * eq):
                        q = q_min
                    else:
                        q = 0.0
                        skipped_minlot += 1
                if q > 0:
                    eq_pre = eq
                    pos = d; qty = q; epx = px; e_idx = i
                    e_fee = qty * px * taker
                    eq -= e_fee
                    e_fund = 0.0
                    stop_px = px - d * sd
                    tp_px = px + d * tp_mult * sd if tp_mult > 0 else 0.0
                    if d == 1:
                        liq_px = (qty * px - eq) / (qty * (1.0 - mmr))
                    else:
                        liq_px = (eq + qty * px) / (qty * (1.0 + mmr))
                    e_risk = qty * sd
                    bars_held = 0
        pend_dir = 0
        # 3) intravela: liquidación, stop, take-profit
        if pos != 0:
            closed = False
            reason = STOP
            xpx = 0.0
            xfee_rate = taker
            if pos == 1:
                liq_hit = l[i] <= liq_px
                stop_hit = (l[i] <= stop_px) or (o[i] <= stop_px)
                tp_hit = tp_px > 0 and h[i] > tp_px * (1.0 + tp_pen)
                # el más cercano a la entrada se toca antes; el stop gana empates con TP
                if liq_hit and (liq_px >= stop_px):
                    closed = True; reason = LIQ; xpx = liq_px
                elif stop_hit:
                    closed = True; reason = STOP
                    xpx = min(o[i], stop_px) * (1.0 - max(slip, stress_range_frac * (h[i] - l[i]) / o[i]))
                    if xpx <= liq_px:                 # hueco más allá de la liquidación
                        reason = LIQ; xpx = liq_px
                elif tp_hit:
                    closed = True; reason = TP; xpx = tp_px; xfee_rate = maker
            else:
                liq_hit = h[i] >= liq_px
                stop_hit = (h[i] >= stop_px) or (o[i] >= stop_px)
                tp_hit = tp_px > 0 and l[i] < tp_px * (1.0 - tp_pen)
                if liq_hit and (liq_px <= stop_px):
                    closed = True; reason = LIQ; xpx = liq_px
                elif stop_hit:
                    closed = True; reason = STOP
                    xpx = max(o[i], stop_px) * (1.0 + max(slip, stress_range_frac * (h[i] - l[i]) / o[i]))
                    if xpx >= liq_px:
                        reason = LIQ; xpx = liq_px
                elif tp_hit:
                    closed = True; reason = TP; xpx = tp_px; xfee_rate = maker
            if closed:
                if reason == LIQ:
                    fee = 0.0
                    pnl_total = -eq_pre                  # se pierde todo el capital previo a la entrada
                    eq = 0.0
                    ruined = True
                    t_entry[nt] = e_idx; t_exit[nt] = i; t_dir[nt] = pos; t_epx[nt] = epx
                    t_xpx[nt] = xpx; t_qty[nt] = qty; t_pnl[nt] = pnl_total
                    t_fee[nt] = e_fee; t_fund[nt] = e_fund; t_reason[nt] = LIQ
                    t_risk[nt] = e_risk; t_eqpre[nt] = eq_pre
                    t_r[nt] = pnl_total / e_risk if e_risk > 0 else 0.0
                    nt += 1
                    pos = 0; qty = 0.0
                else:
                    fee = qty * xpx * xfee_rate
                    pnl = pos * qty * (xpx - epx)
                    eq += pnl - fee
                    t_entry[nt] = e_idx; t_exit[nt] = i; t_dir[nt] = pos; t_epx[nt] = epx
                    t_xpx[nt] = xpx; t_qty[nt] = qty; t_pnl[nt] = pnl - fee - e_fee + e_fund
                    t_fee[nt] = fee + e_fee; t_fund[nt] = e_fund; t_reason[nt] = reason
                    t_risk[nt] = e_risk; t_eqpre[nt] = eq_pre
                    t_r[nt] = (pnl - fee - e_fee + e_fund) / e_risk if e_risk > 0 else 0.0
                    nt += 1
                    pos = 0; qty = 0.0
        # 4) funding y tiempo en posición (solo si sigue abierta al cierre)
        if pos != 0:
            f = -pos * qty * c[i] * funding[i]
            eq += f
            e_fund += f
            if pos == 1:
                liq_px = (qty * epx - eq) / (qty * (1.0 - mmr))
            else:
                liq_px = (eq + qty * epx) / (qty * (1.0 + mmr))
            bars_held += 1
            if max_bars > 0 and bars_held >= max_bars:
                pend_exit = True; pend_reason = TIME
        # 5) capital marcado a mercado
        if pos != 0:
            eq_close[i] = eq + pos * qty * (c[i] - epx)
            worst = l[i] if pos == 1 else h[i]
            eq_low[i] = min(eq_close[i], eq + pos * qty * (worst - epx))
        else:
            eq_close[i] = eq
            eq_low[i] = eq
        if eq_close[i] <= 0:
            ruined = True
            eq_close[i] = 0.0
            eq_low[i] = 0.0
        # 6) señales al cierre de la vela i (se ejecutan en la apertura de i+1)
        if i < n - 1 and not ruined:
            if pos == 0:
                s = entry_sig[i]
                if s == 1 or (s == -1 and allow_short):
                    pend_dir = s; pend_stop = stop_dist[i]
            else:
                if exit_sig[i] != 0 and exit_sig[i] == -pos:
                    pend_exit = True; pend_reason = SIGNAL
    # cierre forzado al final de los datos
    if pos != 0 and not ruined:
        px = c[n - 1] * (1.0 - pos * slip)
        fee = qty * px * taker
        pnl = pos * qty * (px - epx)
        eq += pnl - fee
        t_entry[nt] = e_idx; t_exit[nt] = n - 1; t_dir[nt] = pos; t_epx[nt] = epx
        t_xpx[nt] = px; t_qty[nt] = qty; t_pnl[nt] = pnl - fee - e_fee + e_fund
        t_fee[nt] = fee + e_fee; t_fund[nt] = e_fund; t_reason[nt] = END
        t_risk[nt] = e_risk; t_eqpre[nt] = eq_pre
        t_r[nt] = (pnl - fee - e_fee + e_fund) / e_risk if e_risk > 0 else 0.0
        nt += 1
        eq_close[n - 1] = eq
        eq_low[n - 1] = min(eq_low[n - 1], eq)
    return (eq_close, eq_low, nt, t_entry[:nt], t_exit[:nt], t_dir[:nt], t_epx[:nt], t_xpx[:nt],
            t_qty[:nt], t_pnl[:nt], t_fee[:nt], t_fund[:nt], t_reason[:nt], t_r[:nt],
            t_risk[:nt], t_eqpre[:nt], skipped_minlot, skipped_badstop, ruined)


def run(o, h, l, c, entry_sig, stop_dist, params: Params = Params(), exit_sig=None,
        funding=None) -> dict:
    """entry_sig: +1 / -1 / 0 por vela. stop_dist: distancia de stop en PRECIO (>0) por vela."""
    o, h, l, c = (np.ascontiguousarray(x, dtype=np.float64) for x in (o, h, l, c))
    n = len(o)
    entry_sig = np.ascontiguousarray(entry_sig, dtype=np.int8)
    stop_dist = np.ascontiguousarray(stop_dist, dtype=np.float64)
    exit_sig = np.zeros(n, np.int8) if exit_sig is None else np.ascontiguousarray(exit_sig, np.int8)
    if funding is None:
        import warnings
        warnings.warn("run() sin funding: se asume 0. Pasa funding=np.zeros(n) si es a propósito.")
        funding = np.zeros(n)
    funding = np.ascontiguousarray(funding, np.float64)
    for name, a in (("h", h), ("l", l), ("c", c), ("entry_sig", entry_sig),
                    ("stop_dist", stop_dist), ("exit_sig", exit_sig), ("funding", funding)):
        if len(a) != n:
            raise ValueError(f"longitud distinta en {name}")
    p = params
    out = _run(o, h, l, c, entry_sig, exit_sig, stop_dist, funding, p.capital, p.risk_frac,
               p.max_leverage, p.taker_fee, p.maker_fee, p.slippage, p.lot_step, p.min_qty,
               p.max_minlot_risk, p.mmr, p.tp_mult, p.max_bars, p.allow_short, p.min_notional,
               p.tp_pen, p.stress_range_frac)
    (eq, eq_low, nt, ei, xi, d, epx, xpx, q, pnl, fee, fund, reason, r, risk, eqpre, skipped, badstop, ruined) = out
    return {"equity": eq, "equity_low": eq_low, "n_trades": nt, "entry_idx": ei, "exit_idx": xi, "dir": d,
            "entry_px": epx, "exit_px": xpx, "qty": q, "pnl": pnl, "fees": fee,
            "funding": fund, "reason": reason, "r": r, "risk": risk,
            "risk_frac_real": risk / np.where(eqpre > 0, eqpre, np.nan), "skipped_minlot": skipped,
            "skipped_badstop": badstop, "ruined": bool(ruined), "params": p}
