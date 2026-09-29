# Registro de pruebas (para corregir por comparaciones múltiples)

Cada variante de PROCESO o regla evaluada cuenta, se apruebe o no. Última actualización: 2026-09-29.

| # | Prueba | Resultado |
|---|---|---|
| 1–3 | Minero v1, top 5/10/20 (walk-forward 2022-25) | Sharpe OOS 0,36 / 0,17 / 0,08 |
| 4–8 | 5 reglas canónicas de tendencia | Sharpe OOS 0,79 / 0,98 / 0,73 / 1,17 / 0,08 |
| 9–12 | Minero v2, top 5/10 × bruto/vol-target | Sharpe OOS 0,13–0,31 |
| 13–14 | Conjunto canónico 4h; momentum 20/60/120 d | Sharpe OOS 1,03 / 0,63 (0,75 con vol-target) |
| 15 | **Núcleo v1 prerregistrado** (2017-2025.06) | Sharpe 1,10; 6/6 criterios; ciego +0,9 % dentro de bandas |
| 16 | Variante F (filtro de funding p95) | Rechazada: no reduce la caída |
| 17 | Recorte ×0,5 alrededor del FOMC (2021-2025.06) | **Rechazada**: Sharpe 0,78 → 0,74; −0,85 %/año (IC90 −1,8 % a +0,1 %) |
| 18–23 | 6 variantes de sombra del Laboratorio (exploratorio, 2017-2025.06) | Sharpe 1,00–1,13; ninguna mejora al núcleo por ≥ 0,3 |

Estrategias únicas minadas (no usadas para elegir el núcleo): ≈ 66.000 (v1 32.304 + 8 ventanas WFO v1 ≈ 113.000 evaluaciones + v2 ≈ 119.000).
El periodo ciego (2025-07 → 2026-08) se abrió UNA vez y está consumido.

## Desviaciones anotadas (no corregidas: ni cambian resultados ni se retocan parámetros)
- La Pata A se decide al cierre diario (00:00 UTC) y se aplica desde la vela de las 04:00 del día siguiente (4 h de retraso extra
  frente a "desde la vela siguiente"). Es igual en backtest y en vivo (revisión Opus, hallazgo 8).
- El freno de pérdida diaria mide la caída intradía desde las 00:00 UTC (máx. histórica 5,8 %), no cierre a cierre (4,7 %).
