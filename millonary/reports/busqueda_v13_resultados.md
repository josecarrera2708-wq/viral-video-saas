# Búsqueda v13 · swing 1-3 días con filtro estadístico

Eventos en desarrollo (2020-10→2026-09): **3283** · G0 (etiquetas barajadas): AUC 0.484 → OK

## Fuera de muestra (walk-forward trimestral 2022-10→2026-09), riesgo unitario

| Configuración · modelo | Tomadas | Ops/año | Acierto | Empate | R media | t (día) | Trim. + | ×2 costes | AUC | Brier skill |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 2R | logistica | 4% | 20 | 48% | 43% | +0.078 | 0.57 | 10/16 | +0.036 | 0.511 | -0.002 |
| C1 2R | boosting | 4% | 24 | 39% | 39% | +0.002 | 0.01 | 8/16 | -0.076 | 0.523 | -0.002 |
| C1 2R | bosque | 0% | 0 | 0% | 100% | +0.000 | 0.00 | 0/16 | +0.000 | 0.499 | +0.000 |
| C1 2R | media | 1% | 5 | 53% | 46% | +0.086 | 0.41 | 4/16 | +0.044 | 0.519 | +0.002 |
| C2 3R | logistica | 3% | 16 | 52% | 50% | +0.023 | 0.20 | 7/16 | -0.032 | 0.510 | -0.001 |
| C2 3R | boosting | 1% | 7 | 39% | 38% | +0.022 | 0.08 | 5/16 | -0.023 | 0.504 | -0.003 |
| C2 3R | bosque | 0% | 0 | 0% | 100% | +0.000 | 0.00 | 0/16 | +0.000 | 0.506 | +0.000 |
| C2 3R | media | 0% | 2 | 25% | 73% | -0.632 | -3.00 | 2/16 | -0.665 | 0.510 | +0.001 |
| C3 2R + protección (promediar 1 vez) | logistica | 5% | 29 | 59% | 62% | -0.020 | -0.45 | 7/16 | -0.038 | 0.484 | -0.010 |
| C3 2R + protección (promediar 1 vez) | boosting | 5% | 26 | 71% | 61% | +0.075 | 1.65 | 11/16 | +0.059 | 0.521 | -0.001 |
| C3 2R + protección (promediar 1 vez) | bosque | 0% | 0 | 0% | 100% | +0.000 | 0.00 | 0/16 | +0.000 | 0.470 | +0.000 |
| C3 2R + protección (promediar 1 vez) | media | 1% | 6 | 61% | 71% | -0.068 | -0.78 | 6/16 | -0.084 | 0.504 | -0.001 |

Referencia «tomar todas»: C1 2R: 2250 ops, acierto 43%, R -0.032 · C2 3R: 2250 ops, acierto 42%, R -0.015 · C3 2R + protección (promediar 1 vez): 2250 ops, acierto 63%, R -0.010

## Puertas (media de los 3 modelos)

**C1 2R** — 2/7 · p frente a tomar todas 0.284 · DSR nan · Sharpe anual 0.00
- ✅ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥400, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ✅ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥100 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento 3x (≤2 h) / 2x (4 h)): 19 ops, final 1018 USDT, mes medio +0.2% (mediana +0.1%), meses negativos 5/12, caída máx. 2%, riesgo medio 0.69%, apalancamiento medio 1h 0.2x, 2h 0.0x (máx. 0.5x)

**C2 3R** — 1/7 · p frente a tomar todas 0.985 · DSR nan · Sharpe anual 0.00
- ✅ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥400, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ❌ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥100 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento 3x (≤2 h) / 2x (4 h)): 8 ops, final 973 USDT, mes medio -0.4% (mediana -0.4%), meses negativos 5/7, caída máx. 3%, riesgo medio 0.57%, apalancamiento medio 1h 0.1x, 2h 0.1x (máx. 0.3x)

**C3 2R + protección (promediar 1 vez)** — 1/7 · p frente a tomar todas 0.780 · DSR nan · Sharpe anual 0.00
- ✅ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥400, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ❌ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥100 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento 3x (≤2 h) / 2x (4 h)): 22 ops, final 989 USDT, mes medio -0.1% (mediana +0.0%), meses negativos 6/14, caída máx. 2%, riesgo medio 1.00%, apalancamiento medio 1h 0.1x, 2h 0.1x, 5m 0.1x (máx. 0.2x)

## Decisión

- Elegida: **ninguna**
- Ninguna configuración pasa todas las puertas: no hay papel (regla prerregistrada).
