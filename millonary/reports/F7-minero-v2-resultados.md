# Minero v2 (price action + datos exógenos, solo 4h/1d) · walk-forward 2022-01 → 2025-06

Cambios frente a la v1: 14 tipos de entrada (añade barras interiores, NR7, falsas rupturas,
retest de soportes/resistencias, momentum de series temporales, retroceso a la media móvil),
11 filtros de régimen combinables de dos en dos (marco temporal superior, estructura HH/HL,
Fear & Greed, funding extremo, open interest, VIX, dólar…), solo velas 4h y diarias, fitness de
consistencia por bloques. ≈17.000 pruebas únicas por ventana, 7 ventanas de 6 meses.
Periodo ciego (≥ 2025-07-01): **no tocado.**

| Cartera (1.270 días OOS) | Sharpe | Retorno | DD máx. | CAGR | DSR (N=14) |
|---|---|---|---|---|---|
| Minero top 5 | 0,13 | +2,4 % | 13,5 % | 0,7 % | 0,48 |
| Minero top 5, vol. target 15 % | 0,19 | +6,2 % | 28,5 % | 1,7 % | 0,52 |
| Minero top 10 | 0,31 | +6,3 % | 7,4 % | 1,8 % | 0,61 |
| Minero top 10, vol. target 15 % | 0,31 | +13,7 % | 18,4 % | 3,8 % | 0,62 |
| **Conjunto canónico 4h** (SMA 50/200 y Donchian 50, largo y largo+corto) | **1,03** | +32,2 % | 6,4 % | 8,3 % | — |
| **Conjunto canónico 4h, vol. target 15 %** | **1,04** | **+68,8 %** | 16,3 % | 16,2 % | — |
| Momentum 20/60/120 días | 0,63 | +12,4 % | 7,5 % | 3,4 % | — |
| Momentum 20/60/120 días, vol. target 15 % | 0,75 | +34,0 % | 13,3 % | 8,7 % | — |
| Comprar y mantener BTC | 0,72 | +131,7 % | 66,9 % | 27,2 % | — |
| Nulo A: 10 reglas aleatorias elegibles (mediana / p95) | 0,03 / 0,68 | +0,1 % | — | — | — |
| Nulo B: 10 al azar entre las halladas (mediana / p95) | 0,19 / 0,61 | +3,2 % | — | — | — |

Retorno por ventana (top 10 minero): −5,6 %, −0,6 %, +8,3 %, +6,9 %, +1,2 %, −2,2 %, −1,2 %.

## Lectura honesta
1. **El minero sigue sin aportar ventaja demostrable.** Sharpe OOS 0,13–0,31. El 24 % de las
   carteras aleatorias (nulo A) y el 33 % de las del nulo B igualan o superan al minero (top 10).
   Añadir price action y datos exógenos NO ha cambiado esto.
2. **Restringir a 4h/1d y penalizar por consistencia arregló el desastre de la v1** (el nulo A
   pasó de Sharpe −1,53 a +0,03), es decir, ya no se pierde por costes. Pero eso no crea ventaja.
3. **Los conjuntos simples de tendencia superan al minero con claridad** (Sharpe ≈ 1,0 frente a
   0,3), con menos caída y con un vol-target del 15 % anual: +69 % con DD del 16 %.
4. Ninguna cartera supera a comprar y mantener en retorno absoluto (+132 %), aunque el
   drawdown es 4 veces menor.

## Cautelas (importantes, no las escondo)
- **El conjunto canónico lo elegí yo** conociendo el historial general de BTC. Son 4 reglas, unas
  ≈130 operaciones en total; una sola trayectoria de precio (2022 bajista → 2023-25 alcista).
  No es una prueba estadística. Cuenta como variante en el registro.
- Con un solo activo y un solo régimen dominante, un Sharpe ~1 de seguimiento de tendencia es
  compatible con suerte. Falta contraste en otras épocas (2017-2019 spot) y otros activos.
- El vol-target usa retornos diarios de una cartera de sub-cuentas y aproxima costes y liquidación
  proporcionalmente; hay que validar con el motor completo antes de operar.

## Registro de variantes de proceso (para el DSR acumulado)
v1: 3 (minero top 5/10/20) + 5 (reglas canónicas) = 8.
v2: 4 (minero top 5/10 × raw/vol-target) + 2 (conjunto canónico, momentum) = 6.
**Total: 14.** (Además, ≈50.000 estrategias únicas minadas en total.)
