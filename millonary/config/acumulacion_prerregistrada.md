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
