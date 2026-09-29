# Capa de ejecución de Millonary (`src/exec/`)

Objetivo: que pasar de papel a demo y a real sea cambiar un adaptador, no reescribir el sistema.

| Pieza | Fichero | Qué hace |
|---|---|---|
| Contrato | `base.py` | `Exchange`: ping, equity, position, last_price, place, cancel, open_orders, fills. Órdenes de mercado, límite y stop (reduce_only). |
| Papel | `paper.py` | Simula comisiones (taker 5 pb / maker 2 pb), deslizamiento 2 pb, stop con hueco de apertura, TP con penetración de 1 pb, margen y liquidación. |
| Guardián | `guard.py` | Toda orden pasa por aquí: símbolo permitido, KILL y pérdida diaria (solo se puede reducir), órdenes/minuto, apalancamiento máximo tras la orden, tamaño máximo por orden. |
| Ejecutor | `executor.py` | Posición objetivo → órdenes idempotentes (mismo tag y vela = no se repite) con stop y TP protectores; sin stop no abre. |
| Conciliación | `reconcile.py` | Deslizamiento real en pb frente al modelado (2 pb) y comparación con la simulación por `client_id`. |
| Margex | `margex.py` | **Pendiente**: no hay documentación pública de su API. Lanza `NotImplementedError` hasta que exista. |

## Dinero real: candados
1. `mode="live"` sin aprobación solo permite **reducir** posiciones.
2. La aprobación es `config/live_approval.json` (`approved_by`, `expires`, `max_order_notional`, `max_leverage`), que **crea el dueño**, nunca el sistema, y exige además la variable de entorno `MILLONARY_ALLOW_LIVE=1`.
3. Los límites del fichero solo pueden ser más estrictos que los del guardián.
4. Las claves de un exchange, si llegan a existir: solo permiso de trading (nunca de retirada), en variables de entorno, jamás en el repositorio.

## Cómo se incorpora un exchange nuevo
1. Escribir el adaptador (`src/exec/<nombre>.py`) en `mode="demo"` (cuenta de pruebas del exchange).
2. Añadirlo a `ADAPTERS` en `tests/test_exec_contract.py`: debe pasar el mismo contrato que `PaperExchange`.
3. Ejecutar la estrategia en demo y medir con `reconcile.slippage_report` si el deslizamiento real supera el modelado (2 pb). Si lo supera, los resultados del histórico se recalculan con ese coste antes de seguir.
4. Solo después, y con aprobación expresa del dueño, tamaño mínimo en real.

## Estado de Margex (2026-09-29)
Sin API documentada en su centro de ayuda ni en su web; reseñas de terceros no dan enlace. Se necesita del dueño: el apartado «API» de su cuenta o la respuesta del soporte (¿API REST/WebSocket?, ¿claves con permisos separados?, ¿funciona con la demo AirUSD?).
Comisiones publicadas por terceros: maker 0,019 %, taker 0,060 % (fijas). Apalancamiento hasta 100× (nuestros límites: 2× núcleo, 5× intradía).
