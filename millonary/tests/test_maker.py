import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from src.maker.engine import run as run_m, Params
from src.backtest.engine import run as run_t


def _bars(c, wick=0.5):
    c = np.asarray(c, float); o = np.r_[c[0], c[:-1]]; return o, np.maximum(o, c) + wick, np.minimum(o, c) - wick, c


def test_fill_at_limit_with_maker_fee():
    o, h, l, c = _bars(np.full(30, 100.0)); e = np.zeros(30, np.int8); e[5] = 1
    r = run_m(o, h, l, c, e, np.full(30, 2.0), Params(capital=1e6, max_bars=3), funding=np.zeros(30))
    assert r["n_trades"] == 1 and r["missed"] == 0 and abs(r["entry_px"][0] - 100.0) < 1e-9
    q = r["qty"][0]; assert abs(r["fees"][0] - (q * 100 * 0.0002 + q * r["exit_px"][0] * 0.0005)) < 1e-6


def test_no_fill_when_price_runs_away_and_missed_counted():
    c = np.r_[np.full(6, 100.0), np.linspace(101, 130, 24)]; o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) + 0.1; l = np.minimum(o, c) + 0.0                       # tras la señal el mínimo nunca baja del límite
    e = np.zeros(30, np.int8); e[5] = 1
    r = run_m(o, h, l, c, e, np.full(30, 2.0), Params(capital=1e6), funding=np.zeros(30))
    assert r["n_trades"] == 0 and r["missed"] == 1
    t = run_t(o, h, l, c, e, np.full(30, 2.0), Params(capital=1e6), funding=np.zeros(30))
    assert t["n_trades"] == 1                                                     # el motor taker sí habría entrado


def test_no_tp_on_fill_bar_but_stop_allowed():
    c = np.full(20, 100.0); o, h, l, _ = _bars(c, 0.2); e = np.zeros(20, np.int8); e[5] = 1
    h[6] = 110.0                                                                  # en la vela de llenado el máximo supera el TP
    r = run_m(o, h, l, c, e, np.full(20, 2.0), Params(capital=1e6, tp_mult=1.0), funding=np.zeros(20))
    assert r["exit_idx"][0] != 6
    l2 = l.copy(); l2[6] = 90.0
    r2 = run_m(o, h, l2, c, e, np.full(20, 2.0), Params(capital=1e6, tp_mult=1.0), funding=np.zeros(20))
    assert r2["exit_idx"][0] == 6                                                # el stop sí vale en la vela de llenado


def test_original_engine_untouched():
    import inspect, src.backtest.engine as E
    s = inspect.getsource(E)
    assert "pend_lim" not in s and "missed" not in s
