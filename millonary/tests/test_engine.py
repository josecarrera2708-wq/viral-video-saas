import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
import warnings
warnings.filterwarnings('ignore', message='run\\(\\) sin funding')
from src.backtest.engine import run, Params, STOP, TP, SIGNAL, TIME, LIQ, END

ZERO = dict(taker_fee=0.0, maker_fee=0.0, slippage=0.0, lot_step=1e-6, min_qty=1e-6,
            min_notional=0.0, tp_pen=0.0)


def bars(opens, highs=None, lows=None, closes=None):
    o = np.array(opens, float)
    h = o + 1 if highs is None else np.array(highs, float)
    l = o - 1 if lows is None else np.array(lows, float)
    c = o.copy() if closes is None else np.array(closes, float)
    return o, h, l, c


def sig(n, at, d=1):
    s = np.zeros(n, np.int8); s[at] = d; return s


def test_entry_executes_next_open_not_signal_bar():
    o, h, l, c = bars([100, 110, 120, 130, 140])
    r = run(o, h, l, c, sig(5, 1), np.full(5, 50.0), Params(**ZERO))
    assert r["entry_idx"][0] == 2
    assert r["entry_px"][0] == 120.0          # apertura de la vela SIGUIENTE a la señal


def test_stop_loses_exactly_one_R_without_costs():
    o, h, l, c = bars([100, 100, 100, 100], lows=[99, 99, 89, 99])
    p = Params(capital=1000, risk_frac=0.01, **ZERO)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 10.0), p)
    assert r["reason"][0] == STOP
    assert r["pnl"][0] == pytest.approx(-10.0, rel=1e-6)      # 1 % de 1000
    assert r["r"][0] == pytest.approx(-1.0, rel=1e-6)
    assert r["equity"][-1] == pytest.approx(990.0, rel=1e-6)


def test_tp_wins_R_multiple():
    o, h, l, c = bars([100, 100, 100, 100], highs=[101, 101, 121, 101])
    p = Params(capital=1000, risk_frac=0.01, tp_mult=2.0, **ZERO)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 10.0), p)
    assert r["reason"][0] == TP
    assert r["r"][0] == pytest.approx(2.0, rel=1e-6)


def test_stop_and_tp_same_bar_stop_first():
    o, h, l, c = bars([100, 100, 100, 100], highs=[101, 101, 130, 101], lows=[99, 99, 85, 99])
    p = Params(capital=1000, risk_frac=0.01, tp_mult=2.0, **ZERO)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 10.0), p)
    assert r["reason"][0] == STOP


def test_gap_through_stop_fills_at_open_worse_than_stop():
    o = [100, 100, 80, 80]; h = [101, 101, 81, 81]; l = [99, 99, 79, 79]
    p = Params(capital=1000, risk_frac=0.01, **ZERO)
    r = run(*bars(o, h, l), sig(4, 0), np.full(4, 10.0), p)
    assert r["reason"][0] == STOP
    assert r["exit_px"][0] == 80.0
    assert r["r"][0] < -1.5                                    # peor que 1R


def test_short_symmetry():
    o, h, l, c = bars([100, 100, 100, 100], highs=[101, 101, 111, 101])
    p = Params(capital=1000, risk_frac=0.01, **ZERO)
    r = run(o, h, l, c, sig(4, 0, -1), np.full(4, 10.0), p)
    assert r["dir"][0] == -1 and r["reason"][0] == STOP
    assert r["r"][0] == pytest.approx(-1.0, rel=1e-6)


def test_fees_and_slippage_reduce_pnl():
    o, h, l, c = bars([100, 100, 100, 100, 100], highs=[101] * 5, lows=[99, 99, 99, 99, 99])
    free = run(o, h, l, c, sig(5, 0), np.full(5, 10.0), Params(**ZERO))
    cost = run(o, h, l, c, sig(5, 0), np.full(5, 10.0),
               Params(lot_step=1e-6, min_qty=1e-6, min_notional=0.0))
    assert cost["pnl"][0] < free["pnl"][0]
    assert cost["fees"][0] > 0


