import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.core.nucleo import (CoreParams, run_core, signal_a, signal_b, reference_bh, _simulate, ewma_vol)


def synth(n=6000, seed=0, drift=0.0002):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(drift, 0.008, n)))
    o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * 1.003; l = np.minimum(o, c) * 0.997
    idx = pd.date_range("2019-01-01", periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": 1.0}, index=idx)


def test_full_exposure_no_costs_equals_buy_and_hold():
    df = synth(); n = len(df)
    r = df["close"].pct_change().fillna(0).to_numpy()
    eq, expo, turn, fc = _simulate(r, np.r_[0.0, np.ones(n - 1)], np.r_[False, True, np.zeros(n - 2, bool)],
                                   np.zeros(n), 0.0, 0.2)
    bh = np.cumprod(1 + r)
    assert np.allclose(eq[5:] / eq[5], bh[5:] / bh[5], rtol=1e-9)          # tras entrar, idéntico a comprar y mantener


def test_switch_costs_exactly_one_side_and_exposure_drifts():
    n = 10; r = np.array([0, 0.1, 0.1, 0, 0, 0, 0, 0, 0, 0.0])
    target = np.r_[0.0, np.full(n - 1, 0.5)]
    changed = np.zeros(n, bool); changed[1] = True
    eq, expo, turn, fc = _simulate(r, target, changed, np.zeros(n), 0.0007, 0.2)
    assert turn[1] == pytest.approx(0.5)                                     # entra con 0,5 de exposición
    assert eq[1] == pytest.approx((1 - 0.5 * 0.0007) * (1 + 0.5 * 0.1))
    assert expo[2] > 0.5 * 0.999                                             # deriva al subir el precio (antes de reajustar)


def test_no_rebalance_inside_band():
    n = 6; r = np.zeros(n); target = np.r_[0.0, np.full(n - 1, 1.0)]
    target[3] = 1.1                                                          # dentro de la banda del 20 %
    changed = np.zeros(n, bool); changed[1] = True
    eq, expo, turn, fc = _simulate(r, target, changed, np.zeros(n), 0.0007, 0.2)
    assert turn[3] == 0.0 and expo[3] == pytest.approx(1.0)
    target[4] = 1.5                                                          # fuera de la banda
    eq, expo, turn, fc = _simulate(r, target, changed, np.zeros(n), 0.0007, 0.2)
    assert turn[4] == pytest.approx(0.5)


def test_funding_is_paid_by_longs_when_positive():
    n = 6; r = np.zeros(n); target = np.r_[0.0, np.full(n - 1, 1.0)]
    changed = np.zeros(n, bool); changed[1] = True
    f = np.zeros(n); f[3] = 0.001
    a = _simulate(r, target, changed, np.zeros(n), 0.0, 0.2)[0][-1]
    b = _simulate(r, target, changed, f, 0.0, 0.2)[0][-1]
    assert b == pytest.approx(a * (1 - 0.001))


def test_signal_a_uses_only_past_days_and_is_applied_next_day():
    df = synth(n=6000)
    a = signal_a(df)
    k = 2500
    df2 = df.copy(); df2.iloc[k:, df2.columns.get_indexer(["open", "high", "low", "close"])] *= 3   # futuro alterado
    a2 = signal_a(df2)
    day = df.index[k].floor("1D")
    same_upto = df.index < day + pd.Timedelta(days=1)          # incluye la propia jornada de k (usa el cierre del día previo)
    assert np.array_equal(a[same_upto], a2[same_upto])


def test_signal_b_state_causal_and_donchian_logic():
    c = np.r_[np.full(60, 100.0), 105.0, 106.0, 99.0, 90.0, np.full(10, 90.0)]
    df = pd.DataFrame({"open": c, "high": c + 0.5, "low": c - 0.5, "close": c},
                      index=pd.date_range("2024-01-01", periods=len(c), freq="4h", tz="UTC"))
    st = signal_b(df, 50)
    assert st[60] == 1.0 and st[61] == 1.0                     # rompe el máximo y se mantiene
    assert st[63] == 0.0                                       # cierra bajo el mínimo de 50 velas: sale


def test_prefix_invariance_of_whole_core():
    df = synth(n=5000); n = len(df); f = np.zeros(n)
    full = run_core(df, f)
    k = 3200
    df2 = df.copy(); cols = df2.columns.get_indexer(["open", "high", "low", "close"]); df2.iloc[k:, cols] *= 2.5
    alt = run_core(df2, f)
    assert np.allclose(full["equity"].iloc[:k].to_numpy(), alt["equity"].iloc[:k].to_numpy(), rtol=1e-12)
    assert np.allclose(full["expo"].iloc[:k + 1].to_numpy(), alt["expo"].iloc[:k + 1].to_numpy(), rtol=1e-12)


def test_vol_target_reduces_exposure_and_respects_cap():
    df = synth(n=5000); f = np.zeros(len(df))
    res = run_core(df, f)
    assert res["expo"].max() <= 2.0 * 1.6                      # el tope efectivo (2x) sólo puede excederse por deriva de precio
    assert res["expo"].mean() < 1.0
    ref = reference_bh(df, f, vol_targeted=True)
    assert len(ref) == len(df) and ref.iloc[-1] > 0
