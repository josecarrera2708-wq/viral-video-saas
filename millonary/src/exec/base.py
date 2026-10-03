"""Capa de ejecución independiente del exchange. Cualquier adaptador (paper, demo, real) implementa `Exchange`.

Convención: qty siempre POSITIVA en las órdenes; la posición es con signo (+ largo, − corto). Precios en USDT, cantidades en BTC.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd

BUY, SELL = "buy", "sell"
MARKET, LIMIT, STOP = "market", "limit", "stop"          # STOP = stop de mercado (normalmente reduce_only)


@dataclass(frozen=True)
class OrderRequest:
    client_id: str
    symbol: str
    side: str
    qty: float
    type: str = MARKET
    price: float | None = None            # precio límite o de disparo (stop)
    reduce_only: bool = False


@dataclass
class Fill:
    client_id: str
    ts: pd.Timestamp
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    is_maker: bool
    reason: str = "fill"                  # fill | stop | tp | liq
    intended_price: float | None = None   # precio de referencia al enviar (para medir el deslizamiento)


@dataclass
class Position:
    symbol: str
    qty: float = 0.0
    entry_px: float = 0.0


class ExchangeError(Exception):
    pass


class Exchange(ABC):
    name = "abstract"
    mode = "paper"                        # paper | demo | live

    @abstractmethod
    def ping(self) -> bool: ...
    @abstractmethod
    def equity(self) -> float: ...
    @abstractmethod
    def position(self, symbol: str) -> Position: ...
    @abstractmethod
    def last_price(self, symbol: str) -> float: ...
    @abstractmethod
    def place(self, req: OrderRequest) -> list[Fill]: ...
    @abstractmethod
    def cancel(self, client_id: str) -> bool: ...
    @abstractmethod
    def open_orders(self, symbol: str) -> list[OrderRequest]: ...
    @abstractmethod
    def fills(self) -> list[Fill]: ...
