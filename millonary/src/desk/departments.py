"""Departamentos del Trading Floor de Millonary con lógica REAL (datos y cálculos verificables).

Cada función recibe un Context y devuelve un Report. Ninguna cambia el objetivo de exposición del núcleo:
solo Riesgos puede vetar (mediante la capa de riesgo determinista ya validada).
"""
from __future__ import annotations
import shutil
import numpy as np
import pandas as pd
from ..core.nucleo import compute_targets, signal_b
from ..signals import indicators as I, candles as C
from .base import Context, Report, OK, AVISO, ALERTA
from .events import next_event


def _acct(ctx: Context):
    st = ctx.store
    rows = st.rows("equity") if st else []
    if not rows:
        return None
    r = rows[-1]
    return {"equity": r["equity"], "units": r["units"], "price": r["price"], "expo": r["expo"], "peak": st.get("peak"),
            "day0": st.get("day_start_equity"), "halted": bool(st.get("halted")), "last_bar": st.get("last_bar")}


def _last(series: pd.Series | None):
    if series is None or len(series) == 0:
        return None
    s = series.dropna()
    return None if s.empty else (s.index[-1], float(s.iloc[-1]))


# ------------------------------------------------------------------------------------------------ RIESGOS
def riesgos(ctx: Context) -> Report:
    lim = ctx.cfg.risk; a = _acct(ctx)
    if not a:
        return Report("Riesgos", "Sin cuenta todavía", OK, notes=["No hay operaciones ni equity registradas."])
    dd = 1 - a["equity"] / a["peak"] if a["peak"] else 0.0
    dl = max(0.0, 1 - a["equity"] / a["day0"]) if a["day0"] else 0.0
    kill = (ctx.cfg.data_dir / "KILL").exists()
    expo = a["expo"]
    stress = {f"gap {int(s * 100)}%": round(expo * s, 4) for s in (-0.10, -0.20, -0.35, -0.50)}
    liq = (1 / expo - 0.005) if expo > 1e-9 else None
    status = OK; notes = []
    if a["halted"] or kill:
        status = ALERTA; notes.append("SISTEMA PARADO" + (" (KILL activo)" if kill else "") + ": la posición está aplanada hasta el reinicio manual.")
    if dd >= lim.dd_warn or dl >= lim.daily_loss_warn:
        status = max(status, AVISO, key=[OK, AVISO, ALERTA].index); notes.append(f"Caída {dd:.1%} desde máximos; pérdida del día {dl:.1%}.")
    notes.append(f"Distancia a los frenos: caída {dd:.1%} de {lim.dd_halt:.0%}; pérdida diaria {dl:.1%} de {lim.daily_loss_halt:.0%}.")
    notes.append(f"Exposición {expo:.2f}× (tope efectivo {lim.max_expo:.1f}×; el 5× del exchange no se usa).")
    if liq is not None:
        notes.append(f"Liquidación (margen cruzado): el precio tendría que moverse ≈ {liq:.0%} en contra; con esta exposición un gap de -50% costaría {stress['gap -50%']:.0%} del capital.")
    return Report("Riesgos", f"{'PARADO' if (a['halted'] or kill) else 'Operativa permitida'} · exposición {expo:.2f}× · caída {dd:.1%}", status,
                  {"caida_desde_maximo": dd, "perdida_dia": dl, "exposicion": expo, "estres_capital": stress, "distancia_liquidacion": liq},
                  notes, veto=bool(a["halted"] or kill))


