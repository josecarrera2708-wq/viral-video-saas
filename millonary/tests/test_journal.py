import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.live.config import LiveConfig, RiskLimits
from src.live.journal import build_journal
from src.live.store import Store
from src.live.trader import PaperTrader

H4 = pd.Timedelta("4h")


def synth(n=2400, seed=3, drift=0.0004):
    rng = np.random.default_rng(seed)
    c = 30000 * np.exp(np.cumsum(rng.normal(drift, 0.012, n)))
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.004, "low": np.minimum(o, c) * 0.996, "close": c, "volume": 1.0}, index=idx)


def run(seed, capital=100000.0, lot=1e-6, funding_rate=0.0):
    bars = synth(seed=seed); d = pathlib.Path(tempfile.mkdtemp())
    cfg = LiveConfig(capital=capital, data_dir=d, min_history_bars=300, lot_step=lot, min_qty=lot, min_notional=0.0,
                     risk=RiskLimits(dd_halt=9, daily_loss_halt=9))
    tr = PaperTrader(cfg, Store(d / "s.db"))
    ev = pd.DataFrame({"time": bars.index[1000:] + H4, "funding_rate": funding_rate})
    for i in range(1000, len(bars)):
        tr.step(bars.iloc[: i + 1], ev, bars.index[i] + H4 + pd.Timedelta(seconds=60))
    return tr, cfg


@pytest.mark.parametrize("seed", [1, 2, 3, 4])
def test_journal_reconciles_with_equity_to_the_cent(seed):
    tr, cfg = run(seed, funding_rate=0.0001)
    j = build_journal(tr.st, cfg.capital)
    assert len(j["orders"]) > 5 and len(j["lots"]) > 2
    assert j["cuadre"]["ok"], j["cuadre"]                                            # equity final - capital = suma P&L de lotes
    eq = pd.DataFrame(tr.st.rows("equity"))
    assert j["lots"]["pnl_usdt"].sum() == pytest.approx(eq["equity"].iloc[-1] - cfg.capital, abs=0.01)


def test_every_closed_lot_and_position_is_labeled_win_or_loss():
    tr, cfg = run(2)
    j = build_journal(tr.st, cfg.capital)
    cl = j["lots"][j["lots"]["estado"] == "CERRADO"]
    assert set(cl["resultado"]) <= {"GANA", "PIERDE"} and ((cl["pnl_usdt"] > 0) == (cl["resultado"] == "GANA")).all()
    ce = j["episodes"][j["episodes"]["estado"] == "CERRADA"]
    assert set(ce["resultado"]) <= {"GANA", "PIERDE"}
    r = j["resumen"]["lotes_cerrados"]
    assert r["n"] == len(cl) and r["ganan"] + r["pierden"] == r["n"] and 0 <= r["tasa_acierto"] <= 1
    # MAE <= 0 <= MFE por construcción de las excursiones
    assert (j["lots"]["mfe_pct"] >= -1e-12).all() and (j["lots"]["mae_pct"] <= 1e-12).all()


def test_positions_add_up_to_total_pnl_when_all_closed():
    tr, cfg = run(4)
    j = build_journal(tr.st, cfg.capital)
    ep = j["episodes"]
    assert ep["pnl_usdt"].sum() == pytest.approx(pd.DataFrame(tr.st.rows("equity"))["equity"].iloc[-1] - cfg.capital, abs=0.01)


def test_journal_of_empty_account_is_safe():
    d = pathlib.Path(tempfile.mkdtemp()); st = Store(d / "s.db")
    j = build_journal(st, 1000.0)
    assert j["resumen"]["lotes_cerrados"]["n"] == 0 and j["cuadre"]["ok"]
