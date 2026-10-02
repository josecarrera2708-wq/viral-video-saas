import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.cartera import gestor as G


def _R(n=900, k=5, seed=1):
    r = np.random.default_rng(seed); idx = pd.date_range("2020-01-01", periods=n, freq="1D", tz="UTC")
    vol = np.array([0.01, 0.02, 0.03, 0.005, 0.04])[:k]
    return pd.DataFrame(r.normal(0.0003, 1, (n, k)) * vol, index=idx, columns=[f"s{i}" for i in range(k)])


def test_hrp_sums_one_positive_and_favours_low_vol():
    R = _R(); w = G.hrp_weights(R)
    assert abs(w.sum() - 1) < 1e-12 and (w > 0).all()
    assert w["s3"] == w.max() and w["s4"] == w.min()


def test_hrp_two_assets_equals_inverse_variance():
    R = _R(k=2); w = G.hrp_weights(R); v = R.var(); iv = (1 / v) / (1 / v).sum()
    assert np.allclose(w.values, iv.values)


def test_schedule_is_causal_and_monthly():
    R = _R(); cut = 500; R2 = R.copy(); R2.iloc[cut + 1:] *= -3
    for m in ("hrp", "iv"):
        a, b = G.schedule(R, m), G.schedule(R2, m)
        assert np.allclose(a.iloc[:cut + 2], b.iloc[:cut + 2])
        ch = a.diff().abs().sum(axis=1) > 0
        assert (pd.Series(G.month_end(R.index), index=R.index).shift(1).fillna(False)[ch]).all()


def test_combine_and_overlay_are_causal():
    R = _R(); W = G.schedule(R, "hrp"); r, _ = G.combine(R, W); cut = 600
    R2 = R.copy(); R2.iloc[cut + 1:] = -0.2; r2, _ = G.combine(R2, G.schedule(R2, "hrp"))
    o, m = G.dd_overlay(r); o2, m2 = G.dd_overlay(r2)
    assert np.allclose(o.iloc[:cut + 1], o2.iloc[:cut + 1]) and np.allclose(m.iloc[:cut + 2], m2.iloc[:cut + 2])


def test_overlay_cuts_exposure_in_drawdown_and_recovers():
    idx = pd.date_range("2020-01-01", periods=200, freq="1D", tz="UTC")
    r = pd.Series(0.0, index=idx); r.iloc[10:40] = -0.01; r.iloc[60:160] = 0.01
    _, m = G.dd_overlay(r)
    assert m.iloc[0] == 1 and m.min() == 0.25 and m.iloc[-1] == 1 and set(np.unique(m)) <= {0.25, 0.5, 0.75, 1.0}


def test_cvar_and_boot():
    r = pd.Series(np.r_[np.full(95, 0.01), np.full(5, -0.1)])
    assert abs(G.cvar(r) - 0.1) < 1e-12
    R = _R(n=1500); good = R["s0"] + 0.002; assert G.boot_sharpe_diff(good, R["s0"], n=300) < 0.05
    assert G.boot_sharpe_diff(R["s0"], R["s0"] + 0.002, n=300) > 0.5


def test_cpcv_splits_purge_and_embargo():
    sp = list(G.cpcv_splits(120, 6, 2, embargo=5))
    assert len(sp) == 15
    for tr, te in sp:
        assert not set(tr) & set(te) and len(te) == 40
        for e in te:
            if e + 1 not in te and e + 1 < 120:
                assert not set(range(e + 1, min(120, e + 6))) & set(tr)
