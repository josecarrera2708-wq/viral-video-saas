import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.incubator.setups import all_states, SETUPS
from src.incubator.sim import simulate, trades, simulate_pos
from src.incubator.factors import regress, holm, benjamini_hochberg, trend_factor
from src.incubator.allocate import allocate
from src.incubator.forward import forward_run
from src.desk.opciones import analyze_chain
from src.desk.chat import feed, ask
from test_desk import synth


def test_setups_are_causal():
    """El estado en la vela i no cambia si se alteran las velas futuras."""
    df = synth(1500); S = all_states(df)
    cut = 900; df2 = df.copy(); df2.iloc[cut + 1:, df2.columns.get_indexer(["open", "high", "low", "close"])] *= 1.7
    S2 = all_states(df2)
    for k in S:
        assert np.allclose(S[k].iloc[:cut + 1].to_numpy(), S2[k].iloc[:cut + 1].to_numpy()), k


def test_states_in_range_and_15_setups():
    S = all_states(synth(1500)); assert S.shape[1] == 15 == len(SETUPS)
    assert set(np.unique(S.to_numpy())) <= {-1.0, 0.0, 1.0}


def test_sim_no_lookahead_and_costs():
    df = synth(600); st = np.ones(len(df)); f = np.zeros(len(df))
    r = simulate(df, st, f, cost=0.0)
    assert r["pos"].iloc[0] == 0 and (r["pos"].iloc[1:] == 1).all()
    assert np.allclose(r["ret"].iloc[1:], df["close"].pct_change().iloc[1:])
    r2 = simulate(df, st, f, cost=0.001); assert r2["ret"].sum() < r["ret"].sum()
    # corto cobra funding positivo
    fs = np.full(len(df), 0.0001); rs = simulate(df, -st, fs, cost=0.0)
    assert (rs["ret"].iloc[1:] + df["close"].pct_change().iloc[1:]).mean() > 0


def test_trades_segments():
    df = synth(200); st = np.zeros(len(df)); st[10:20] = 1; st[30:40] = -1
    t = trades(simulate(df, st, np.zeros(len(df)), cost=0.0)); assert list(t["side"]) == [1, -1] and list(t["bars"]) == [10, 10]


def test_multiple_comparison_corrections():
    p = np.array([0.001, 0.02, 0.5, 0.9]); h = holm(p); b = benjamini_hochberg(p)
    assert h[0] == pytest.approx(0.004) and (h >= p).all() and (b <= h + 1e-12).all() and (b >= p).all()


def test_regression_recovers_beta_and_alpha():
    rng = np.random.default_rng(0); n = 1500; idx = pd.date_range("2020-01-01", periods=n, freq="1D", tz="UTC")
    btc = pd.Series(rng.normal(0.0005, 0.03, n), index=idx); tr = pd.Series(rng.normal(0, 0.02, n), index=idx, name="trend")
    y = 0.001 + 0.5 * btc + 0.3 * tr + pd.Series(rng.normal(0, 0.01, n), index=idx)
    r = regress(y, btc, tr); assert abs(r["beta_btc"] - 0.5) < 0.05 and abs(r["beta_tend"] - 0.3) < 0.08 and r["t_alpha"] > 2


def test_allocation_defaults_to_core_and_caps():
    assert allocate({"certificadas": []}) == {"núcleo v1": 1.0}
    res = {"certificadas": ["a", "b", "c"], "setups": {k: {"retorno_anual_full": .2, "sharpe_full": 1.0, "p_holm": .05} for k in "abc"}}
    w = allocate(res); assert w["núcleo v1"] >= 0.5 - 1e-9 and abs(sum(w.values()) - 1) < 1e-9 and max(v for k, v in w.items() if k != "núcleo v1") <= .25


def test_forward_starts_flat_and_ignores_past():
    df = synth(1500); start = df.index[1200] + pd.Timedelta("4h")
    f = pd.DataFrame({"time": df.index + pd.Timedelta("4h"), "funding_rate": 0.0001})
    out = forward_run(df, f, start); assert len(out) == 15
    # cambiar el pasado previo al inicio no altera el hacia delante de los setups con memoria corta si están planos al inicio
    assert all(v["dias"] > 0 for v in out.values()) and all(-1 <= v["retorno"] for v in out.values())
    assert forward_run(df, f, None) == {}


def test_options_chain_math():
    now = pd.Timestamp("2026-09-29", tz="UTC"); S = 100000.0; book = []
    for K in (80000, 90000, 100000, 110000, 120000):
        for t in ("P", "C"):
            book.append({"instrument_name": f"BTC-30OCT26-{K}-{t}", "mark_iv": 40.0 + (5 if (t == "P" and K < S) else 0), "mark_price": 0.02, "underlying_price": S})
    ch = analyze_chain(book, now); assert ch and 0.3 < ch["iv_atm"] < 0.5 and ch["put10_strike"] == 90000 and ch["put10_coste_pct"] == pytest.approx(0.02)
    assert analyze_chain([], now) is None


def test_chat_feed_and_ask():
    s = {"ts": "2026-09-30 04:17:00+00:00", "decision": "Mantener 0.3×", "veto": False,
         "departamentos": [{"dept": "Riesgos", "headline": "Todo bien", "status": "OK", "notes": ["Caída máxima 2 %", "Pérdida diaria 0 %"], "shadow": []},
                           {"dept": "Macroeconomía", "headline": "RISK-ON", "status": "OK", "notes": ["Fear & Greed 74"], "shadow": ["x"]}]}
    m = feed(s); assert m[0]["de"] == "Dirección" and m[-1]["canal"] == "Comité" and any(x["canal"] == "Riesgos" for x in m)
    assert all(x["canal"] == "Macro" or x["de"] == "Macroeconomía" for x in feed(s, "Macro"))
    assert "Caída máxima" in ask(s, "riesgos", "¿cuál es la caída máxima?") and "No conozco" in ask(s, "xyz", "hola")