def test_leverage_cap_limits_notional():
    o, h, l, c = bars([100] * 4)
    p = Params(capital=1000, risk_frac=0.5, max_leverage=5, **ZERO)   # el riesgo pediría más
    r = run(o, h, l, c, sig(4, 0), np.full(4, 1.0), p)
    assert r["qty"][0] * r["entry_px"][0] <= 5 * 1000 + 1e-6


def test_min_lot_skipped_when_too_risky():
    # capital 100, stop 2 % de 83.000 = 1.660 -> lote mínimo arriesga 1,66 (1,66 %) => se opera
    o, h, l, c = bars([83000] * 4, highs=[83100] * 4, lows=[82900] * 4)
    p = Params(capital=100, risk_frac=0.01, taker_fee=0, maker_fee=0, slippage=0, min_notional=0.0)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 1660.0), p)
    assert r["n_trades"] == 1 and r["qty"][0] == pytest.approx(0.001)
    # con stop del 5 % el lote mínimo arriesga 4,15 % > 2 % => se omite
    r2 = run(o, h, l, c, sig(4, 0), np.full(4, 4150.0), p)
    assert r2["n_trades"] == 0 and r2["skipped_minlot"] == 1


def test_liquidation_when_gap_jumps_past_liquidation_price():
    # 3,6x largo con stop al 25 %; la vela siguiente abre en 50 (por debajo de la liquidación ~72,7)
    o = [100, 100, 50, 50]; h = [101, 101, 51, 51]; l = [99, 99, 49, 49]
    p = Params(capital=1000, risk_frac=0.9, max_leverage=5, **ZERO)
    r = run(*bars(o, h, l), sig(4, 0), np.full(4, 25.0), p)
    assert r["reason"][0] == LIQ and r["ruined"]
    assert r["equity"][-1] == 0.0 and (r["equity"] >= 0).all()


def test_equity_never_negative_and_stop_inside_liquidation():
    # sin hueco, con 5x y stop cercano: el stop actúa antes que la liquidación
    o, h, l, c = bars([100, 100, 100, 100], lows=[99, 99, 79, 99])
    p = Params(capital=1000, risk_frac=0.05, max_leverage=5, **ZERO)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 5.0), p)
    assert r["reason"][0] == STOP and not r["ruined"]


def test_funding_long_pays_when_positive():
    o, h, l, c = bars([100] * 6)
    f = np.zeros(6); f[3] = 0.001
    p = Params(capital=1000, risk_frac=0.01, **ZERO)
    a = run(o, h, l, c, sig(6, 0), np.full(6, 10.0), p)
    b = run(o, h, l, c, sig(6, 0), np.full(6, 10.0), p, funding=f)
    assert b["funding"][0] < 0 and b["pnl"][0] < a["pnl"][0]
    s = run(o, h, l, c, sig(6, 0, -1), np.full(6, 10.0), p, funding=f)
    assert s["funding"][0] > 0                                 # el corto cobra


def test_time_exit_and_signal_exit():
    o, h, l, c = bars([100] * 8)
    p = Params(**ZERO, max_bars=2)
    r = run(o, h, l, c, sig(8, 0), np.full(8, 10.0), p)
    assert r["reason"][0] == TIME
    ex = np.zeros(8, np.int8); ex[3] = -1
    r2 = run(o, h, l, c, sig(8, 0), np.full(8, 10.0), Params(**ZERO), exit_sig=ex)
    assert r2["reason"][0] == SIGNAL and r2["exit_idx"][0] == 4


def test_accounting_identity():
    rng = np.random.default_rng(1)
    n = 3000
    ar = np.zeros(n)
    for i in range(1, n):
        ar[i] = 0.97 * ar[i - 1] + rng.normal(0, 0.006)     # serie que oscila (muchos stops)
    c = 100 * np.exp(ar)
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.0005, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.002, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.002, n)))
    s = np.where(rng.random(n) < 0.03, np.where(rng.random(n) < 0.5, 1, -1), 0)
    sd = c * 0.01
    f = rng.normal(0, 0.0001, n)
    p = Params(capital=1000, risk_frac=0.01, lot_step=1e-6, min_qty=1e-6, min_notional=0.0)
    r = run(o, h, l, c, s, sd, p, funding=f)
    assert r["n_trades"] >= 5
    assert r["equity"][-1] == pytest.approx(1000 + r["pnl"].sum(), rel=1e-9, abs=1e-6)


