"""Adaptador de Margex: PENDIENTE. No hay documentación pública de su API (ver docs/EJECUCION.md).

Cuando el dueño aporte la documentación oficial (enlace o captura de su cuenta), este adaptador debe:
  * implementar `Exchange` (ping, equity, position, last_price, place, cancel, open_orders, fills);
  * arrancar en mode="demo" (cuenta AirUSD) y usar claves SIN permiso de retirada;
  * pasar `tests/test_exec_contract.py` con el mismo contrato que PaperExchange;
  * no exponer nunca las claves en logs ni en el repositorio (variables de entorno).
"""
from __future__ import annotations
from .base import Exchange


class MargexExchange(Exchange):
    name = "margex"
    mode = "demo"

    def __new__(cls, *a, **k):
        raise NotImplementedError("Margex no tiene API pública documentada: falta la documentación oficial del dueño (docs/EJECUCION.md).")
