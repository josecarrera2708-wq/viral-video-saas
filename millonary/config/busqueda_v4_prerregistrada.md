# Búsqueda v4 · patrones chartistas, velas japonesas e ineficiencias (prerregistro, 2026-10-05)

Petición del dueño: «dejemos como está lo que funciona en modelo fondo de inversión. Busquemos las mejores estrategias documentadas
estadísticamente de traders que operan patrones: acción de precio, ineficiencias, velas de alto acierto, doble/triple techo y suelo,
estrella de la mañana, banderines, triángulos, tazas».
Las mesas y estrategias en marcha NO se tocan. Este documento y el código (`src/busqueda/v4.py`, `src/busqueda/evaluate_v4.py`)
se registran en git ANTES de ejecutar. Pruebas nº 1110-1517 (408 variantes).

## Lo documentado (investigación, 2026-10-05)
- **Bulkowski, *Encyclopedia of Chart Patterns*:** estadística de miles de patrones en acciones de EE. UU.
  - Taza con asa: puesto 3 de 39 alcistas; 5 % de fallo hasta el punto muerto.
  - Doble suelo: subida media del 40 % y fallo del 11 %. «Eve & Eve» es la mejor variante.
- **Bulkowski, *Encyclopedia of Candlestick Charts*:** «acierto» = el precio gira en la dirección esperada, NO beneficio tras costes.
  - Mejores velas: tres líneas (three-line strike) 84 % / 65 %, tres cuervos negros 78 % y estrella de la tarde 72 %.
- **Estudios académicos en cripto:**
  - Con costes realistas, las velas japonesas no superan al azar.
  - Excepción: la continuación tras velas seguidas en futuros de BTC (Applied Economics Letters 2021).
- **Lo, Mamaysky y Wang (2000):** los patrones aportan algo de información, pero poca.

## Reglas (código congelado con este commit)
- **Familias (17):**
  - B01 doble suelo, B02 doble techo, B03 triple suelo/techo, B04 hombro-cabeza-hombro (y el invertido).
  - B05 triángulo ascendente, B06 triángulo descendente, B07 triángulo simétrico.
  - B08 rectángulo, B09 bandera/banderín, B10 taza con asa.
  - V01 envolvente de giro, V02 estrella de la mañana/tarde, V03 tres soldados / tres cuervos.
  - V04 tres líneas (three-line strike), V05 martillo / estrella fugaz en extremo, V06 cuatro velas seguidas (continuación).
  - I01 ineficiencia (FVG) con retesteo.
- **Pivotes fractales:** 3 velas a cada lado, conocidos solo 3 velas después. Las rupturas se toman al CIERRE y se entra en la apertura siguiente.
- **Stop estructural:** más allá del patrón + 0,25 ATR, limitado a 0,5-6 ATR.
- **Rejilla:** 3 temporalidades (1 h, 4 h, diario) × 17 familias × 2 filtros (sin filtro / a favor de tendencia) × 4 salidas = 408 variantes.
  - Filtro de tendencia: cierre y EMA50 al mismo lado de la EMA200.
  - Salidas:
    - TP 1R, que equivale a la «regla de la medida» porque el stop está al otro lado del patrón.
    - TP 2R.
    - TP 3R.
    - Dejar correr: cierre al otro lado de la EMA50.
  - Límite de tiempo con TP: 72 velas (1 h), 42 (4 h) y 20 (diario).

## Evaluación (idéntica a v2/v3)
Datos: perpetuo Binance BTCUSDT.

| Periodo | Desde | Hasta |
|---|---|---|
| Construcción | 2020-03 | 2024-01 |
| Validación | 2024-01 | 2025-07 |
| Examen | 2025-07 | 2026-09-28 |

- Motor `src/backtest/engine.py`: taker 0,05 %, deslizamiento 2 pb, funding real, riesgo 0,5 %.
- Elegible: R>0 en construcción y en validación, con ≥30 ops en validación (≥10 en diario).
- Examen: las elegibles, como máximo 20, por t de validación.
- Puertas:
  - G1: R>0 con ≥20 ops.
  - G2: p de Holm <0,10.
  - G3: R>0 con costes ×2.
  - G4: caída <30 %.
  - G5: DSR ≥0,80 con n_trials = 408.
- Certificada = 5/5. Sin certificación no hay dinero real, que además exige la aprobación EXPRESA del dueño.
- Se informa el acierto (% de operaciones ganadoras), porque el dueño lo pide, pero el criterio es la R media tras costes.

## Mesa de patrones en papel (regla fijada ANTES de ver los resultados)
- Composición: la mejor variante elegible de cada familia, por t de validación. Las familias sin ninguna elegible quedan fuera.
- Inicio: las 00:00 UTC siguientes al commit de los resultados.
- Fuente: Deribit (desde las velas de 15 min), 1.000 USDT de papel por trader, mismo motor.
- Apodos solo de presentación.
- Sin tocar reglas durante la prueba.
