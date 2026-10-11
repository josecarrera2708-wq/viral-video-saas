# Fase 2 · primas de riesgo, lote 1 · Prerregistro v1 — antes de ejecutar nada sobre datos reales

Fecha 2026-10-03. Petición del dueño: añadir fuentes de retorno nuevas que usan los fondos («que gane por todos lados»). Sistema aparte
(`src/primas/`); núcleo, carry, mesas, fondos y cartera no se tocan. Código fijo en este commit: `src/primas/data.py`, `estrategias.py`, `evaluar.py`.
Parámetros elegidos a priori (redondos o de la práctica publicada, no mirando estos datos). Cambiar algo tras ejecutar = prueba nueva.

## Estrategias (4 pruebas nuevas: n.º 266–269)
| # | Estrategia | Fuente | Regla (decisión a las 00:00 UTC con velas de 1 h cerradas) |
|---|---|---|---|
| B01 | Basis trimestral hasta vencimiento | cash-and-carry clásico; Schmeling, Schrimpf y Todorov (BIS WP 1087, 2023) | Sin posición: trimestral USDT-M más cercano con ≥ 30 días al vencimiento; si (F/S − 1)·365/días > 5 % → largo contado + corto futuro (mismos BTC, nocional 1×). Se mantiene hasta el vencimiento (08:00 UTC; liquidación ≈ último cierre 1 h del futuro, contado vendido a la misma hora) y se vuelve a evaluar al día siguiente |
| B02 | Basis trimestral con salida anticipada | gestión activa del basis (práctica de mesas de arbitraje) | Igual que B01, pero si el basis anualizado restante cae por debajo del 1 % se cierran las dos patas antes del vencimiento |
| V01 | Prima de volatilidad | Carr y Wu (RFS 2009); Bakshi y Kapadia (2003); en cripto, Alexander e Imeraj (2021) | Venta de varianza a 30 d con strike = DVOL (Deribit) del día anterior; retorno diario = (0,5 %/3)·(1 − z²), z = r_d/(IV/√365): pierde 0,5 % del capital en un día de 2σ (riesgo 0,5 %, decisión #9) |
| V02 | Prima de volatilidad con filtro | «VRP condicional» | V01 solo los días en que IV > volatilidad realizada de los 30 días anteriores |

Costes: contado 10 + 2 pb y futuro 5 + 2 pb por lado (entrada y salida o liquidación); VRP 1,5 puntos de vol de vega en cada entrada y cada 30 días
en posición (horquilla de opciones + comisiones + cobertura delta). Sin funding en trimestrales. Supuestos anotados: el capital del contado sirve de
garantía del corto (margen cruzado, como F06); la varianza diaria es una APROXIMACIÓN de un straddle cubierto en delta: con movimientos enormes
pierde de forma cuadrática, más que un straddle real (conservador en la cola).

## Datos y periodos
Futuros trimestrales BTCUSDT USDT-M y contado 1 h de Binance Vision (2021-01 → hoy; el primer trimestral USDT-M vence el 2021-03-26);
DVOL diario de Deribit (desde 2021-03-24). Evaluación: basis desde 2021-01-01, VRP desde 2021-05-01 (calentamiento de 30 d).
Subperiodos X inicio → 2023-12 · Y 2024-01 → hoy. Sin entrenamiento: toda la muestra es fuera de muestra respecto a los parámetros.

## Contraste (`src/primas/evaluar.py`, ejecución única)
C1 Sharpe > 0 y p unilateral de la media diaria (HAC, 5 retardos) con Holm sobre las 4 < 0,10 · C2 Sharpe > 0 en X y en Y ·
C3 Sharpe > 0 con costes ×2 · C4 Deflated Sharpe ≥ 0,80 con n = 269 y varianza nula 1/T · C5 ≥ 20 operaciones o rollos
(el basis abre como mucho una posición por trimestre). **Certificada = C1–C5.**
Diagnóstico (no decide): CAGR, USDT/mes, caída, peor día, CVaR, correlación con el núcleo y con el carry de funding, años, y si añadirla como
tercer bolsillo a la paridad de riesgo núcleo + carry (K1) sube su Sharpe. PBO/CPCV (filtro de la Fase 1) no aplica: nada se ajusta con datos
y cada familia tiene 2 variantes.

## Hacia delante
Las certificadas pasan a papel con 1.000 USDT cada una desde el día siguiente a la evaluación (rutina diaria) y entrarían como bolsillo de una
versión nueva del gestor de cartera (prueba nueva). **Dinero real: nada.** Requiere ≥ 90 días en papel y aprobación EXPRESA del dueño.
Riesgos fuera del dato: quiebra del exchange, desapalancamiento automático, liquidez de opciones en crisis (V01/V02 pueden perder mucho en un día).
