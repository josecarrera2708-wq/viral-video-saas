"""Ejecutor: convierte una posición OBJETIVO en órdenes idempotentes con stop y take-profit protectores, siempre a través del guardián."""
from __future__ import annotations
import json
import math
from pathlib import Path
import pandas as pd
from .base import Exchange, OrderRequest, ExchangeError, BUY, SELL, MARKET, LIMIT, STOP
from .guard import RiskGuard


class Executor:
    def __init__(self, ex: Exchange, guard: RiskGuard, symbol="BTCUSDT", lot=0.001, min_notional=100.0, state_path: Path | None = None):
        self.ex, self.guard, self.symbol, self.lot, self.min_notional = ex, guard, symbol, lot, min_notional
        self.state_path = Path(state_path) if state_path else None
        self.sent: set[str] = set(json.loads(self.state_path.read_text())) if self.state_path and self.state_path.exists() else set()
        self.log: list[dict] = []

    def _remember(self, tag: str):
        self.sent.add(tag)
        if self.state_path:
            self.state_path.write_text(json.dumps(sorted(self.sent)))

    def _send(self, req: OrderRequest, mark: float) -> dict:
        d = self.guard.check(req, mark)
        if not d.ok:
            rec = {"client_id": req.client_id, "estado": "rechazada", "motivo": d.reason}
        else:
            try:
                fills = self.ex.place(req); rec = {"client_id": req.client_id, "estado": "enviada", "fills": len(fills)}
            except ExchangeError as e:
                rec = {"client_id": req.client_id, "estado": "error", "motivo": str(e)}
        self.log.append(rec)
        return rec

    def _round(self, q: float) -> float:
        return math.floor(abs(q) / self.lot + 1e-9) * self.lot

    def set_target(self, tag: str, ts: pd.Timestamp, target_qty: float, stop: float | None = None, tp: float | None = None) -> dict:
        """target_qty con signo (BTC). Idempotente por (tag, ts). Con posición abierta exige stop."""
        key = f"{tag}-{pd.Timestamp(ts):%Y%m%d%H%M}"
        if key in self.sent:
            return {"estado": "ya_enviada", "key": key}
        mark = self.ex.last_price(self.symbol); cur = self.ex.position(self.symbol).qty
        if target_qty != 0 and stop is None:
            return {"estado": "rechazada", "motivo": "una posición abierta exige stop"}
        for o in self.ex.open_orders(self.symbol):                        # las protecciones anteriores ya no valen
            if o.reduce_only:
                self.ex.cancel(o.client_id)
        steps: list[dict] = []; n = 0
        if cur != 0 and (target_qty == 0 or cur * target_qty < 0):          # cerrar (o invertir: primero se cierra)
            n += 1
            steps.append(self._send(OrderRequest(f"{key}-{n}", self.symbol, SELL if cur > 0 else BUY, self._round(cur), MARKET, reduce_only=True), mark))
            cur = self.ex.position(self.symbol).qty
        delta = target_qty - cur
        q = self._round(delta)
        if q > 0 and (q * mark >= self.min_notional):
            n += 1
            steps.append(self._send(OrderRequest(f"{key}-{n}", self.symbol, BUY if delta > 0 else SELL, q, MARKET), mark))
        pos = self.ex.position(self.symbol).qty
        if pos != 0:
            side = SELL if pos > 0 else BUY
            n += 1; steps.append(self._send(OrderRequest(f"{key}-{n}", self.symbol, side, abs(pos), STOP, stop, True), mark))
            if tp:
                n += 1; steps.append(self._send(OrderRequest(f"{key}-{n}", self.symbol, side, abs(pos), LIMIT, tp, True), mark))
        self._remember(key)
        return {"estado": "ok", "key": key, "pasos": steps, "posicion": pos}