# ------------------------------------------------------------------------------------------------ MACROECONOMÍA
def macro(ctx: Context) -> Report:
    m = ctx.macro or {}; flags, notes, met = [], [], {}
    fng = _last(m.get("fng"))
    if fng:
        met["fng"] = fng[1]
        zone = "miedo extremo" if fng[1] <= 20 else "miedo" if fng[1] <= 40 else "neutral" if fng[1] < 60 else "codicia" if fng[1] < 80 else "codicia extrema"
        notes.append(f"Fear & Greed {fng[1]:.0f} ({zone}).")
        if fng[1] <= 20 or fng[1] >= 80: flags.append("sentimiento extremo")
    vix = m.get("vix")
    if vix is not None and len(vix.dropna()) > 250:
        v = vix.dropna(); pct = float((v.iloc[-250:] <= v.iloc[-1]).mean()); met["vix"] = float(v.iloc[-1]); met["vix_percentil_1a"] = pct
        notes.append(f"VIX {v.iloc[-1]:.1f} (percentil {pct:.0%} del último año).")
        if pct >= 0.9: flags.append("estrés de volatilidad (VIX)")
    y10, y2 = _last(m.get("y10")), _last(m.get("y2"))
    if y10 and y2:
        curve = y10[1] - y2[1]; met["curva_10y_2y"] = curve
        notes.append(f"Curva 10a-2a: {curve:+.2f} pp" + (" (invertida)" if curve < 0 else "") + f"; 10a {y10[1]:.2f}%.")
        if curve < 0: flags.append("curva invertida")
    usd = m.get("usd")
    if usd is not None and len(usd.dropna()) > 60:
        u = usd.dropna(); ch = float(u.iloc[-1] / u.iloc[-50] - 1); met["dolar_50d"] = ch
        notes.append(f"Dólar (índice amplio) {ch:+.1%} en 50 días.")
        if ch > 0.04: flags.append("dólar fuerte")
    fe = ctx.funding_events
    if fe is not None and len(fe) > 100:
        fr = fe["funding_rate"].to_numpy(); last30 = fr[-90:].mean() * 3 * 365
        w = fr[-1095:]; pct = float(((w < fr[-1]).mean() + (w <= fr[-1]).mean()) / 2)          # rango medio: los empates no inflan el percentil
        met["funding_anualizado_30d"] = float(last30); met["funding_percentil_1a"] = pct
        notes.append(f"Funding actual {fr[-1] * 100:.4f}% por 8h (percentil {pct:.0%} del último año); media 30d anualizada {last30:.1%}.")
        if pct >= 0.95 and fr[-1] >= 0.0003: flags.append("apalancamiento largo extremo (funding)")      # y al menos 3× el nivel base de 0,01 %
    ev = ctx.events; status = OK; shadow = []
    if ev is not None and len(ev):
        ne = next_event(ev, ctx.now)
        if ne is not None:
            hrs = (ne["time"] - ctx.now).total_seconds() / 3600; met["horas_al_proximo_evento"] = hrs
            notes.append(f"Próximo evento: {ne['type']} ({ne.get('impact', '')}) {ne['time']:%Y-%m-%d %H:%M} UTC, en {hrs:.0f} h.")
            if hrs <= 12:
                status = AVISO; notes.append("Evento de impacto alto inminente: en 2021-2025 la vela del anuncio se movió ≈ 3,3× lo normal.")
    notes.append("Regla histórica probada: recortar la exposición alrededor del FOMC EMPEORÓ el núcleo (Sharpe 0,78 → 0,74; rechazada). Solo se informa, no se actúa.")
    label = "RIESGO ALTO" if len(flags) >= 3 else "PRECAUCIÓN" if flags else "NORMAL"
    if label != "NORMAL" and status == OK: status = AVISO
    met["banderas"] = flags
    return Report("Macroeconomía", f"Entorno {label}" + (f" · banderas: {', '.join(flags)}" if flags else ""), status, met, notes, shadow)


