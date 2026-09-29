import sys, pathlib, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.desk.base import Context, OK, AVISO, ALERTA
from src.desk.committee import sesion, markdown, ROSTER
from src.desk.departments import riesgos, macro, analisis, cartera, mesa, derivados, infra
from src.desk.events import parse_fomc, next_event, event_study
from src.desk.lab import laboratorio, run_from, SHADOWS
from src.desk.school import escuela, _tags_at
from src.live.config import LiveConfig, RiskLimits
from src.live.journal import build_journal
from src.live.store import Store
from src.live.trader import PaperTrader
from src.core.nucleo import CoreParams, run_core

H4 = pd.Timedelta("4h")


def synth(n=4200, seed=5, drift=0.0004):
    rng = np.random.default_rng(seed)
    c = 30000 * np.exp(np.cumsum(rng.normal(drift, 0.012, n)))
    o = np.r_[c[0], c[:-1]]
    idx = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    return pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.004, "low": np.minimum(o, c) * 0.996, "close": c, "volume": 1.0}, index=idx)


def make_ctx(kill=False, halt=False):
    bars = synth(); d = pathlib.Path(tempfile.mkdtemp())
    cfg = LiveConfig(capital=100000.0, data_dir=d, min_history_bars=300, risk=RiskLimits(dd_halt=0.99, daily_loss_halt=0.99))
    tr = PaperTrader(cfg, Store(d / "s.db"))
    fund = pd.DataFrame({"time": bars.index + H4, "funding_rate": 0.0001})
    for i in range(3300, len(bars)):
        tr.step(bars.iloc[: i + 1], fund, bars.index[i] + H4 + pd.Timedelta(seconds=60))
    if kill: (d / "KILL").write_text("x"); tr.step(bars, fund, bars.index[-1] + 2 * H4)
    days = pd.date_range(bars.index[-1].floor("D") - pd.Timedelta(days=700), periods=700, freq="1D", tz="UTC")
    rng = np.random.default_rng(1)
    macro_d = {"fng": pd.Series(np.clip(50 + np.cumsum(rng.normal(0, 3, 700)) % 100, 0, 100), index=days),
               "vix": pd.Series(15 + np.abs(rng.normal(0, 3, 700)), index=days), "y10": pd.Series(4.0 + rng.normal(0, .1, 700), index=days),
               "y2": pd.Series(4.2 + rng.normal(0, .1, 700), index=days), "usd": pd.Series(120 + np.cumsum(rng.normal(0, .05, 700)), index=days)}
    ev = pd.DataFrame({"time": [bars.index[-1] + H4 + pd.Timedelta(hours=6), bars.index[-1] + pd.Timedelta(days=30)], "type": "FOMC", "impact": "alto"})
    ctx = Context(now=bars.index[-1] + H4 + pd.Timedelta(seconds=60), bars=bars, cfg=cfg, store=tr.st, journal=build_journal(tr.st, cfg.capital),
                  funding_events=fund, macro=macro_d, events=ev, feed_source="test", lab_start=bars.index[3300] + H4)
    return ctx, tr


def test_every_department_reports_with_real_content():
    ctx, tr = make_ctx()
    for fn in (riesgos, macro, analisis, cartera, mesa, derivados, infra, laboratorio, escuela):
        r = fn(ctx)
        assert r.dept and r.headline and r.status in (OK, AVISO, ALERTA) and r.notes, fn.__name__
    m = macro(ctx); assert "horas_al_proximo_evento" in m.metrics and m.status in (AVISO, ALERTA)         # evento en 6 h
    a = analisis(ctx); assert set(a.metrics["retorno_por_horizonte"]) <= {20, 60, 120, 250} and "donchian50" in a.metrics
    c = cartera(ctx); assert c.metrics["objetivo"] >= 0 and abs(c.metrics["senal"] - (0.5 * c.metrics["pata_A"] + 0.5 * c.metrics["pata_B"])) < 1e-9


def test_committee_never_exceeds_core_target_and_only_risk_can_veto():
    ctx, tr = make_ctx()
    s = sesion(ctx)
    assert s["objetivo_final"] == pytest.approx(s["objetivo_nucleo"]) and not s["veto"] and "Mantener" in s["decision"]
    ctx2, tr2 = make_ctx(kill=True)
    s2 = sesion(ctx2); assert s2["veto"] and s2["objetivo_final"] == 0.0 and s2["estado"] == ALERTA
    md = markdown(s); assert "Organigrama" in md and all(n in md for n, _, _ in ROSTER)


def test_committee_survives_a_failing_department(monkeypatch):
    from src.desk import committee
    ctx, tr = make_ctx()
    def boom(c): raise RuntimeError("fallo simulado")
    monkeypatch.setattr(committee, "DEPTS", [("Departamento roto", boom)] + committee.DEPTS[:3])
    s = sesion(ctx)
    assert len(s["departamentos"]) == 4 and s["departamentos"][0]["headline"] == "FALLO DEL DEPARTAMENTO"
    assert s["estado"] == ALERTA and "Departamento roto" in s["alertas"]


def test_fomc_parser_ignores_minutes_dates_and_handles_month_crossing():
    html = ("<h4>2026 FOMC Meetings</h4> January 27-28 Statement: PDF | HTML Minutes: PDF | HTML (Released February 18, 2026) "
            "Oct/Nov 31-1 Statement: PDF March 17-18* Statement: PDF <h4>2025 FOMC Meetings</h4>")
    ev = parse_fomc(html)
    days = ev["time"].dt.strftime("%m-%d").tolist()
    assert "01-28" in days and "03-18" in days and "11-01" in days and "02-18" not in days            # nada de fechas de minutas
    assert (ev["time"].dt.hour.isin([18, 19])).all()                                                   # 14:00 ET en UTC (con/sin horario de verano)


def test_lab_shadows_start_flat_and_promotion_needs_90_days():
    ctx, tr = make_ctx()
    eq = run_from(ctx.bars, np.zeros(len(ctx.bars)), CoreParams(), ctx.lab_start)
    assert eq.iloc[0] == pytest.approx(1.0) and len(eq) > 500
    ctx.lab_start = ctx.bars.index[-300] + H4                                    # ~50 días de prueba
    r = laboratorio(ctx); v = r.metrics["variantes"]
    assert len(v) == len(SHADOWS) and 40 < v["nucleo (referencia)"]["dias"] < 60
    assert "sin evidencia" in " ".join(r.notes) and "CANDIDATA" not in " ".join(r.notes)      # < 90 días: nada se promociona
    ctx.lab_start = ctx.bars.index[-900] + H4                                    # ~150 días: se evalúa la regla de promoción
    r2 = laboratorio(ctx); assert "sin evidencia" not in " ".join(r2.notes)


def test_school_tags_use_only_information_available_at_entry():
    ctx, tr = make_ctx()
    when = ctx.bars.index[3500] + H4
    t1 = _tags_at(ctx.bars, when, ctx.macro)
    future = ctx.bars.copy(); future.iloc[3501:, future.columns.get_indexer(["open", "high", "low", "close"])] *= 3     # alterar el futuro
    assert _tags_at(future, when, ctx.macro) == t1 and {"tendencia", "volatilidad"} <= set(t1)


def test_narrator_is_optional_and_never_needed():
    from src.desk.committee import narrate
    ctx, tr = make_ctx(); s = sesion(ctx)
    import os; os.environ.pop("ANTHROPIC_API_KEY", None)
    assert narrate(s) is None                                              # sin clave: cae al informe determinista
