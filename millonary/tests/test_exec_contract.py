import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd, pytest
from src.exec.base import OrderRequest, ExchangeError, Fill, BUY, SELL, MARKET, LIMIT, STOP
from src.exec.paper import PaperExchange
from src.exec.guard import RiskGuard, GuardConfig, live_approved
from src.exec.executor import Executor
from src.exec.reconcile import slippage_report, compare_to_sim
from src.exec.margex import MargexExchange

T0 = pd.Timestamp("2026-10-01 00:00", tz="UTC"); H = pd.Timedelta("1h")


def make_paper(capital=1000.0):
    ex = PaperExchange(capital); ex.on_bar(T0, 100.0, 100.0, 100.0, 100.0); return ex


ADAPTERS = [make_paper]          # todo adaptador nuevo (demo/real) debe pasar este mismo contrato


@pytest.mark.parametrize("make", ADAPTERS)
def test_contract_market_roundtrip_and_accounting(make):
    ex = make(); assert ex.ping() and ex.equity() == pytest.approx(1000.0)
    ex.place(OrderRequest("a", "BTCUSDT", BUY, 2.0))
    p = ex.position("BTCUSDT"); assert p.qty == 2.0 and p.entry_px > 100.0          # deslizamiento en contra
    ex.place(OrderRequest("b", "BTCUSDT", SELL, 2.0, reduce_only=True)); assert ex.position("BTCUSDT").qty == 0
    fills = ex.fills(); assert len(fills) == 2 and all(f.fee > 0 for f in fills)
    assert ex.equity() < 1000.0                                                     # ida y vuelta sin movimiento = solo costes
    assert ex.equity() == pytest.approx(1000.0 - sum(f.fee for f in fills) - 2.0 * (fills[0].price - 100.0) - 2.0 * (100.0 - fills[1].price), abs=1e-6)


@pytest.mark.parametrize("make", ADAPTERS)
def test_contract_rejections(make):
    ex = make()
    ex.place(OrderRequest("a", "BTCUSDT", BUY, 1.0))
    with pytest.raises(ExchangeError): ex.place(OrderRequest("a", "BTCUSDT", BUY, 1.0))                  # client_id duplicado
    with pytest.raises(ExchangeError): ex.place(OrderRequest("z", "BTCUSDT", BUY, 0.0))                  # cantidad nula
    with pytest.raises(ExchangeError): ex.place(OrderRequest("y", "BTCUSDT", BUY, 1.0, reduce_only=True))  # reduce_only aumentando
    assert ex.cancel("nope") is False


@pytest.mark.parametrize("make", ADAPTERS)
def test_contract_stop_gap_tp_penetration_and_cleanup(make):
    ex = make(); ex.place(OrderRequest("e", "BTCUSDT", BUY, 1.0))
    ex.place(OrderRequest("s", "BTCUSDT", SELL, 1.0, STOP, 95.0, True)); ex.place(OrderRequest("t", "BTCUSDT", SELL, 1.0, LIMIT, 110.0, True))
    assert ex.on_bar(T0 + H, 100.0, 110.0, 99.0, 105.0) == []                        # toca 110 exacto: no penetra el TP
    out = ex.on_bar(T0 + 2 * H, 100.0, 110.5, 99.0, 105.0); assert [f.reason for f in out] == ["tp"] and ex.position("x").qty == 0
    assert ex.open_orders("BTCUSDT") == []                                           # el stop restante se anula al quedar plano
    ex2 = make(); ex2.place(OrderRequest("e", "BTCUSDT", BUY, 1.0)); ex2.place(OrderRequest("s", "BTCUSDT", SELL, 1.0, STOP, 95.0, True))
    out = ex2.on_bar(T0 + H, 90.0, 92.0, 88.0, 91.0)                                 # hueco: abre bajo el stop
    assert out[0].reason == "stop" and out[0].price < 90.0 and out[0].price == pytest.approx(90.0 * (1 - ex2.slip))


@pytest.mark.parametrize("make", ADAPTERS)
def test_contract_stop_beats_tp_on_same_bar_and_short_side(make):
    ex = make(); ex.place(OrderRequest("e", "BTCUSDT", SELL, 1.0))
    ex.place(OrderRequest("s", "BTCUSDT", BUY, 1.0, STOP, 105.0, True)); ex.place(OrderRequest("t", "BTCUSDT", BUY, 1.0, LIMIT, 90.0, True))
    out = ex.on_bar(T0 + H, 100.0, 106.0, 89.0, 100.0); assert [f.reason for f in out] == ["stop"]


def test_paper_liquidation_wipes_margin():
    ex = make_paper(100.0); ex.place(OrderRequest("e", "BTCUSDT", BUY, 1.9))           # ~1,9× de apalancamiento
    ex.on_bar(T0 + H, 100.0, 100.0, 40.0, 45.0)
    assert ex.position("x").qty == 0 and ex.equity() == 0.0 and "liquidacion" in ex.events


