# Mesa intradía · Prerregistro (v1) — fijado ANTES de ejecutar los resultados

Fecha: 2026-09-29. Petición del dueño: 1-2 operaciones al día para poder evaluar rápido. El núcleo v1 (baja frecuencia) NO se toca:
la mesa intradía es un sistema aparte, con su propia contabilidad.

## Universo (N = 14 traders, parámetros FIJOS en `src/intraday/setups.py`, velas de 1 h, BTCUSDT perpetuo)
I01 Rango asiático→Londres/NY · I02 Donchian 24 h · I03 Bollinger+RSI · I04 Reversión a VWAP diaria · I05 Cruce EMA 9/21+EMA200 ·
I06 RSI(2) retroceso · I07 Ruptura tras squeeze · I08 Máx./mín. de ayer · I09 Supertrend 10/3 · I10 Ráfaga de momentum ·
I11 Ruptura fallida · I12 Ichimoku 1 h · I13 Parabolic SAR+EMA200 · I14 Apertura de Nueva York.
Cada uno con STOP por ATR/estructura, TAKE-PROFIT en múltiplos de R (o salida por señal contraria) y salida por tiempo.
Calibración previa: SOLO la frecuencia de señales, medida en 2020-2023 sin calcular resultados (0,4-2,7 señales/día).
Motor: `src/backtest/engine.py` (validado): riesgo 0,5 % del capital por operación, apalancamiento máx. 5×, capital 1.000 USDT,
comisión taker 5 pb, maker 2 pb en TP, deslizamiento 2 pb, funding real, liquidación, lote mínimo y nocional mínimo.

## Periodos (datos Binance perpetuo 1 h)
Construcción 2020-01-01→2023-12-31 · Validación 2024-01-01→2025-06-30 ·
**Examen sellado 2025-07-01→2026-09-28: se mira UNA vez** (periodo que el núcleo consumió como ciego, pero estas estrategias no se han
evaluado nunca en él; aviso: conozco la trayectoria agregada de BTC en ese periodo por el ciego del núcleo, fuga menor de régimen).

## Métricas
Por trader y periodo: nº de operaciones, operaciones/día, % acierto, reparto de salidas (TP / stop / tiempo / señal / liquidación),
expectativa en R (media de R por operación) con t-stat, retorno, caída máxima, Sharpe diario.

## Puertas «certificada intradía» (7)
Q1 ≥ 0,3 operaciones/día · Q2 expectativa en R > 0 en validación Y en examen · Q3 p unilateral (t-test de R, examen) con Holm < 0,10 sobre las 14 ·
Q4 expectativa > 0 en el examen con costes ×2 (comisión, deslizamiento y maker duplicados) · Q5 prueba de truncamiento superada (la señal en la
vela i no cambia al alterar el futuro) · Q6 sin liquidación y caída máxima del examen < 40 % · Q7 Sharpe < 6 (una cifra mayor se trata como
error del backtest: red flag).
Además se informa la sensibilidad a costes ×1,5 / ×2 / ×3 y una banda de Monte Carlo (2.000 remuestreos de las R del examen) de la caída máxima y del retorno.

## Hacia delante (papel, datos de Deribit BTC-PERPETUAL 1 h, actualización cada hora, desde 2026-09-29 16:30 UTC)
Los 14 traders operan TODOS en papel (para medir), cada uno con 1.000 USDT virtuales, entrada en la apertura de la vela siguiente a la señal.
Control de deriva: la R acumulada hacia delante se compara con la banda 5-95 % del Monte Carlo del examen; salirse por abajo = alerta.
Dinero real (Fase 2) solo para traders certificados en histórico con ≥ 150 operaciones hacia delante, expectativa en R > 0 con
probabilidad posterior ≥ 0,90, dentro de la banda de deriva, y aprobación EXPRESA del dueño; tamaño mínimo.
Aviso honesto: las diferencias entre precio de Deribit y Binance y la latencia real no están en la simulación; un trader intradía real
sufre más deslizamiento que el modelo.

## Adenda (fijada antes de ejecutar): fin del examen sellado
El fichero de funding termina el 2026-08-31 (integridad exigida por el motor). El examen sellado es 2025-07-01 → 2026-08-31 (23:00 UTC), no hasta el 09-28.