# ------------------------------------------------------------------------------------------------ ANÁLISIS (mercados)
def analisis(ctx: Context) -> Report:
    b = ctx.bars; c = b["close"]; notes = []; met = {}
    d = c.resample("1D").last().dropna()
    hz = {}
    for L in (20, 60, 120, 250):
        if len(d) > L: hz[L] = float(d.iloc[-1] / d.iloc[-1 - L] - 1)
    met["retorno_por_horizonte"] = hz
    pos = [L for L, v in hz.items() if v > 0]
    notes.append("Momentum por horizonte: " + ", ".join(f"{L}d {v:+.1%}" for L, v in hz.items()) + f" → {len(pos)}/4 positivos.")
    st = signal_b(b)[-1]; met["donchian50"] = "largo" if st == 1 else "fuera"
    notes.append(f"Ruptura Donchian-50 (4h): {'LARGO' if st == 1 else 'FUERA'}.")
    if len(d) > 200:
        s50, s200 = d.rolling(50).mean().iloc[-1], d.rolling(200).mean().iloc[-1]
        met["precio_vs_sma200d"] = float(d.iloc[-1] / s200 - 1); met["sma50_vs_sma200"] = float(s50 / s200 - 1)
        notes.append(f"Precio {d.iloc[-1] / s200 - 1:+.1%} sobre la SMA200 diaria; SMA50 {'>' if s50 > s200 else '<'} SMA200.")
    atr = I.atr(b, 14); atrp = atr / c
    if len(atrp.dropna()) > 500:
        pct = float((atrp.iloc[-2190:] <= atrp.iloc[-1]).mean()); met["atr_pct"] = float(atrp.iloc[-1]); met["volatilidad_percentil_1a"] = pct
        notes.append(f"Volatilidad (ATR 4h) {atrp.iloc[-1]:.2%} del precio, percentil {pct:.0%} del último año.")
    sw = I.swings(b, 3)
    if sw["last_high"].notna().iloc[-1] and sw["last_low"].notna().iloc[-1]:
        hh, ll = float(sw["last_high"].iloc[-1]), float(sw["last_low"].iloc[-1]); a = float(atr.iloc[-1])
        met["soporte"] = ll; met["resistencia"] = hh
        notes.append(f"Estructura: último máximo confirmado {hh:,.0f} ({(hh - c.iloc[-1]) / a:+.1f} ATR), último mínimo {ll:,.0f} ({(ll - c.iloc[-1]) / a:+.1f} ATR).")
    cd = C.all_candles(b.iloc[-60:]).iloc[-3:]
    hits = [f"{col}{' alcista' if v > 0 else ' bajista'}" for _, row in cd.iterrows() for col, v in row.items() if v != 0 and col not in ("doji",)]
    if hits: notes.append("Patrones de velas recientes (informativo, sin ventaja probada): " + ", ".join(sorted(set(hits))) + ".")
    return Report("Análisis de mercados", f"Tendencia {'alcista' if len(pos) >= 3 else 'bajista' if len(pos) <= 1 else 'mixta'} ({len(pos)}/4 horizontes)", OK, met, notes)


# ------------------------------------------------------------------------------------------------ GESTIÓN DE CARTERA
def cartera(ctx: Context) -> Report:
    cfg = ctx.cfg; ct = compute_targets(ctx.bars.iloc[-cfg.history_bars:], cfg.core)
    A, B, sig, vol, scale, tgt = (float(ct[k][-1]) for k in ("A", "B", "sig", "vol", "scale", "tgt"))
    a = _acct(ctx); expo = a["expo"] if a else 0.0; band = cfg.core.band
    need = (tgt > 0 and abs(expo - tgt) > band * tgt) or (tgt == 0 and expo > 0)
    met = {"pata_A": A, "pata_B": B, "senal": sig, "volatilidad_anual_ewma": vol, "escala_vol": scale, "objetivo": tgt, "exposicion_actual": expo}
    notes = [f"Señal = 0,5·A({A:.2f}) + 0,5·B({B:.0f}) = {sig:.3f}.", f"Volatilidad anual (EWMA 45d) {vol:.0%} → escala mín(2; 25%/σ) = {scale:.2f}.",
             f"Exposición objetivo {tgt:.2f}× frente a {expo:.2f}× actual (banda ±{band:.0%}) → {'REBALANCEO pendiente' if need else 'sin cambios necesarios'}."]
    fe = ctx.funding_events
    if fe is not None and len(fe) > 30:
        drag = expo * fe["funding_rate"].iloc[-90:].mean() * 3 * 365; met["coste_funding_anual_estimado"] = float(drag)
        notes.append(f"Coste de funding estimado a esta exposición: {drag:+.2%} anual del capital.")
    lot_value = cfg.lot_step * float(ctx.bars["close"].iloc[-1])
    if a and lot_value > 0.05 * a["equity"]:
        notes.append(f"Cuenta pequeña: el lote mínimo ({lot_value:.0f} USDT) es el {lot_value / a['equity']:.0%} del capital; el objetivo se redondea a ese paso.")
    return Report("Gestión de cartera", f"Objetivo {tgt:.2f}× · actual {expo:.2f}×", AVISO if need else OK, met, notes)


