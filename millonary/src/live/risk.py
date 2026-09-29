"""Capa de riesgo DETERMINISTA por encima de la estrategia. Ningún agente de IA puede saltársela.

Filosofía: frenos de catástrofe situados FUERA de la envolvente histórica del núcleo, de modo que
no modifican el comportamiento validado en backtest (se comprueba con una prueba de reproducción).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import pandas as pd
from .config import RiskLimits


@dataclass
class RiskDecision:
    target: float                 # exposición objetivo tras aplicar los límites
    flatten: bool = False         # cerrar todo ahora
    halted: bool = False          # sistema parado (requiere reinicio manual)
    flags: list = field(default_factory=list)


def validate_bars(bars: pd.DataFrame, now: pd.Timestamp, lim: RiskLimits, interval: pd.Timedelta,
                  min_bars: int = 1800):
    """Devuelve (problemas, avisos). Los PROBLEMAS bloquean la operativa normal; los avisos no.
    Solo bloquea lo que cambia la señal: historia truncada, precios inválidos, huecos en las últimas
    12 velas o datos atrasados. Un hueco antiguo o un salto grande de precio (un desplome real) no bloquean."""
    problems, warns = [], []
    if len(bars) < min_bars:
        problems.append(f"historia insuficiente ({len(bars)} < {min_bars} velas): la señal cambiaría")
        return problems, warns
    idx = bars.index
    if not idx.is_monotonic_increasing or idx.has_duplicates:
        problems.append("índice no monótono o con duplicados")
    gaps = idx.to_series().diff().dropna()
    if (gaps.iloc[-12:] != interval).any():
        problems.append("huecos o irregularidades en las últimas 12 velas")
    elif (gaps != interval).any():
        warns.append(f"hay {int((gaps != interval).sum())} huecos antiguos en la historia (no afectan a la señal reciente)")
    px = bars[["open", "high", "low", "close"]]
    if (~np.isfinite(px.to_numpy())).any() or (px <= 0).any().any():
        problems.append("precios no finitos o <= 0")
    o, h, l, c = (bars[k].to_numpy() for k in ("open", "high", "low", "close"))
    if ((h < np.maximum(o, c) - 1e-9) | (l > np.minimum(o, c) + 1e-9)).any():
        problems.append("OHLC incoherente")
    last_expected = now.floor(interval) - interval                     # apertura de la última vela ya cerrada
    lag = (last_expected - idx[-1]) / interval
    if lag > lim.stale_bars:
        problems.append(f"datos atrasados: última vela {idx[-1]} (esperada {last_expected})")
    if lag < 0:
        problems.append("la última vela está aún abierta")
    jump = np.abs(bars["close"].pct_change().iloc[-3:]).max()
    if jump > lim.max_bar_jump:
        warns.append(f"SALTO_GRANDE de {jump:.1%} en las últimas velas (se sigue operando: puede ser un desplome real)")
    return problems, warns


class RiskLayer:
    def __init__(self, lim: RiskLimits, kill_file: Path):
        self.lim, self.kill_file = lim, Path(kill_file)

    def apply(self, target: float, equity: float, peak: float, day_start_equity: float,
              halted: bool) -> RiskDecision:
        lim = self.lim; flags = []
        if halted:
            return RiskDecision(0.0, flatten=True, halted=True, flags=["HALT_ACTIVO"])
        if self.kill_file.exists():
            return RiskDecision(0.0, flatten=True, halted=True, flags=["KILL_SWITCH"])
        dd = 1 - equity / peak if peak > 0 else 0.0
        day_loss = 1 - equity / day_start_equity if day_start_equity > 0 else 0.0
        if dd >= lim.dd_halt:
            return RiskDecision(0.0, flatten=True, halted=True, flags=[f"DD_HALT_{dd:.1%}"])
        if day_loss >= lim.daily_loss_halt:
            return RiskDecision(0.0, flatten=True, halted=True, flags=[f"PERDIDA_DIARIA_HALT_{day_loss:.1%}"])
        if dd >= lim.dd_warn: flags.append(f"AVISO_DD_{dd:.1%}")
        if day_loss >= lim.daily_loss_warn: flags.append(f"AVISO_PERDIDA_DIARIA_{day_loss:.1%}")
        t = float(np.clip(target, 0.0, min(lim.max_expo, lim.hard_expo)))
        if t != target: flags.append("EXPOSICION_RECORTADA")
        return RiskDecision(t, flags=flags)
