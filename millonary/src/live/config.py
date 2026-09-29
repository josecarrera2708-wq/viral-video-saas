"""Configuración del ejecutor de Millonary. MODO PAPER: no se usan claves ni se envían órdenes reales."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from ..core.nucleo import CoreParams


@dataclass(frozen=True)
class RiskLimits:
    """Frenos de catástrofe FUERA de la envolvente histórica del núcleo (mayor caída 25 %; mayor pérdida
    intradía medida desde la marca de las 00:00 UTC: 5,8 %), para que no alteren el comportamiento
    validado. Los avisos no cambian nada."""
    max_expo: float = 2.0            # tope efectivo de exposición (x capital). El 5x del exchange NO se usa
    hard_expo: float = 5.0           # tope técnico absoluto
    daily_loss_warn: float = 0.03
    daily_loss_halt: float = 0.07    # pérdida en el día UTC >= 7 % -> aplanar y parar
    dd_warn: float = 0.20
    dd_halt: float = 0.30            # caída desde máximos >= 30 % -> aplanar y parar (reinicio manual)
    max_bar_jump: float = 0.25       # una vela con movimiento > 25 % se considera dato sospechoso
    stale_bars: int = 1              # se tolera como máximo 1 vela de retraso en los datos


@dataclass(frozen=True)
class LiveConfig:
    symbol: str = "BTCUSDT"
    interval: str = "4h"
    capital: float = 1000.0
    history_bars: int = 4000         # ~667 días: cubre el horizonte de 250 días y el calentamiento del EWMA
    min_history_bars: int = 1800     # por debajo la señal CAMBIA (la pata A necesita >251 días): no se opera
    lot_step: float = 0.001          # BTC
    min_qty: float = 0.001
    min_notional: float = 100.0      # VERIFICAR en el exchange real antes de operar con dinero
    reduce_below_min: bool = True    # SUPUESTO (verificar): las órdenes reduce-only no tienen nocional mínimo
    taker_fee: float = 0.0005
    slippage: float = 0.0002
    core: CoreParams = field(default_factory=CoreParams)
    risk: RiskLimits = field(default_factory=RiskLimits)
    mode: str = "paper"
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("MILLONARY_DATA", "./live_data")))
    close_delay_s: int = 45          # espera tras el cierre de la vela antes de pedir datos

    def __post_init__(self):
        if self.mode != "paper":
            raise ValueError("Solo el modo 'paper' está implementado. Operar con dinero real requiere "
                             "una decisión go/no-go explícita y un módulo de ejecución revisado.")
