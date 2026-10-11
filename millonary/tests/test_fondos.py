import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.fondos import estrategias as E
from src.fondos.data import to_daily, funding_daily


def _days(n=1500, seed=3, drift=0.0008):
    r = np.random.default_rng(seed); ret = r.normal(drift, 0.03, n) + 0.002 * np.sin(np.arange(n) / 40)
    c = 20000 * np.exp(np.cumsum(ret)); o = np.r_[c[0], c[:-1]]
    h = np.maximum(o, c) * (1 + np.abs(r.normal(0, 0.012, n))); l = np.minimum(o, c) * (1 - np.abs(r.normal(0, 0.012, n)))
    idx = pd.date_range("2019-01-01", periods=n, freq="1D", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "pclose": c * (1 + r.normal(0, 0.0005, n)),
                         "f": r.normal(0.0002, 0.0002, n), "f_real": True}, index=idx)


def test_all_strategies_are_causal_by_truncation():
    d = _days(); cut = 1100; d2 = d.copy(); d2.iloc[cut + 1:, :5] *= 1.3; d2.iloc[cut + 1:, 5] *= -2
    a, b = E.run_all(d), E.run_all(d2)
    assert len(a) == 10
    for k in a:
        assert np.allclose(a[k]["ret"].iloc[:cut + 1], b[k]["ret"].iloc[:cut + 1], rtol=0, atol=1e-12), k


def test_no_strategy_trades_before_start_and_some_trade_after():
    d = _days(); t0 = 1000; res = E.run_all(d, t0=t0); active = 0
    for k, v in res.items():
        assert np.allclose(v["ret"].iloc[:t0 - 1], 0.0, atol=1e-15), k
        assert (np.abs(v["expo"].iloc[:t0 - 1]) < 1e-15).all(), k
        active += bool(np.abs(v["ret"].iloc[t0:]).sum() > 0)
    assert active >= 8


def test_turtle_respects_unit_and_exposure_caps():
    d = _days(drift=0.003)
    for k in ("F01 Tortugas S1 (Dennis, 20/10)", "F02 Tortugas S2 (Dennis, 55/20)"):
        v = E.ESTRATEGIAS[k](d)
        assert len(v["trades"]) > 5 and v["trades"]["unidades"].between(1, 4).all()
        assert (v["expo"].abs() <= E.MAX_EXPO + 1e-6).all()
        assert v["trades"]["R"].min() > -3.5                      # 4 unidades con stop a 2N de la última: pérdida acotada


def test_carry_is_price_neutral_and_earns_funding_minus_costs():
    d = _days(); n = len(d); cost = (E.SPOT_FEE + E.SLIP) + (E.FEE + E.SLIP)
    flat = d.copy(); flat[["open", "high", "low", "close", "pclose"]] = 20000.0; flat["f"] = 0.0003
    v = E.carry(flat); r = v["ret"].to_numpy()
    assert len(v["trades"]) == 0 and v["n_ops"] <= 3                  # entra una vez y no sale (funding siempre > 0); solo reajustes de banda
    assert r[7] == pytest.approx(-cost + 0.0003, abs=1e-5)
    assert np.allclose(r[8:200], 0.0003, rtol=0.1) and (r[8:] > -cost).all()
    walk = flat.copy(); m = np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.04, n)))
    for c in ("open", "high", "low", "close", "pclose"):
        walk[c] = 20000.0 * m
    w = E.carry(walk)["ret"].iloc[8:]
    assert w.min() > -2 * cost and w.max() < 0.001                    # el precio (±4 %/día) no mueve el resultado: solo funding y reajustes
    assert (E.carry(walk)["nocional"] <= 3.0).all()                   # banda del 20 % + un día de deriva


def test_nr7_two_sided_day_is_a_full_loss():
    d = _days(300); i = 150
    d.iloc[i - 7:i - 1, d.columns.get_loc("high")] = d["close"].iloc[i - 7:i - 1] * 1.05
    d.iloc[i - 7:i - 1, d.columns.get_loc("low")] = d["close"].iloc[i - 7:i - 1] * 0.95
    c = d["close"].iloc[i - 1]; d.iloc[i - 1, :4] = [c, c * 1.001, c * 0.999, c]
    d.iloc[i, :4] = [c, c * 1.02, c * 0.98, c]
    tr = E.nr7(d)["trades"]; row = tr[tr["entrada"] == d.index[i]].iloc[0]
    assert row["motivo"].startswith("stop") and row["R"] < -0.9


def test_multi_weights_are_long_only_and_sum_to_one():
    res = E.run_all(_days())
    W = res[E.MULTI]["pesos"]
    assert (W >= 0).all().all() and (W.sum(axis=1).round(9).isin([0.0, 1.0])).all()


def test_daily_bars_need_six_4h_bars_and_funding_sums_by_day():
    i = pd.date_range("2026-01-01", periods=13, freq="4h", tz="UTC")
    b = pd.DataFrame({"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5}, index=i)
    dd = to_daily(b); assert len(dd) == 2
    ev = pd.DataFrame({"time": pd.to_datetime(["2026-01-01 08:00", "2026-01-01 16:00", "2026-01-02 00:00", "2026-01-02 08:00"], utc=True),
                       "funding_rate": [1e-4, 2e-4, 3e-4, 4e-4], "synthetic": [False, False, True, False]})
    f, real = funding_daily(dd.index, ev)
    assert np.allclose(f, [6e-4, 4e-4]) and list(real) == [False, True]


def test_gap_fill_keeps_real_price_levels():
    from src.fondos.data import _grid
    i = pd.date_range("2018-02-07", periods=30, freq="4h", tz="UTC"); i = i[(i < "2018-02-08") | (i >= "2018-02-11")]
    b = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0}, index=i); b.loc[b.index >= "2018-02-11", ["open", "high", "low", "close"]] = 80.0
    g = _grid(b)
    assert len(g) == 30 and (g.loc[g.index >= "2018-02-11", "close"] == 80.0).all()      # sin reescalar el tramo posterior
    assert (g.loc[(g.index >= "2018-02-08") & (g.index < "2018-02-11"), "close"] == 100.0).all()
