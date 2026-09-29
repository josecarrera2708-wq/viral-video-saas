# F1 · Informe de calidad de datos (2026-09-29)

**Fuente única de precios:** Binance Vision (`data.binance.vision`), archivos públicos oficiales.
**Seguridad aplicada:** solo HTTPS a hosts en lista blanca, sin redirecciones; cada zip verificado
contra su `.CHECKSUM` SHA-256 oficial (todos coincidieron); inspección del zip (1 miembro, nombre
esperado, sin rutas, tamaño acotado) y lectura en memoria, sin extraer ni ejecutar nada; contenido
interpretado solo como CSV numérico. Librerías instaladas desde PyPI con nombres exactos
(pandas, pyarrow, numba, scipy, matplotlib, requests). Los datos no se suben a git (`data/`).

## Cobertura (hasta 2026-09-28)
| Serie | Desde | Filas | Huecos | Notas |
|---|---|---|---|---|
| Spot BTCUSDT 1d | 2017-08-17 | 3.302 (+28 recientes) | 0 | limpio |
| Spot BTCUSDT 4h | 2017-08-17 | 19.794 (+168) | 17 velas | huecos 2017-2019 (mantenimientos) |
| Spot BTCUSDT 1h | 2017-08-17 | 79.117 (+672) | 170 velas | incl. ≈75 h el 2018-02-08 |
| Spot BTCUSDT 15m | 2017-08-17 | 316.414 (+2.688) | 643 velas | idem |
| Perp USDT-M 1h | 2020-01-01 | 58.440 (+672) | **0** | limpio |
| Perp USDT-M 4h | 2020-01-01 | 14.610 (+168) | **0** | limpio |
| Funding perp | 2020-01-01 | 7.305 | — | cada 8 h |
| Fear & Greed | 2018-02-01 | 3.159 | — | hoy = 73 |
| FRED | DFF, DGS10, DGS2, CPIAUCSL, UNRATE, VIXCLS, DTWEXBGS, T10YIE | — | — | hasta sept-2026 |

*Nota:* Binance no publica 2019-09→2019-12 en el perpetuo mensual (empezamos en 2020-01).

## Comprobaciones
- 0 duplicados, 0 velas con OHLC incoherente (high < max, low > min, precios ≤ 0) en todas las series.
- Cambio de unidad de tiempo: desde 2025 Binance usa **microsegundos**; el cargador lo detecta por
  magnitud. Sin esto, las fechas de 2025+ saldrían mal.
- 1h agregada a 4h/1d vs velas descargadas: en el perpetuo coinciden (dif. máx. 0,12 % en 1 vela de
  14.610). En el spot, 10 velas de 4h en **feb-2018** difieren hasta ≈1,6 %: efecto de la caída de
  servidor del 8-feb-2018. **Zona a excluir del backtest: 2018-02-08 → 2018-02-11.**
- Mayor movimiento en una vela de 1h: 18,2 % (spot) y 18,7 % (perp): eventos reales (p. ej.
  mar-2020 y oct-2025), no errores.

## Decisiones que se derivan
1. **El perpetuo (2020-01 en adelante) es la serie principal** para minar y validar: sin huecos y con
   funding. ~6,7 años.
2. El **spot 2017-2019** solo se usa como ampliación (tendencias de largo plazo), no para minar en
   1h/15m por los huecos.
3. Excluir 2018-02-08→11 del spot.

## Límites que quedan
- **Las APIs en vivo de Binance (HTTP 451) y Bybit (HTTP 403) están bloqueadas desde este servidor**
  (restricción por región). Sirven los datos históricos de Binance Vision, no la operativa en vivo.
  El paper trading (F9) deberá correr en un **VPS en una región permitida** o desde tu PC.
- Sin datos de 1m ni de open interest todavía (opcional, fase posterior).
- Datos de un solo exchange (Binance). Bybit puede diferir ligeramente en precios y funding.
