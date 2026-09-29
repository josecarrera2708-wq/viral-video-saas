import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.intraday.setups import all_specs, SETUPS
from src.intraday import forward as fw
from src.intraday.evaluate import mc_band, stress
from src.backtest.engine import Params


def bars1h(n=2500, seed=3):
    rng = np.random.default_rng(seed); c = 60000 * np.exp(np.cumsum(rng.normal(0, 0.004, n))); o = np.r_[c[0], c[:-1]]
    idx = pd.date_range("2026-06-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.002, "low": np.minimum(o, c) * 0.998, "close": c, "volume": rng.uniform(50, 500, n)}, index=idx)


def test_specs_are_causal_and_well_formed():
    df = bars1h(); cut = 1800; d2 = df.copy(); d2.iloc[cut + 1:, d2.columns.get_indexer(["open", "high", "low", "close"])] *= 1.4
    a, b = all_specs(df), all_specs(d2); assert len(a) == 14
    for k in a:
        assert np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]), k
        assert np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True), k
        assert set(np.unique(a[k].entry)) <= {-1, 0, 1} and a[k].tp_mult >= 0 and a[k].max_bars > 0
        st = a[k].stop[a[k].entry != 0]; assert (st[~np.isnan(st)] > 0).all(), k


def test_once_per_day_setups_never_fire_twice_a_day():
    df = bars1h(4000); sp = all_specs(df)
    for k in ("I01 Rango asiático → Londres/NY", "I08 Ruptura del máx./mín. de ayer"):
        e = pd.Series(sp[k].entry != 0, index=df.index).groupby(df.index.floor("1D")).sum(); assert e.max() <= 1, k


def test_fetch_uses_only_closed_bars_and_forward_is_flat_before_start():
    df = bars1h(1000); now = df.index[-1] + pd.Timedelta("30min")           # la última vela aún está formándose
    ms = lambda t: int(t.timestamp() * 1000)
    def get(url, p):
        if "chart" in url:
            return {"result": {"ticks": [ms(t) for t in df.index], "open": df.open.tolist(), "high": df.high.tolist(), "low": df.low.tolist(), "close": df.close.tolist(), "volume": df.volume.tolist()}}
        return {"result": [{"timestamp": ms(t), "interest_1h": 1e-6} for t in df.index]}
    got = fw.fetch_bars(df.index[700], now, get=get); assert got.index[-1] == df.index[-2]           # descarta la vela en formación
    f = fw.fetch_funding(got.index, now, get=get); assert len(f) == len(got) and f.max() > 0
    start = got.index[-200] + pd.Timedelta("1h"); res = fw.run_all(got, f, start)
    for k, r in res.items():
        assert (np.asarray(r["entry_idx"]) >= np.argmax(got.index + pd.Timedelta("1h") >= start)).all(), k       # ninguna entrada antes del inicio
    summ, allt = fw.summarize_all(got, res, start, now); assert set(summ) == set(SETUPS) and all(v["por_dia"] >= 0 for v in summ.values())


def test_cost_stress_and_mc_band():
    b = Params(); s = stress(2.0); assert s.taker_fee == 2 * b.taker_fee and s.slippage == 2 * b.slippage
    R = np.r_[np.full(60, 1.5), np.full(140, -1.0)]; m = mc_band(R, n=500); assert m["dd_p95"] >= m["dd_p50"] > 0 and m["ret_p5"] <= m["ret_p95"]


def test_improvement_operators_only_restrict_or_scale_and_stay_causal():
    from src.intraday.mejora import OPERADORES
    df = bars1h(); base = all_specs(df); cut = 1800; d2 = df.copy(); d2.iloc[cut + 1:, d2.columns.get_indexer(["open", "high", "low", "close"])] *= 1.4
    b2 = all_specs(d2)
    for k in ("I02 Ruptura Donchian 24 h", "I05 Cruce EMA 9/21 + EMA200", "I10 Ráfaga de momentum"):
        for on, fn in OPERADORES.items():
            v, v2 = fn(df, base[k]), fn(d2, b2[k])
            assert np.array_equal(v.entry[:cut + 1], v2.entry[:cut + 1]), (k, on)                      # causal
            if on in ("M1 a favor de la tendencia", "M3 sesión 07-21 UTC", "M4 stop mínimo 0,8 %"):
                assert ((v.entry != 0) <= (base[k].entry != 0)).all(), (k, on)                        # solo elimina entradas, nunca añade
