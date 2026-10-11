# Walk-forward del proceso completo (2022-01 → 2025-06, fuera de muestra)

Proceso evaluado: en cada una de 7 ventanas de 6 meses, el minero (4 islas × 300 × 15 generaciones,
≈16.000 pruebas únicas por ventana) solo ve datos anteriores a la ventana (mercado truncado
físicamente); se eligen las M mejores por fitness de entrenamiento (descorrelacionadas, solo con
datos de train) y se operan en los 6 meses siguientes con costes reales. Cartera equiponderada.
Periodo ciego (≥ 2025-07-01): **no se ha tocado.**

| Cartera (1.270 días fuera de muestra) | Sharpe | Retorno total | Drawdown máx. | DSR (N=3) |
|---|---|---|---|---|
| Minero, top 5 | 0,36 | +15,9 % | 14,9 % | 0,68 |
| Minero, top 10 | 0,17 | +4,9 % | 15,2 % | 0,54 |
| Minero, top 20 | 0,08 | +1,1 % | 19,8 % | 0,47 |
| Comprar y mantener BTC | 0,72 | +131,7 % | 66,9 % | — |
| Nulo A: 10 reglas aleatorias elegibles | −1,53 (mediana) | −27,9 % | — | — |
| Nulo B: 10 al azar entre las halladas por el minero | 0,07 (mediana; p95 = 0,40) | +0,9 % | — | — |

Retorno por ventana (top 10): −12,2 %, −2,5 %, +9,6 %, −0,8 %, +9,5 %, +3,3 %, −0,3 %.

## Lectura honesta
1. **El proceso "minar + elegir por fitness" no produce ventaja demostrable fuera de muestra.**
   Sharpe entrenamiento ≈ 1,5 → fuera de muestra 0,1–0,4. Ningún DSR llega a 0,95.
2. **El ranking del minero no aporta nada sobre el azar entre las halladas:** el 30 % de las
   carteras del nulo B iguala o supera al minero (top 10). Lo que "funciona" es haber filtrado reglas
   que no pierden por costes (frente al nulo A, mediana −1,53), no saber cuáles serán las mejores.
3. **Quedan por debajo de comprar y mantener** en rentabilidad (+5–16 % frente a +132 %), aunque con
   drawdown mucho menor (15 % frente a 67 %) y sin exposición direccional permanente.
4. Todo lo anterior es con señales SOLO de precio y volumen.

## Líneas base canónicas (declaradas antes de ejecutarlas, sin ajustar), misma ventana
| Regla (stop 3×ATR, salida por señal contraria, riesgo 1 %) | Operaciones | Sharpe | Retorno | DD máx. |
|---|---|---|---|---|
| Cruce SMA 50/200 en 4h (largo+corto) | 36 | 0,79 | +25,4 % | 8,9 % |
| Cruce SMA 50/200 en 4h (solo largos) | 25 | 0,98 | +31,9 % | 6,5 % |
| Ruptura Donchian 50 en 4h (largo+corto) | 70 | 0,73 | +27,3 % | 11,7 % |
| Ruptura Donchian 50 en 4h (solo largos) | 36 | 1,17 | +43,1 % | 8,4 % |
| Cruce EMA 12/50 en 1h (largo+corto) | 442 | 0,08 | −1,1 % | 25,7 % |

**Cuatro reglas clásicas de baja frecuencia (4h, pocas operaciones, stops anchos) superan a la
cartera minada** (Sharpe 0,7–1,2 frente a 0,1–0,4). La regla de 1h, con 442 operaciones, se queda en
~0 por costes.

Cautelas:
- Son 25–70 operaciones cada una: **insuficiente para certificar nada** (los intervalos de confianza
  del Sharpe son enormes).
- Elegí estas 5 reglas conociendo el historial general de BTC; hay sesgo de selección de mi lado.
  Cuentan como 5 pruebas más en el registro (ver abajo).
- Pero coinciden con lo que muestra la literatura sobre momentum de series temporales en cripto.

## Qué implica para Millonary
- **Hoy no hay un sistema rentable y validado.** Hay una pista: la ventaja, si existe, está en
  **baja frecuencia (4h o más) y seguimiento de tendencia con stops anchos**, no en muchas
  operaciones rápidas con reglas raras.
- El minero, tal como está, **sobre-busca** en 1h y castiga poco la rotación. Hay que
  (a) restringirlo a baja frecuencia, (b) penalizar coste/rotación, (c) reducir el espacio de
  búsqueda, y (d) añadir información que el precio no da (funding, open interest, Fear & Greed,
  macro; datos ya descargados y alineados sin fuga).
- Cualquier variante nueva se evalúa con el mismo walk-forward y se anota en el registro.

## Registro de variantes de PROCESO probadas (para el DSR acumulado)
| # | Variante | Resultado |
|---|---|---|
| 1–3 | WFO minero, elegir top 5 / 10 / 20 | Sharpe OOS 0,36 / 0,17 / 0,08 |
| 4–8 | 5 reglas canónicas (tabla anterior) | Sharpe OOS 0,79 / 0,98 / 0,73 / 1,17 / 0,08 |
Total de variantes contabilizadas: **8** (más las 32.304 estrategias del primer minado).
