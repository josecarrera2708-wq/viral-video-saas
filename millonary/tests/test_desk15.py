import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd
from src.desk15 import data, setups
from src.desk15.learner import gate, base_trades, context15, _cum_stats, veto_state, level_ids
from src.intraday.setups import Spec


def synth(n=6000, seed=3):
    rng = np.random.default_rng(seed); idx = pd.date_range("2024-01-01", periods=n, freq="15min", tz="UTC")
    c = 30000 * np.exp(np.cumsum(rng.normal(0, 0.0015, n))); o = np.r_[c[0], c[:-1]]; sp = np.abs(rng.normal(0, 0.0012, n)) * c
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) + sp, "low": np.minimum(o, c) - sp, "close": c, "volume": rng.uniform(50, 500, n)}, index=idx)


def test_all_setups_are_causal_truncation():
    df = synth(); cut = 4000; d2 = df.copy(); cols = d2.columns.get_indexer(["open", "high", "low", "close"]); d2.iloc[cut + 1:, cols] *= 1.37
    a, b = setups.all_specs(df), setups.all_specs(d2)
    for k in a:
        assert np.array_equal(a[k].entry[:cut + 1], b[k].entry[:cut + 1]), k
        assert np.allclose(a[k].stop[:cut + 1], b[k].stop[:cut + 1], equal_nan=True), k


def test_setups_emit_some_signals_and_valid_stops():
    df = synth(20000)
    for k, sp in setups.all_specs(df).items():
        assert set(np.unique(sp.entry)) <= {-1, 0, 1}, k
        s = np.nan_to_num(sp.stop[sp.entry != 0], nan=0.0)
        assert (s >= 0).all(), k


def test_learner_veto_is_causal_and_relative():
    df = synth(3000); ctx = context15(df); n = len(df)
    # 12 operaciones perdedoras CERRADAS en el nivel «sesión Asia» (y 12 ganadoras fuera): el veto debe aparecer solo DESPUÉS de cerrarse
    lv_bad, lv_ok = (1, 1, 0), (1, 1, 1)
    tr = [(100 + 10 * i, lv_bad, -1.0) for i in range(12)] + [(100 + 10 * i, lv_ok, +0.5) for i in range(12)]
    cnt, s, ss = _cum_stats(tr, n); vs = veto_state(cnt, s, ss, 6)
    k = 2 * 3 + 0                                                       # dimensión sesión, nivel Asia
    assert not vs[k, :150].any() and vs[k, 400:].all()                  # antes de acumular evidencia no hay veto; después sí
    assert not vs[2 * 3 + 1, 400:].any()                                # el nivel bueno no se veta


def test_gate_removes_only_vetoed_signals_and_keeps_stops():
    df = synth(3000); ctx = context15(df); n = len(df); ent = np.zeros(n, np.int8); ent[1500::50] = 1
    sp = Spec(ent, np.full(n, 100.0), tp_mult=2.0, max_bars=10)
    tr = [(100 + 10 * i, (1, 1, k), -1.0 if k == 0 else 0.5) for i in range(12) for k in (0, 1)]
    g, vs = gate(sp, df, ctx, tr, 6)
    assert (g.entry != 0).sum() <= (ent != 0).sum() and np.array_equal(g.stop, sp.stop)
    assert ((g.entry != 0) <= (ent != 0)).all()


def test_fetch_bars_paginates_backwards_and_keeps_closed_only():
    calls = []
    full = pd.date_range("2026-01-01", periods=12000, freq="15min", tz="UTC")

    def get(path, p):
        calls.append(path); end = pd.Timestamp(p["end_timestamp"], unit="ms", tz="UTC"); t = full[full <= end][-5000:]
        ms = [int(x.timestamp() * 1000) for x in t]; v = list(np.arange(len(t), dtype=float))
        return {"ticks": ms, "open": v, "high": v, "low": v, "close": v, "volume": v}
    now = full[-1] + pd.Timedelta("7min")
    df = data.fetch_bars(full[0], now, get=get)
    assert len(calls) >= 3 and df.index.is_monotonic_increasing and not df.index.duplicated().any()
    assert df.index[-1] + data.M15 <= now and df.index[0] == full[0]      # la última vela abierta (cierra después de now) se descarta


def test_funding_per_candle_quarter_of_hourly_rate():
    idx = pd.date_range("2026-01-01 00:00", periods=8, freq="15min", tz="UTC")             # 2 horas
    rows = [{"timestamp": int(pd.Timestamp("2026-01-01 01:00", tz="UTC").timestamp() * 1000), "interest_1h": 4e-5},
            {"timestamp": int(pd.Timestamp("2026-01-01 02:00", tz="UTC").timestamp() * 1000), "interest_1h": 8e-5}]
    f = data.fetch_funding(idx, idx[-1] + data.M15, get=lambda p, q: rows)
    assert np.allclose(f[:4], 1e-5) and np.allclose(f[4:], 2e-5)
