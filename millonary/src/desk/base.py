"""Base del 'Trading Floor' de Millonary: contexto compartido e informe de cada departamento.

Principios (no negociables):
  * Los departamentos ANALIZAN y RECOMIENDAN; solo la capa de riesgo determinista (Riesgos) puede vetar/aplanar.
  * Ningún departamento puede subir la exposición por encima del objetivo del núcleo validado.
  * Toda recomendación no validada queda en MODO SOMBRA: se registra y el Laboratorio mide después si habría mejorado.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd

OK, AVISO, ALERTA = "OK", "AVISO", "ALERTA"


@dataclass
class Context:
    now: pd.Timestamp
    bars: pd.DataFrame                          # velas 4h cerradas
    cfg: Any                                    # LiveConfig
    store: Any = None                           # Store de la cuenta de papel (o None)
    journal: dict | None = None                 # build_journal(...)
    funding_events: pd.DataFrame | None = None  # time, funding_rate
    macro: dict = field(default_factory=dict)   # series diarias: fng, vix, y10, y2, usd
    events: pd.DataFrame | None = None          # time, type, impact
    feed_source: str | None = None
    lab_start: pd.Timestamp | None = None       # inicio de la prueba (para sombras)


@dataclass
class Report:
    dept: str
    headline: str
    status: str = OK
    metrics: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    shadow: list = field(default_factory=list)   # recomendaciones NO aplicadas (modo sombra)
    veto: bool = False                           # solo Riesgos puede vetar

    def as_dict(self):
        return {"dept": self.dept, "headline": self.headline, "status": self.status, "metrics": self.metrics,
                "notes": self.notes, "shadow": self.shadow, "veto": self.veto}
