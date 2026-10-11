"""Guardián de riesgo previo a cada orden. Ninguna orden llega al exchange sin pasar por aquí.

Reglas (en este orden): modo real bloqueado sin aprobación expresa · símbolo permitido · parada (KILL o pérdida diaria) solo deja reducir ·
límite de órdenes por minuto · apalancamiento máximo tras la orden · tamaño máximo por orden.
La aprobación para dinero REAL vive en config/live_approval.json (la crea el dueño, nunca el sistema) y exige además MILLONARY_ALLOW_LIVE=1.
"""
from __future__ import annotations
import json, os
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd
from .base import Exchange, OrderRequest, BUY

ROOT = Path(__file__).resolve().parents[2]
APPROVAL = ROOT / "config" / "live_approval.json"


@dataclass
class GuardConfig:
    symbols: tuple = ("BTCUSDT",)
    max_leverage: float = 2.0             # nocional total / patrimonio tras la orden
    max_order_notional: float = 1000.0    # USDT por orden
    daily_loss_halt: float = 0.07         # parada si el patrimonio cae este % desde el inicio del día UTC
    max_orders_per_min: int = 20
    kill_file: Path = ROOT / "KILL"
    approval_file: Path = APPROVAL


@dataclass
class Decision:
    ok: bool
    reason: str = "ok"


def live_approved(cfg: GuardConfig, today: pd.Timestamp | None = None) -> tuple[bool, str, dict]:
    if os.environ.get("MILLONARY_ALLOW_LIVE") != "1":
        return False, "falta MILLONARY_ALLOW_LIVE=1", {}
    if not cfg.approval_file.exists():
        return False, "no existe config/live_approval.json (la aprobación la firma el dueño)", {}
    try:
        a = json.loads(cfg.approval_file.read_text())
        exp = pd.Timestamp(a["expires"], tz="UTC")
        ok = bool(a.get("approved_by")) and float(a["max_order_notional"]) > 0 and float(a["max_leverage"]) > 0
    except Exception as e:                                           # noqa: BLE001
        return False, f"aprobación ilegible: {type(e).__name__}", {}
    if not ok:
        return False, "aprobación incompleta", {}
    if (today or pd.Timestamp.now(tz="UTC")) > exp:
        return False, "aprobación caducada", {}
    return True, "ok", a


class RiskGuard:
    def __init__(self, ex: Exchange, cfg: GuardConfig | None = None, now=lambda: pd.Timestamp.now(tz="UTC")):
        self.ex, self.cfg, self.now = ex, cfg or GuardConfig(), now
        self.day = self.now().floor("1D"); self.day_start = ex.equity()
        self.halted = False; self.reason = ""
        self._recent: deque = deque()

    def _roll_day(self):
        d = self.now().floor("1D")
        if d != self.day:
            self.day, self.day_start = d, self.ex.equity()
            self.halted = False; self.reason = ""

    def check(self, req: OrderRequest, mark: float) -> Decision:
        self._roll_day(); c = self.cfg; eq = self.ex.equity()
        limits = {"max_leverage": c.max_leverage, "max_order_notional": c.max_order_notional}
        if self.ex.mode == "live":
            ok, why, appr = live_approved(c, self.now())
            if not ok and not req.reduce_only:
                return Decision(False, f"modo real bloqueado: {why}")
            if ok:
                limits = {"max_leverage": min(c.max_leverage, float(appr["max_leverage"])), "max_order_notional": min(c.max_order_notional, float(appr["max_order_notional"]))}
        if req.symbol not in c.symbols:
            return Decision(False, f"símbolo no permitido: {req.symbol}")
        if c.kill_file.exists():
            self.halted, self.reason = True, "KILL"
        elif self.day_start > 0 and eq <= self.day_start * (1 - c.daily_loss_halt):
            self.halted, self.reason = True, "pérdida diaria"
        if self.halted and not req.reduce_only:
            return Decision(False, f"parada activa ({self.reason}): solo se permite reducir")
        t = self.now()
        while self._recent and (t - self._recent[0]).total_seconds() > 60:
            self._recent.popleft()
        if len(self._recent) >= c.max_orders_per_min:
            return Decision(False, "demasiadas órdenes por minuto")
        if not req.reduce_only:
            cur = self.ex.position(req.symbol).qty; delta = req.qty if req.side == BUY else -req.qty
            post = abs(cur + delta) * mark
            if req.qty * mark > limits["max_order_notional"]:
                return Decision(False, f"orden de {req.qty * mark:,.0f} USDT supera el máximo {limits['max_order_notional']:,.0f}")
            if eq <= 0 or post > limits["max_leverage"] * eq:
                return Decision(False, f"apalancamiento tras la orden {post / max(eq, 1e-9):.2f}× supera {limits['max_leverage']:.2f}×")
        self._recent.append(t)
        return Decision(True)