# ------------------------------------------------------------------------------------------------ MESA DE TRADING
def mesa(ctx: Context) -> Report:
    j = ctx.journal
    if not j or j["orders"].empty:
        return Report("Mesa de trading", "Sin órdenes todavía", OK, notes=["La mesa ejecutará cuando el núcleo pida cambiar la exposición."])
    o = j["orders"]; lots = j["lots"]; rs = j["resumen"]
    notes = [f"{len(o)} órdenes ejecutadas (comisiones {o['fee'].sum():.2f} USDT). Modelo de costes: 5 pb comisión + 2 pb deslizamiento por lado."]
    last = o.tail(3)
    for _, r in last.iterrows(): notes.append(f"  {r['bar'][:16]} {r['side']} {abs(r['qty']):.4f} BTC @ {r['price']:,.1f} ({r['reason']})")
    lc = rs["lotes_cerrados"]
    if lc.get("n"): notes.append(f"Lotes cerrados: {lc['n']} → {lc['ganan']} ganan / {lc['pierden']} pierden; P&L realizado {lc['pnl_total']:+.2f} USDT.")
    notes.append(f"Lotes abiertos: {rs['lotes_abiertos']} (no realizado {rs['pnl_no_realizado']:+.2f} USDT). Cuadre del diario: {'OK' if j['cuadre']['ok'] else 'FALLA'}.")
    return Report("Mesa de trading", f"{len(o)} órdenes · {rs['lotes_abiertos']} lotes abiertos", OK if j["cuadre"]["ok"] else ALERTA,
                  {"ordenes": len(o), "comisiones": float(o["fee"].sum()), "cuadre_ok": j["cuadre"]["ok"]}, notes)


# ------------------------------------------------------------------------------------------------ DERIVADOS / ARBITRAJE (investigación)
def derivados(ctx: Context) -> Report:
    fe = ctx.funding_events
    if fe is None or len(fe) < 90:
        return Report("Derivados y arbitraje", "Sin datos de funding suficientes", OK)
    fr = fe["funding_rate"]; a30 = float(fr.iloc[-90:].mean() * 3 * 365); a365 = float(fr.iloc[-1095:].mean() * 3 * 365)
    notes = [f"Funding anualizado: 30d {a30:+.1%}, 1 año {a365:+.1%}.",
             f"Carry teórico 'cash-and-carry' (largo spot + corto perpetuo): ≈ {a30:.1%} anual bruto a 30d; el coste de montar y desmontar es ≈ 4 × 5 pb = 0,20 % y exige capital en spot y margen en el perpetuo.",
             "ESTADO: INVESTIGACIÓN. No se opera: requiere ejecución en dos mercados y gestión del riesgo de contraparte; se evaluará como pata aparte con su propio protocolo."]
    return Report("Derivados y arbitraje", f"Carry teórico {a30:+.1%} anual (investigación)", OK, {"funding_30d_anual": a30, "funding_1a_anual": a365}, notes)


# ------------------------------------------------------------------------------------------------ INFRAESTRUCTURA
def infra(ctx: Context) -> Report:
    notes, met, status = [], {}, OK
    last = ctx.bars.index[-1] + pd.Timedelta("4h")
    age_h = (ctx.now - last).total_seconds() / 3600; met["edad_ultima_vela_horas"] = age_h
    notes.append(f"Última vela cerrada a las {last:%Y-%m-%d %H:%M} UTC (hace {age_h:.1f} h) · fuente: {ctx.feed_source or 'n/d'}.")
    if age_h > 30: status = AVISO; notes.append("Datos con más de 30 h de retraso (normal solo con Binance Vision).")
    st = ctx.store
    if st:
        ok = st.db.execute("PRAGMA integrity_check").fetchone()[0]; met["integridad_bd"] = ok
        notes.append(f"Base de datos: {ok}.")
        if ok != "ok": status = ALERTA
        ev = pd.DataFrame(st.rows("events"))
        if not ev.empty:
            rec = ev[pd.to_datetime(ev["ts"], utc=True, errors="coerce") >= ctx.now - pd.Timedelta(days=7)]
            n_err = int((rec["level"].isin(["ERROR", "CRITICO"])).sum()); met["incidencias_7d"] = n_err
            notes.append(f"Incidencias en 7 días: {n_err}.")
            if n_err: status = max(status, AVISO, key=[OK, AVISO, ALERTA].index)
    free = shutil.disk_usage(str(ctx.cfg.data_dir if ctx.cfg.data_dir.exists() else ".")).free / 1e9; met["disco_libre_gb"] = free
    notes.append(f"Disco libre {free:.1f} GB.")
    if free < 1: status = ALERTA
    return Report("Infraestructura", f"{'Sano' if status == OK else 'Requiere atención'} · datos hace {age_h:.1f} h", status, met, notes)
