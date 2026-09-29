"""Evaluación matemática de la prueba en papel (protocolo: config/prueba_papel_prerregistrada.md).

Contiene:
  * bandas y cono del backtest (generados solo con datos < 2025-07-01, ver make_bands);
  * réplica: el trader (con lote fino) frente al simulador validado e INDEPENDIENTE (_simulate);
  * réplica de estado: la cuenta real de papel frente a un replay con la misma configuración;
  * probabilidad posterior bayesiana del Sharpe verdadero;
  * las puertas G1-G5 y el informe en texto llano.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats as st
from ..backtest.funding import align_funding
from ..core.nucleo import CoreParams, compute_targets, _simulate
from .config import LiveConfig, RiskLimits
from .journal import build_journal
from .pipeline import replay
from .store import Store
from .trader import PaperTrader, INTERVAL

ROOT = Path(__file__).resolve().parents[2]
BANDS = ROOT / "config" / "backtest_bands.json"
H4 = INTERVAL


# ------------------------------------------------------------------ bandas del backtest
def make_bands(daily_returns: np.ndarray, expo: pd.Series, turn: pd.Series, eq: pd.Series, out: Path = BANDS,
               horizons=(7, 14, 30, 60, 90, 180, 365), sims=20000, seed=1) -> dict:
    rng = np.random.default_rng(seed); n = len(daily_returns); cone = {}
    for L in horizons:
        ret = np.empty(sims); dd = np.empty(sims)
        for s in range(sims):
            idx = np.empty(L, np.int64); idx[0] = rng.integers(n)
            for t in range(1, L):
                idx[t] = rng.integers(n) if rng.random() < 1 / 30 else (idx[t - 1] + 1) % n
            x = np.cumprod(1 + daily_returns[idx]); ret[s] = x[-1] - 1
            dd[s] = (1 - x / np.maximum.accumulate(np.r_[1, x])[1:]).max()
        cone[str(L)] = {"ret": {p: float(np.percentile(ret, p)) for p in (1, 5, 25, 50, 75, 95, 99)},
                        "dd": {p: float(np.percentile(dd, p)) for p in (50, 95, 99)}, "p_perdida": float((ret < 0).mean())}
    W = 180
    bands = {"nota": "Solo datos < 2025-07-01 (núcleo v1)", "cono": cone,
             "exposicion_30d": {p: float(np.percentile(expo.rolling(W).mean().dropna(), p)) for p in (1, 5, 50, 95, 99)},
             "ordenes_30d": {p: float(np.percentile((turn > 0).astype(int).rolling(W).sum().dropna(), p)) for p in (1, 5, 50, 95, 99)},
             "sharpe_backtest": float(daily_returns.mean() / daily_returns.std(ddof=1) * np.sqrt(365))}
    Path(out).write_text(json.dumps(bands, indent=1))
    return bands


def load_bands() -> dict:
    return json.loads(BANDS.read_text())


def cone_for(days: int, bands: dict) -> dict:
    ks = sorted(int(k) for k in bands["cono"]); k = min(ks, key=lambda x: abs(x - days))
    return {"horizonte_usado_dias": k, **bands["cono"][str(k)]}


# ------------------------------------------------------------------ probabilidad posterior del Sharpe
def posterior_sharpe(daily_returns: np.ndarray, prior_mean=0.4, prior_sd=0.5) -> dict:
    """Actualización normal-normal del Sharpe anual verdadero. La evidencia crece con 1/√años."""
    r = np.asarray(daily_returns, float); r = r[np.isfinite(r)]
    T = len(r)
    if T < 10:
        return {"dias": T, "estado": "insuficiente"}
    sr = float(r.mean() / r.std(ddof=1) * np.sqrt(365)); yrs = T / 365
    se = float(np.sqrt((1 + sr ** 2 / 2) / yrs))
    p_prec, o_prec = 1 / prior_sd ** 2, 1 / se ** 2
    mu = (prior_mean * p_prec + sr * o_prec) / (p_prec + o_prec); sd = float(np.sqrt(1 / (p_prec + o_prec)))
    return {"dias": T, "sharpe_observado": sr, "error_estandar": se, "posterior_media": float(mu), "posterior_sd": sd,
            "prob_sharpe_mayor_0": float(1 - st.norm.cdf(0, mu, sd)), "ic90": [float(mu - 1.645 * sd), float(mu + 1.645 * sd)],
            "prior": {"media": prior_mean, "sd": prior_sd}}


def dias_para_confirmar(sharpe_real: float, t_objetivo=2.0) -> float:
    return (t_objetivo / sharpe_real) ** 2 * 365 if sharpe_real > 0 else float("inf")


# ------------------------------------------------------------------ réplicas
def replicate_with_fine_lot(cfg: LiveConfig, bars: pd.DataFrame, funding_events: pd.DataFrame, start_bar: pd.Timestamp) -> dict:
    """Decisiones del trader (lote fino, sin mínimos) frente al simulador validado _simulate (código independiente)."""
    fine = LiveConfig(capital=cfg.capital, data_dir=cfg.data_dir, lot_step=1e-9, min_qty=1e-9, min_notional=0.0,
                      min_history_bars=cfg.min_history_bars, risk=RiskLimits(dd_halt=9.0, daily_loss_halt=9.0), core=cfg.core)
    tr = replay(fine, bars, funding_events, str(start_bar), str(bars.index[-1]))
    eq_live = tr.st.rows("equity")[-1]["equity"]
    ct = compute_targets(bars, cfg.core); sig, tgt = ct["sig"], ct["tgt"]
    n = len(bars); i0 = int(bars.index.get_loc(start_bar))
    r = bars["close"].pct_change().fillna(0).to_numpy()
    target = np.zeros(n); changed = np.zeros(n, bool)
    target[i0 + 1:] = tgt[i0:-1]; changed[i0 + 1:] = (sig[i0:-1] != sig[i0 - 1:-2])
    f = align_funding(bars.index, H4, funding_events) if len(funding_events) else np.zeros(n)
    eq, expo, turn, fc = _simulate(r[i0 + 1:], target[i0 + 1:], changed[i0 + 1:], f[i0 + 1:], cfg.core.cost, cfg.core.band)
    ref = cfg.capital * eq[-1]
    return {"equity_trader": eq_live, "equity_simulador": ref, "diferencia_rel": eq_live / ref - 1,
            "ordenes_trader": len(tr.st.rows("trades")), "ordenes_simulador": int((turn > 0).sum())}


def replicate_state(cfg: LiveConfig, bars: pd.DataFrame, funding_events: pd.DataFrame, start_bar: pd.Timestamp, live_store: Store) -> dict:
    """La cuenta REAL de papel (con sus reglas de lote/mínimo y con reinicios) frente a un replay limpio con la misma
    configuración: detecta velas perdidas, estado corrupto o dobles procesados."""
    tr = replay(cfg, bars, funding_events, str(start_bar), str(bars.index[-1]))
    a, b = tr.st.rows("equity"), live_store.rows("equity")
    ea, eb = a[-1]["equity"], b[-1]["equity"]
    return {"equity_replay": ea, "equity_cuenta": eb, "diferencia_rel": eb / ea - 1, "ordenes_replay": len(tr.st.rows("trades")),
            "ordenes_cuenta": len(live_store.rows("trades")), "velas_replay": len(a), "velas_cuenta": len(b)}


# ------------------------------------------------------------------ informe y puertas
def forward_report(cfg: LiveConfig, live_store: Store, bars: pd.DataFrame, funding_events: pd.DataFrame,
                   start_bar: pd.Timestamp, bands: dict | None = None) -> dict:
    bands = json.loads(json.dumps(bands)) if bands else load_bands()      # claves de texto (igual que en el JSON)
    eq = pd.DataFrame(live_store.rows("equity"))
    if eq.empty:
        return {"estado": "sin datos"}
    j = build_journal(live_store, cfg.capital)
    days = max(1, int((pd.Timestamp(eq["bar"].iloc[-1]) - pd.Timestamp(eq["bar"].iloc[0])).total_seconds() / 86400))
    eqs = pd.Series(eq["equity"].to_numpy(), index=pd.to_datetime(eq["bar"]))
    ret = float(eqs.iloc[-1] / cfg.capital - 1); dd = float((1 - eqs / eqs.cummax()).max())
    daily = eqs.resample("1D").last().pct_change().dropna().to_numpy()
    cone = cone_for(days, bands)
    bars_needed = int((bars.index[-1] - start_bar) / H4) + 1
    r1 = replicate_with_fine_lot(cfg, bars, funding_events, start_bar)
    r2 = replicate_state(cfg, bars, funding_events, start_bar, live_store)
    expo_mean = float(eq["expo"].mean()); n_orders = len(live_store.rows("trades"))
    e5, e95 = bands["exposicion_30d"]["5"], bands["exposicion_30d"]["95"]
    o5, o95 = bands["ordenes_30d"]["5"], bands["ordenes_30d"]["95"]
    scale = min(days, 30) / 30                                       # las bandas son de 30 días
    gates = {
        "G1_replica": abs(r1["diferencia_rel"]) <= 0.005 and abs(r1["ordenes_trader"] - r1["ordenes_simulador"]) <= 1 and abs(r2["diferencia_rel"]) < 1e-9,
        "G2_integridad": len(eq) >= bars_needed - 1 and not live_store.get("halted"),
        "G3_envolvente": (e5 * 0.5 <= expo_mean <= e95 * 1.2) and (o5 * scale - 1 <= n_orders <= o95 * max(scale, 0.2) + 1) and dd <= cone["dd"]["99"] * 1.0 + 1e-9,
        "G4_no_anomalo": cone["ret"]["1"] <= ret <= cone["ret"]["99"],
        "G5_registro_cuadra": j["cuadre"]["ok"],
    }
    post = posterior_sharpe(daily)
    return {"dias": days, "velas": len(eq), "retorno": ret, "caida_max": dd, "exposicion_media": expo_mean, "ordenes": n_orders,
            "cono_30d": cone, "resumen_diario": j["resumen"], "cuadre": j["cuadre"], "replica_decisiones": r1, "replica_estado": r2,
            "posterior_sharpe": post, "puertas": gates, "todas_las_puertas": bool(all(gates.values())),
            "aviso": ("Con menos de 30 días las puertas G3/G4 son provisionales." if days < 30 else "")}


def informe_texto(rep: dict) -> str:
    if rep.get("estado") == "sin datos":
        return "Aún no hay velas procesadas."
    r = rep; p = r["posterior_sharpe"]; c = r["cono_30d"]; js = r["resumen_diario"]
    lc, pc = js["lotes_cerrados"], js["posiciones_cerradas"]
    L = [f"INFORME DE LA PRUEBA EN PAPEL · día {r['dias']} · {r['velas']} velas de 4h procesadas", "",
         f"Retorno: {r['retorno']:+.2%} | Caída máxima: {r['caida_max']:.2%} | Exposición media: {r['exposicion_media']:.2f}× | Órdenes: {r['ordenes']}",
         f"Rango esperado a ~{c['horizonte_usado_dias']} días si el sistema se comporta como en el backtest: p5 {c['ret']['5']:+.1%} · mediana {c['ret']['50']:+.1%} · p95 {c['ret']['95']:+.1%} "
         f"(probabilidad de terminar en pérdida aun siendo bueno: {c['p_perdida']:.0%}).", "",
         "REGISTRO DE ENTRADAS (lotes = cada compra):"]
    L.append(f"  Cerrados: {lc.get('n', 0)} → ganan {lc.get('ganan', 0)} / pierden {lc.get('pierden', 0)}" + (f" (acierto {lc['tasa_acierto']:.0%})" if lc.get("n") else ""))
    L.append(f"  Abiertos: {js['lotes_abiertos']} (P&L no realizado {js['pnl_no_realizado']:+.2f} USDT)")
    L.append(f"  Posiciones completas cerradas: {pc.get('n', 0)}" + (f" → ganan {pc['ganan']} / pierden {pc['pierden']}" if pc.get("n") else "") +
             "  (esperado histórico: ~27 % ganadoras, ganancia media ~9× la pérdida media)")
    L.append(f"  Cuadre del diario con la equity: {'OK' if r['cuadre']['ok'] else 'FALLA'} (dif. {r['cuadre']['diferencia']:+.4f} USDT)")
    L += ["", "PUERTAS del protocolo (paso a dinero real mínimo):"]
    names = {"G1_replica": "G1 Réplica del backtest (decisiones y estado)", "G2_integridad": "G2 Integridad (ninguna vela perdida)",
             "G3_envolvente": "G3 Comportamiento dentro de su envolvente histórica", "G4_no_anomalo": "G4 Retorno no anómalo",
             "G5_registro_cuadra": "G5 El registro cuadra con la equity"}
    for k, v in r["puertas"].items():
        L.append(f"  [{'OK' if v else 'NO'}] {names[k]}")
    rd, re_ = r["replica_decisiones"], r["replica_estado"]
    L.append(f"  Réplica de decisiones: dif. equity {rd['diferencia_rel']:+.3%} vs simulador validado; órdenes {rd['ordenes_trader']} vs {rd['ordenes_simulador']}")
    L.append(f"  Réplica de estado (cuenta vs replay limpio): dif. {re_['diferencia_rel']:+.2e}; velas {re_['velas_cuenta']} vs {re_['velas_replay']}")
    L += ["", "PROBABILIDAD DE QUE EL SISTEMA SEA RENTABLE (Sharpe verdadero > 0):"]
    if p.get("estado") == "insuficiente":
        L.append(f"  Con {p['dias']} días aún no se puede calcular (mínimo 10).")
    else:
        L.append(f"  {p['prob_sharpe_mayor_0']:.0%} (intervalo 90 % del Sharpe verdadero: {p['ic90'][0]:.2f} a {p['ic90'][1]:.2f}; prior conservador {p['prior']['media']} ± {p['prior']['sd']}).")
        L.append(f"  Sharpe observado en {p['dias']} días: {p['sharpe_observado']:.2f} (error estándar ±{p['error_estandar']:.1f}: muy poco informativo a este plazo).")
    L.append("  Referencia: con Sharpe 1,1, confirmar t = 2 exige ≈ %.1f años de datos nuevos." % (dias_para_confirmar(1.1) / 365))
    L += ["", "VEREDICTO: " + ("todas las puertas técnicas se cumplen; el paso a dinero real mínimo depende de tu aprobación expresa." if r["todas_las_puertas"]
                             else "alguna puerta no se cumple todavía; NO pasar a dinero real hasta diagnosticarla.") + (f"  ({r['aviso']})" if r["aviso"] else "")]
    return "\n".join(L)