def _ref(o, h, l, c, s, sd, p, f):
    """Implementación independiente, lenta y sencilla, para contrastar el motor numba."""
    n = len(o); eq = p.capital; pos = 0; pend = 0; pst = 0.0; trades = []
    for i in range(n):
        if pos == 0 and pend != 0:
            d = pend; px = o[i] * (1 + d * p.slippage)
            q = (p.risk_frac * eq) / (pst + px * (2 * p.taker_fee + p.slippage))
            q = min(q, p.max_leverage * eq / px)
            q = np.floor(q / p.lot_step + 1e-9) * p.lot_step
            if q >= p.min_qty:
                pos = d; qty = q; epx = px; fee_e = qty * px * p.taker_fee
                eq -= fee_e; stop = px - d * pst; fund = 0.0
        pend = 0
        if pos != 0:
            hit = (l[i] <= stop or o[i] <= stop) if pos == 1 else (h[i] >= stop or o[i] >= stop)
            if hit:
                base = min(o[i], stop) if pos == 1 else max(o[i], stop)
                xpx = base * (1 - pos * p.slippage)
                fee = qty * xpx * p.taker_fee
                pnl = pos * qty * (xpx - epx)
                eq += pnl - fee
                trades.append(pnl - fee - fee_e + fund); pos = 0
            else:
                ff = -pos * qty * c[i] * f[i]; eq += ff; fund += ff
        if i < n - 1 and pos == 0 and s[i] != 0:
            pend = int(s[i]); pst = sd[i]
    if pos != 0:
        xpx = c[-1] * (1 - pos * p.slippage)
        fee = qty * xpx * p.taker_fee; pnl = pos * qty * (xpx - epx)
        eq += pnl - fee; trades.append(pnl - fee - fee_e + fund)
    return eq, np.array(trades)


def test_matches_independent_reference():
    rng = np.random.default_rng(7)
    for seed in range(5):
        rng = np.random.default_rng(seed)
        n = 2000
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
        o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.0007, n))
        h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.003, n)))
        l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.003, n)))
        s = np.where(rng.random(n) < 0.04, np.where(rng.random(n) < 0.5, 1, -1), 0).astype(np.int8)
        sd = c * 0.012
        f = rng.normal(0, 0.0001, n)
        p = Params(capital=5000, risk_frac=0.01, lot_step=1e-4, min_qty=1e-4, max_leverage=5, min_notional=0.0, tp_pen=0.0)
        r = run(o, h, l, c, s, sd, p, funding=f)
        eq_ref, tr_ref = _ref(o, h, l, c, s, sd, p, f)
        assert r["n_trades"] == len(tr_ref)
        assert r["equity"][-1] == pytest.approx(eq_ref, rel=1e-9)
        assert np.allclose(r["pnl"], tr_ref, rtol=1e-8, atol=1e-8)


def test_no_lookahead_prefix_invariance():
    """Cambiar el FUTURO no puede alterar el pasado: el capital hasta k debe ser idéntico."""
    rng = np.random.default_rng(3)
    n = 1500
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * 1.002; l = np.minimum(o, c) * 0.998
    s = np.where(rng.random(n) < 0.05, np.where(rng.random(n) < 0.5, 1, -1), 0).astype(np.int8)
    sd = c * 0.01
    p = Params(capital=1000, risk_frac=0.01, lot_step=1e-6, min_qty=1e-6, min_notional=0.0)
    full = run(o, h, l, c, s, sd, p, funding=np.zeros(n))
    k = 900
    o2, h2, l2, c2 = o.copy(), h.copy(), l.copy(), c.copy()
    o2[k:] *= 3; h2[k:] *= 3; l2[k:] *= 3; c2[k:] *= 3            # futuro alterado
    alt = run(o2, h2, l2, c2, s, sd, p, funding=np.zeros(n))
    assert np.array_equal(full["equity"][:k - 1], alt["equity"][:k - 1])


