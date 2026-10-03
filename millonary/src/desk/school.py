"""Escuela / Academia: post-mortem de cada operación y marcador por contexto.

Aprende SOLO en el sentido medible: registra en qué contextos (tendencia, volatilidad, señal, sentimiento) gana o
pierde el sistema y avisa de las categorías débiles. No modifica parámetros (cualquier cambio = versión nueva).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals import indicators as I
from .base import Context, Report, OK, AVISO


def _tags_at(bars: pd.DataFrame, when: pd.Timestamp, macro: dict) -> dict:
    """Etiquetas de contexto en el momento de la entrada (usa solo datos hasta ese momento)."""
    b = bars[bars.index + pd.Timedelta("4h") <= when]
    if len(b) < 1300:
        return {}
    d = b["close"].resample("1D").last().dropna()
    tag = {"tendencia": "alcista" if d.iloc[-1] > d.rolling(200).mean().iloc[-1] else "bajista/lateral"}
    atrp = (I.atr(b, 14) / b["close"]).dropna()
    pct = float((atrp.iloc[-2190:] <= atrp.iloc[-1]).mean())
    tag["volatilidad"] = "baja" if pct < 1 / 3 else "media" if pct < 2 / 3 else "alta"
    fng = macro.get("fng") if macro else None
    if fng is not None and len(fng.dropna()):
        v = fng[fng.index <= when].dropna()
        if len(v): tag["sentimiento"] = "miedo" if v.iloc[-1] < 40 else "neutral" if v.iloc[-1] < 60 else "codicia"
    return tag


def escuela(ctx: Context) -> Report:
    j = ctx.journal
    if not j or j["lots"].empty:
        return Report("Escuela", "Sin operaciones que analizar todavía", OK,
                      notes=["La Escuela empieza a aprender cuando haya lotes cerrados: clasifica cada uno por contexto y mide dónde falla el sistema."])
    lots = j["lots"].copy(); closed = lots[lots["estado"] == "CERRADO"]
    notes = []; board = {}
    for _, l in closed.iterrows():
        tags = _tags_at(ctx.bars, pd.Timestamp(l["abre"]), ctx.macro)
        for k, v in tags.items():
            board.setdefault(f"{k}={v}", []).append(l["pnl_pct"])
    weak = []
    for k, v in sorted(board.items()):
        v = np.array(v); s = f"  {k}: n={len(v)}, aciertos {int((v > 0).sum())}/{len(v)}, esperanza {v.mean():+.2%}"
        if len(v) >= 5 and v.mean() < 0: weak.append(k); s += "  ← DÉBIL"
        notes.append(s)
    lessons = []
    for _, l in closed.tail(3).iterrows():
        capt = (l["pnl_pct"] / l["mfe_pct"]) if l["mfe_pct"] > 0 else None
        lessons.append(f"Lote {int(l['lote'])}: {l['resultado']} {l['pnl_pct']:+.1%} (máx. favorable {l['mfe_pct']:+.1%}, máx. adverso {l['mae_pct']:+.1%}" +
                       (f", capturó {capt:.0%} del recorrido" if capt is not None and l['pnl_pct'] > 0 else "") + ").")
    if not board:
        notes.append("Aún no hay lotes cerrados con contexto suficiente para clasificar.")
    hdr = "Marcador por contexto (lotes cerrados):" if board else "Sin lotes cerrados"
    if lessons: notes = lessons + ["", hdr] + notes
    else: notes = [hdr] + notes
    notes.append("Con muestras < 20 estas cifras son ANECDÓTICAS: se muestran para acumular evidencia, no para cambiar reglas.")
    return Report("Escuela", f"{len(closed)} lotes cerrados analizados · {len(weak)} categorías débiles", AVISO if weak else OK,
                  {"marcador": {k: {"n": len(v), "esperanza": float(np.mean(v))} for k, v in board.items()}, "debiles": weak}, notes)
