# Millonary · Decisiones de diseño (2026-09-29)

Las decisiones marcadas **[YO]** las tomo yo con lo recopilado (el dueño me delegó esa autoridad);
las marcadas **[TÚ]** son del dueño.

| # | Decisión | Valor | Razón |
|---|---|---|---|
| 1 | Nombre / marca | **Millonary** | [TÚ] |
| 2 | Activo | Solo BTC | [TÚ] |
| 3 | Capital admitido | **100 a 10.000 USDT** | [TÚ] |
| 4 | Apalancamiento máximo | **5×** (tope duro) | [TÚ]. Objetivo efectivo ≤ 3×; 5× solo si la estrategia lo justifica en backtest |
| 5 | Stop-loss | **Según análisis**, nunca fijo: por estructura y/o ATR, lo elige el minero y lo valida el embudo | [TÚ]/[YO] |
| 6 | Instrumento | **Perpetuo USDT-M** (largos y cortos, funding modelado) | [YO]: es la serie sin huecos con funding; permite ir corto |
| 7 | Marcos temporales | Minar en **1h y 4h**; 1d como filtro de régimen | [YO]: Conesa muestra 1h; 15m se deja para refinar entradas más tarde |
| 8 | Serie de validación principal | Perpetuo desde 2020-01 (≈6,7 años, 0 huecos) | [YO] |
| 9 | Riesgo por operación | 0,5 % del capital (tramo alto); 1 % (tramo bajo) | [YO], ver nota de capital pequeño |
| 10 | Pérdida diaria máxima | 3 % → pausa hasta el día siguiente | [YO] |
| 11 | Drawdown desde máximos | 10 % → tamaño a la mitad; 15 % → parada total y revisión | [YO] |
| 12 | Criterios de aceptación | Los de la sección 6 de la ruta de trabajo | [YO] |
| 13 | Los agentes de IA no pueden saltarse la capa de riesgo | Regla fija | [YO] |

## Tramos de capital (importante)
Con BTC ≈ 83.500 USDT, el lote mínimo de 0,001 BTC vale ≈ 83,5 USDT de nocional. Consecuencias:

| Capital | Qué implica |
|---|---|
| **100–300 USDT** | No se puede dimensionar por riesgo con precisión: con un stop del 2 % el lote mínimo ya arriesga ≈ 1,7 USDT (≈ 1,7 % de 100). Regla: **se omite la operación si el riesgo del lote mínimo supera el 2 % del capital**. Funciona como "modo mínimo", con muchas menos operaciones posibles y más peso de las comisiones. |
| **300–1.000 USDT** | Dimensionado casi correcto. Riesgo objetivo 1 %. |
| **1.000–10.000 USDT** | Dimensionado normal. Riesgo objetivo 0,5 %. |

**Recomendación sincera:** empezar el paper trading con 1.000 USDT de referencia, y para dinero real
no bajar de ~300 USDT. Con 100 USDT las comisiones y el lote mínimo desvirtúan las estadísticas del
backtest.

## Nota sobre el apalancamiento 5×
A 5× una caída adversa de ~20 % liquida la posición (menos margen de mantenimiento). Como BTC hizo
velas de 1h de −18 % (mar-2020, oct-2025), el motor **modela la liquidación** y un stop siempre debe
estar mucho más cerca que ese nivel. El apalancamiento es un tope, no un objetivo.