def test_min_notional_forces_larger_lot_and_skips_if_too_risky():
    # BTC 83.000, capital 100, mínimo nocional 100 => lote mínimo válido 0,002 BTC
    o, h, l, c = bars([83000] * 4, highs=[83100] * 4, lows=[82900] * 4)
    p = Params(capital=100, risk_frac=0.005, taker_fee=0, maker_fee=0, slippage=0, min_notional=100.0)
    r = run(o, h, l, c, sig(4, 0), np.full(4, 830.0), p, funding=np.zeros(4))   # stop 1 %
    assert r["n_trades"] == 1 and r["qty"][0] == pytest.approx(0.002)
    assert r["risk_frac_real"][0] == pytest.approx(0.002 * 830 / 100)          # 1,66 %, no 0,5 %
    r2 = run(o, h, l, c, sig(4, 0), np.full(4, 1660.0), p, funding=np.zeros(4))  # 3,3 % > 2 %
    assert r2["n_trades"] == 0 and r2["skipped_minlot"] == 1


def test_bad_stop_is_counted_not_silent():
    o, h, l, c = bars([100] * 4)
    r = run(o, h, l, c, sig(4, 0), np.array([np.nan, 1, 1, 1.0]), Params(**ZERO), funding=np.zeros(4))
    assert r["n_trades"] == 0 and r["skipped_badstop"] == 1


def test_liquidation_recomputed_after_funding():
    # 5x largo (riesgo pedido > 1 para forzar el tope de apalancamiento) con stop MÁS LEJOS que la
    # liquidación. Sin funding la liquidación está en ~80,4; el funding erosiona el margen y la sube a ~84,4.
    n = 8
    lows = [99, 99, 99, 99, 99, 99, 82, 99]
    o, h, l, c = bars([100] * n, highs=[101] * n, lows=lows)
    f = np.zeros(n); f[2:6] = 0.01
    p = Params(capital=1000, risk_frac=2.5, max_leverage=5, **ZERO)
    with_f = run(o, h, l, c, sig(n, 0), np.full(n, 50.0), p, funding=f)
    without = run(o, h, l, c, sig(n, 0), np.full(n, 50.0), p, funding=np.zeros(n))
    assert with_f["reason"][0] == LIQ            # con funding acumulado, 82 ya liquida
    assert without["reason"][0] != LIQ           # sin funding, 82 no llega a 80,4


def test_liquidated_trade_pnl_matches_equity_loss():
    n = 8
    o, h, l, c = bars([100] * n, highs=[101] * n, lows=[99, 99, 99, 99, 99, 99, 60, 99])
    f = np.zeros(n); f[3] = 0.01
    p = Params(capital=1000, risk_frac=2.5, max_leverage=5, taker_fee=0.0005, maker_fee=0.0002,
               slippage=0.0, lot_step=1e-6, min_qty=1e-6, min_notional=0.0)
    r = run(o, h, l, c, sig(n, 0), np.full(n, 50.0), p, funding=f)
    assert r["reason"][0] == LIQ
    assert r["pnl"].sum() == pytest.approx(r["equity"][-1] - 1000, abs=1e-6)  # cuadra al céntimo


def test_tp_needs_penetration_and_worst_case_curve():
    o, h, l, c = bars([100, 100, 100, 100], highs=[101, 101, 120, 101])       # el máximo TOCA el TP (120)
    p = Params(capital=1000, risk_frac=0.01, tp_mult=2.0, **{**ZERO, "tp_pen": 0.001})
    r = run(o, h, l, c, sig(4, 0), np.full(4, 10.0), p, funding=np.zeros(4))
    assert r["n_trades"] == 1 and r["reason"][0] == END                       # no se llena por solo tocar
    assert (r["equity_low"] <= r["equity"] + 1e-9).all()


def test_stress_slippage_worsens_stop_fill():
    o, h, l, c = bars([100, 100, 100, 100], lows=[99, 99, 80, 99])
    base = run(o, h, l, c, sig(4, 0), np.full(4, 10.0), Params(capital=1000, risk_frac=0.01, **ZERO), funding=np.zeros(4))
    stress = run(o, h, l, c, sig(4, 0), np.full(4, 10.0),
                 Params(capital=1000, risk_frac=0.01, **{**ZERO}, stress_range_frac=0.1), funding=np.zeros(4))
    assert stress["pnl"][0] < base["pnl"][0]
