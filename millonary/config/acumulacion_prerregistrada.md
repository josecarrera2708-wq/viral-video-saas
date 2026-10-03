# Acumulación de BTC — prerregistro (2026-10-03)

**Origen:** petición del dueño (2026-10-03): «reunir el mayor porcentaje de BTC posible» (espera que BTC suba mucho en años).
**Qué es:** una asignación decidida por el dueño, NO una prueba de ventaja: no hay puertas ni certificación. Se sigue en papel y se informa.

## Contexto ya visto (exploratorio, NO prerregistrado; 2020-01 → 2026-10, rebalanceo mensual)
Medido en BTC: cuántos BTC acabas teniendo por cada BTC que comprabas con el mismo dinero al inicio.

| Cartera | USDT final | BTC final | Caída máx. (USDT) |
|---|---|---|---|
| 100 % BTC | ×11,7 | 1,00 | 77 % |
| 50 % BTC / 25 % núcleo / 25 % carry | ×6,9 | 0,59 | 52 % |
| 50 % BTC / 50 % carry · ⅓ cada uno · 25/25/50 | — | 0,60 · 0,47 · 0,39 | 54 % · 40 % · 32 % |
| núcleo solo · carry solo | ×3,1 · ×1,9 | 0,26 · 0,16 | 25 % · 2 % |

Las mezclas ganan BTC en los años bajistas (50/25/25 en 2022: ×1,69 BTC) y lo pierden en los alcistas (2020 ×0,62; 2023 ×0,71; 2024
×0,78). Con una visión alcista de largo plazo, lo que más BTC reúne es mantener el 100 % en BTC. Las 4 mezclas vistas se anotan como
pruebas 310-313 (exploratorias) para que cuenten en el n de futuros Sharpe deflactados.

## Reglas (fijas desde este commit)
- Inicio: compra al cierre diario del 2026-10-03 (04-oct 00:00 UTC), posterior a este commit. 1.000 USDT por cartera.
- **A1 Acumulación BTC (APLICADA):** 100 % BTC al contado; compra única con comisión 0,10 %; nunca se vende ni se reequilibra.
- **A2 50 % BTC / 25 % núcleo v1 / 25 % carry (SOMBRA):** pesos fijos en capital; vuelven a los objetivo al cierre de cada fin de mes;
  15 pb por unidad de rotación (también la compra inicial). Núcleo y carry con la regla del histórico (`src.cartera.evaluar.core_daily`,
  `src.fondos.estrategias.carry`), sin tocar.
- Medidas diarias (rutina de las 04:17 UTC): equity en USDT, BTC equivalentes (equity / cierre), retorno en USDT y en BTC frente a los BTC
  que daban 1.000 USDT al precio de inicio, caída máxima.
- Código: `src/acumulacion/forward.py` → `paper_state/acumulacion/resumen.json`; tests `tests/test_acumulacion.py`.

## Lectura
Informativa, sin umbrales: a los 30 días y después cada mes, BTC de A1 frente a A2. A1 no se vende por ninguna caída (la regla es mantener).

## Qué NO cambia
Núcleo, carry, K4, la sombra B01/B02/V01 y las mesas siguen igual. **Sin dinero real:** pasar a dinero real requiere aprobación EXPRESA del dueño.

## Añadido 2026-10-03 ~14 h UTC (antes del inicio): A3, ganancias a BTC
Petición del dueño: «que las ganancias se conviertan en BTC, siempre que no suban las comisiones».
- **A3 Núcleo + carry con ganancias a BTC (APLICADA):** cuenta aparte de 1.000 USDT con núcleo v1 y carry 50/50 (misma regla del
  histórico, rebalanceo mensual, 15 pb por rotación). Al cierre de cada fin de mes, si la cuenta supera 1.000 USDT en ≥ 10 USDT, ese
  exceso se convierte en BTC al cierre (una sola compra al mes, comisión de contado 0,10 % sobre lo convertido) y la cuenta vuelve a
  1.000. Con pérdidas no se convierte nada (primero recupera los 1.000). El BTC nunca se vende. Mismo inicio que A1/A2.
- Comisiones: las de las estrategias no cambian; la conversión cuesta 0,10 % de lo convertido (1 USDT por cada 1.000), una vez al mes.
- Contexto ya visto (2020 → hoy, mismas reglas): valor ×3,9 (frente a ×2,5 del 50/50 reinvirtiendo en USDT), 0,33 BTC por cada BTC
  inicial, caída máx. 53 % (por el BTC acumulado). No certifica nada.
- Las cuentas núcleo y carry que ya corren NO se tocan: A3 es una copia aparte.