def test_guard_leverage_size_symbol_rate_and_idempotent_executor():
    ex = make_paper(); g = RiskGuard(ex, GuardConfig(max_leverage=2.0, max_order_notional=1500.0, max_orders_per_min=50, kill_file=pathlib.Path("/nonexistent/KILL")), now=lambda: T0)
    assert not g.check(OrderRequest("a", "BTCUSDT", BUY, 25.0), 100.0).ok                       # 2.500 USDT > 1.500 por orden
    assert g.check(OrderRequest("a", "BTCUSDT", BUY, 15.0), 100.0).ok                            # 1.500 USDT y 1,5× → pasa
    assert not g.check(OrderRequest("a", "BTCUSDT", BUY, 21.0), 100.0).ok                       # 2,1× > 2×
    assert "símbolo" in g.check(OrderRequest("a", "ETHUSDT", BUY, 1.0), 100.0).reason
    e = Executor(ex, g, min_notional=10.0)
    r1 = e.set_target("core", T0, 3.0, stop=95.0, tp=110.0); assert r1["estado"] == "ok" and ex.position("x").qty == pytest.approx(3.0)
    assert len([o for o in ex.open_orders("x")]) == 2
    assert e.set_target("core", T0, 3.0, stop=95.0)["estado"] == "ya_enviada"                    # idempotente: no duplica
    assert e.set_target("core", T0 + H, 3.0)["estado"] == "rechazada"                             # sin stop no se opera
    r3 = e.set_target("core", T0 + 2 * H, -2.0, stop=105.0); assert ex.position("x").qty == pytest.approx(-2.0)          # invierte: cierra y abre
    assert all(o.reduce_only and o.side == BUY for o in ex.open_orders("x")) and len(ex.open_orders("x")) == 1            # protecciones renovadas


def test_guard_kill_switch_and_daily_loss_only_allow_reducing(tmp_path):
    ex = make_paper(); kill = tmp_path / "KILL"; clock = {"t": T0}
    g = RiskGuard(ex, GuardConfig(kill_file=kill, daily_loss_halt=0.05), now=lambda: clock["t"]); ex.place(OrderRequest("a", "BTCUSDT", BUY, 5.0))
    kill.write_text("x"); assert not g.check(OrderRequest("b", "BTCUSDT", BUY, 1.0), 100.0).ok
    assert g.check(OrderRequest("c", "BTCUSDT", SELL, 5.0, reduce_only=True), 100.0).ok        # cerrar siempre se puede
    kill.unlink(); g.halted = False
    ex.on_bar(T0 + H, 100.0, 100.0, 89.0, 90.0)                                                  # -50 USDT ≈ -5 %
    assert not g.check(OrderRequest("d", "BTCUSDT", BUY, 1.0), 90.0).ok and g.reason == "pérdida diaria"
    clock["t"] = T0 + pd.Timedelta("1D"); ex.place(OrderRequest("e", "BTCUSDT", SELL, 5.0, reduce_only=True))
    assert g.check(OrderRequest("f", "BTCUSDT", BUY, 1.0), 90.0).ok                               # día nuevo: la parada se rearma


def test_live_mode_is_blocked_without_owner_approval(tmp_path, monkeypatch):
    class Live(PaperExchange):
        mode = "live"
    ex = Live(1000.0); ex.on_bar(T0, 100.0, 100.0, 100.0, 100.0); appr = tmp_path / "live_approval.json"
    cfg = GuardConfig(approval_file=appr, kill_file=tmp_path / "KILL"); g = RiskGuard(ex, cfg, now=lambda: T0)
    monkeypatch.delenv("MILLONARY_ALLOW_LIVE", raising=False)
    assert "bloqueado" in g.check(OrderRequest("a", "BTCUSDT", BUY, 1.0), 100.0).reason
    monkeypatch.setenv("MILLONARY_ALLOW_LIVE", "1"); assert not g.check(OrderRequest("a", "BTCUSDT", BUY, 1.0), 100.0).ok          # falta el fichero
    appr.write_text(json.dumps({"approved_by": "owner", "expires": "2026-12-31", "max_order_notional": 200, "max_leverage": 1.0}))
    assert live_approved(cfg, T0)[0] and g.check(OrderRequest("b", "BTCUSDT", BUY, 1.0), 100.0).ok
    assert not g.check(OrderRequest("c", "BTCUSDT", BUY, 3.0), 100.0).ok                          # 300 USDT > 200 aprobados
    assert not live_approved(cfg, pd.Timestamp("2027-01-02", tz="UTC"))[0]                        # caducada
    assert g.check(OrderRequest("d", "BTCUSDT", SELL, 1.0, reduce_only=True), 100.0).ok


def test_reconcile_slippage_and_sim_comparison():
    mk = lambda cid, side, px, ref: Fill(cid, T0, "BTCUSDT", side, 1.0, px, 0.1, False, "fill", ref)
    fills = [mk("a", BUY, 100.05, 100.0), mk("b", SELL, 99.90, 100.0)]                             # ambos peores: +5 pb y +10 pb
    r = slippage_report(fills, 2.0); assert r["n"] == 2 and r["media_pb"] == pytest.approx(7.5) and r["peor_que_modelo"]
    c = compare_to_sim([mk("a", BUY, 100.02, None), mk("z", BUY, 1, None)], [mk("a", BUY, 100.05, None)])
    assert c["emparejadas"] == 1 and c["sin_ejecucion_real"] == ["z"] and c["diff_media_pb"] == pytest.approx(3.0, abs=0.01)


def test_margex_adapter_refuses_until_docs_exist():
    with pytest.raises(NotImplementedError): MargexExchange()
