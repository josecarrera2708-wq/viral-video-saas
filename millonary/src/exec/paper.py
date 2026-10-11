"""Adaptador de PAPEL: simula mercado, límite y stop con comisiones, deslizamiento, margen y liquidación. Sin red, sin claves."""
from __future__ import annotations
import pandas as pd
from .base import Exchange, OrderRequest, Fill, Position, ExchangeError, BUY, SELL, MARKET, LIMIT, STOP


class PaperExchange(Exchange):
    name = "paper"
    mode = "paper"

    def __init__(self, capital=1000.0, taker=0.0005, maker=0.0002, slip=0.0002, mmr=0.005, tp_pen=0.0001, symbol="BTCUSDT"):
        self.cash = capital
        self.taker, self.maker, self.slip, self.mmr, self.tp_pen = taker, maker, slip, mmr, tp_pen
        self.symbol = symbol
        self.pos = Position(symbol)
        self.px: float | None = None
        self.ts: pd.Timestamp | None = None
        self._orders: dict[str, OrderRequest] = {}
        self._fills: list[Fill] = []
        self.events: list[str] = []

    # --- consultas
    def ping(self):
        return True

    def last_price(self, symbol):
        if self.px is None:
            raise ExchangeError("sin precio de mercado")
        return self.px

    def position(self, symbol):
        return Position(self.pos.symbol, self.pos.qty, self.pos.entry_px)

    def equity(self):
        unreal = self.pos.qty * (self.px - self.pos.entry_px) if (self.px is not None and self.pos.qty) else 0.0
        return self.cash + unreal

    def open_orders(self, symbol):
        return list(self._orders.values())

    def fills(self):
        return list(self._fills)

    # --- contabilidad de una ejecución
    def _apply(self, side, qty, px, fee, maker, cid, reason, ref=None):
        s = 1.0 if side == BUY else -1.0
        p = self.pos
        if p.qty * s < 0:                                        # reduce o invierte: realiza P&L de la parte cerrada
            closed = min(abs(p.qty), qty)
            direction = 1.0 if p.qty > 0 else -1.0
            self.cash += (px - p.entry_px) * direction * closed
        new = p.qty + s * qty
        if p.qty == 0 or p.qty * s > 0:                          # abre o aumenta: precio medio
            p.entry_px = (abs(p.qty) * p.entry_px + qty * px) / (abs(p.qty) + qty)
        elif new * p.qty < 0:                                    # invierte: el resto abre a este precio
            p.entry_px = px
        p.qty = new if abs(new) > 1e-12 else 0.0
        if p.qty == 0:
            p.entry_px = 0.0
        self.cash -= fee
        self._fills.append(Fill(cid, self.ts, self.symbol, side, qty, px, fee, maker, reason, ref))

    def place(self, req: OrderRequest):
        if self.px is None:
            raise ExchangeError("sin precio de mercado")
        if req.qty <= 0:
            raise ExchangeError("cantidad no positiva")
        if req.client_id in self._orders or any(f.client_id == req.client_id for f in self._fills):
            raise ExchangeError("client_id duplicado")
        qty = req.qty
        if req.reduce_only:
            cur = self.pos.qty
            if cur == 0 or (req.side == BUY) == (cur > 0):
                raise ExchangeError("reduce_only sin posición que reducir")
            qty = min(qty, abs(cur))
        if req.type == MARKET:
            px = self.px * (1 + self.slip) if req.side == BUY else self.px * (1 - self.slip)
            self._apply(req.side, qty, px, qty * px * self.taker, False, req.client_id, "fill", self.px)
            return [self._fills[-1]]
        if req.type in (LIMIT, STOP):
            if req.price is None:
                raise ExchangeError("falta precio")
            self._orders[req.client_id] = OrderRequest(req.client_id, req.symbol, req.side, qty, req.type, req.price, req.reduce_only)
            return []
        raise ExchangeError("tipo de orden no soportado")

    def cancel(self, client_id):
        return self._orders.pop(client_id, None) is not None

    # --- avance del mercado (una vela)
    def on_bar(self, ts, o, h, l, c):
        self.ts = pd.Timestamp(ts)
        self.px = o
        out: list[Fill] = []
        for cid, r in list(self._orders.items()):                # 1º stops (ganan los empates con los límites)
            if r.type != STOP:
                continue
            hit = (r.side == SELL and (o <= r.price or l <= r.price)) or (r.side == BUY and (o >= r.price or h >= r.price))
            if hit and self.pos.qty:
                base = min(o, r.price) if r.side == SELL else max(o, r.price)          # hueco de apertura: se llena a la apertura
                px = base * (1 - self.slip) if r.side == SELL else base * (1 + self.slip)
                q = min(r.qty, abs(self.pos.qty)) if r.reduce_only else r.qty
                self._apply(r.side, q, px, q * px * self.taker, False, cid, "stop")
                out.append(self._fills[-1])
                del self._orders[cid]
                self._drop_reduce_orders_if_flat()
        for cid, r in list(self._orders.items()):                # 2º límites (take-profit)
            if r.type != LIMIT:
                continue
            hit = (r.side == SELL and h > r.price * (1 + self.tp_pen)) or (r.side == BUY and l < r.price * (1 - self.tp_pen))
            if hit and (not r.reduce_only or self.pos.qty):
                q = min(r.qty, abs(self.pos.qty)) if r.reduce_only else r.qty
                self._apply(r.side, q, r.price, q * r.price * self.maker, True, cid, "tp" if r.reduce_only else "fill")
                out.append(self._fills[-1])
                del self._orders[cid]
                self._drop_reduce_orders_if_flat()
        self.px = c
        if self.pos.qty and self.equity() <= self.mmr * abs(self.pos.qty) * c:          # liquidación: se pierde el margen
            side = SELL if self.pos.qty > 0 else BUY
            self._fills.append(Fill("LIQ", self.ts, self.symbol, side, abs(self.pos.qty), c, 0.0, False, "liq"))
            out.append(self._fills[-1])
            self.cash = 0.0
            self.pos = Position(self.symbol)
            self._orders.clear()
            self.events.append("liquidacion")
        return out

    def _drop_reduce_orders_if_flat(self):
        if not self.pos.qty:
            for cid, r in list(self._orders.items()):
                if r.reduce_only:
                    del self._orders[cid]
