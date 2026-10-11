"""Detalle de cada operación intradía y análisis post-mortem determinista («aprender de por qué salió mal»).

Todo se calcula con datos reales de la operación (velas entre entrada y salida y las 12 siguientes); no hay LLM ni cifras inventadas.
Una sola operación no demuestra nada: las lecciones son HIPÓTESIS que solo pasan al ciclo de mejora (con prerregistro) cuando
se repiten en ≥ 30 operaciones del mismo trader.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import ema, atr

AFTER = 12                       # velas posteriores a la salida que se miran para saber si el stop «barrió» un movimiento correcto
MIN_SAMPLE = 30                  # muestra mínima para convertir un patrón en candidata de mejora


def context(bars: pd.DataFrame) -> pd.DataFrame:
    """Contexto causal por vela: tendencia de fondo (EMA 800 h ≈ EMA200 de 4 h) y percentil de volatilidad."""
    c = bars["close"]
    return pd.DataFrame({"trend": np.sign(c - ema(c, 800)), "atr_pct": (atr(bars, 14) / c).rolling(500, min_periods=100).rank(pct=True)}, index=bars.index)


def detail(bars: pd.DataFrame, ctx: pd.DataFrame, name: str, spec, r: dict, i: int, tp_mult: float, max_bars: int) -> dict:
    """Ficha completa de la operación i del resultado del motor."""
    ei, xi = int(r["entry_idx"][i]), int(r["exit_idx"][i]); d = int(r["dir"][i]); px = float(r["entry_px"][i]); qty = float(r["qty"][i])
    sig = max(ei - 1, 0); sd = float(np.nan_to_num(spec.stop[sig])); risk = float(r["risk"][i]); reason = {0: "stop", 1: "tp", 2: "signal", 3: "time", 4: "liq", 5: "end"}[int(r["reason"][i])]
    sl = px - d * sd; tp = px + d * tp_mult * sd if tp_mult > 0 else None
    hi, lo = bars["high"].to_numpy(), bars["low"].to_numpy(); n = len(bars)
    seg_h, seg_l = hi[ei:xi + 1], lo[ei:xi + 1]
    mfe = ((seg_h.max() - px) if d > 0 else (px - seg_l.min())) / sd if sd > 0 else 0.0            # máxima excursión a favor, en R
    mae = ((px - seg_l.min()) if d > 0 else (seg_h.max() - px)) / sd if sd > 0 else 0.0            # máxima excursión en contra, en R
    post = None
    if reason == "stop" and xi + 1 < n and sd > 0:
        a, b = hi[xi + 1:xi + 1 + AFTER], lo[xi + 1:xi + 1 + AFTER]
        post = float(((a.max() - px) if d > 0 else (px - b.min())) / sd)                             # cuánto habría ido a favor tras el stop, en R
    t_sig = ctx.iloc[sig]
    out = {"trader": name, "abre": bars.index[ei], "cierra": bars.index[xi] if reason != "end" else pd.NaT, "lado": "LARGO" if d > 0 else "CORTO",
           "px_entrada": px, "sl": float(sl), "tp": None if tp is None else float(tp), "lote_btc": qty, "nocional_usdt": qty * px, "riesgo_usdt": risk,
           "stop_pct": sd / px if px else 0.0, "px_salida": float(r["exit_px"][i]), "salida": reason, "R": float(r["r"][i]), "pnl_usdt": float(r["pnl"][i]),
           "comision_usdt": float(r["fees"][i]), "funding_usdt": float(r["funding"][i]), "barras": int(xi - ei + 1), "max_barras": int(max_bars),
           "mfe_R": float(mfe), "mae_R": float(mae), "post_stop_R": post, "tendencia_a_favor": bool(t_sig["trend"] == d) if pd.notna(t_sig["trend"]) and t_sig["trend"] != 0 else None,
           "vol_percentil": None if pd.isna(t_sig["atr_pct"]) else float(t_sig["atr_pct"]), "hora_utc": int(bars.index[ei].hour), "abierta": reason == "end"}
    out["lecciones"] = lessons(out, tp_mult)
    return out


def lessons(t: dict, tp_mult: float) -> list[str]:
    """Reglas simples y explícitas sobre por qué salió como salió. Vacío si la operación va bien o sigue abierta."""
    if t["abierta"]:
        return []
    L: list[str] = []; R = t["R"]
    if R > 0:
        if t["salida"] == "tp": L.append(f"Ganó: llegó al objetivo (+{R:.2f} R).")
        elif t["salida"] in ("time", "signal"): L.append(f"Ganó {R:+.2f} R saliendo por {'tiempo' if t['salida'] == 'time' else 'señal contraria'}; el máximo a favor fue {t['mfe_R']:.1f} R" + (" (dejó ganancia sobre la mesa)." if t["mfe_R"] > R + 0.7 else "."))
        return L
    if t["mfe_R"] < 0.3 and t["salida"] == "stop":
        L.append(f"Nunca fue a favor (máximo {t['mfe_R']:.2f} R): la señal falló desde el principio.")
    if t["mfe_R"] >= 1.0:
        L.append(f"Llegó a +{t['mfe_R']:.1f} R y lo devolvió todo: sin salida parcial ni stop de protección.")
    if t["post_stop_R"] is not None and tp_mult > 0 and t["post_stop_R"] >= tp_mult:
        L.append(f"Stop barrido: tras salir, el precio habría llegado a +{t['post_stop_R']:.1f} R en {AFTER} h. La dirección era correcta; el stop quedó corto.")
    elif t["post_stop_R"] is not None and t["post_stop_R"] < 0.5 and t["salida"] == "stop":
        L.append("El precio no se recuperó tras el stop: la salida fue la correcta.")
    if t["tendencia_a_favor"] is False:
        L.append("Operó contra la tendencia de fondo (EMA de 800 h).")
    if t["vol_percentil"] is not None and t["vol_percentil"] < 0.2:
        L.append(f"Volatilidad baja (percentil {t['vol_percentil']:.0%}): el stop era estrecho y los costes pesaron más.")
    cost_r = (t["comision_usdt"] - t["funding_usdt"]) / t["riesgo_usdt"] if t["riesgo_usdt"] else 0.0
    if cost_r > 0.15:
        L.append(f"Comisiones y funding costaron {cost_r:.2f} R de esta pérdida.")
    if t["salida"] == "time" and R <= 0:
        L.append(f"Se agotó el tiempo ({t['barras']} h) sin alcanzar el objetivo ni el stop: la idea no se desarrolló.")
    if not L:
        L.append("Pérdida dentro de lo normal del sistema: el stop se activó sin un patrón claro.")
    return L


def learning(details: list[dict]) -> dict:
    """Patrones agregados por trader. Solo son candidatas de mejora con ≥ MIN_SAMPLE operaciones."""
    out: dict = {}
    for name in sorted({d["trader"] for d in details}):
        cl = [d for d in details if d["trader"] == name and not d["abierta"]]; loss = [d for d in cl if d["R"] <= 0]
        pat = {"nunca_a_favor": sum(d["mfe_R"] < 0.3 and d["salida"] == "stop" for d in loss), "stop_barrido": sum(bool(d["post_stop_R"] is not None and d["post_stop_R"] >= 1.5) for d in loss),
               "contra_tendencia": sum(d["tendencia_a_favor"] is False for d in loss), "vol_baja": sum(bool(d["vol_percentil"] is not None and d["vol_percentil"] < 0.2) for d in loss)}
        out[name] = {"cerradas": len(cl), "perdedoras": len(loss), "patrones": pat,
                     "estado": "muestra insuficiente para concluir" if len(cl) < MIN_SAMPLE else "muestra suficiente: patrón elegible como candidata de mejora con prerregistro"}
    return out
