# Búsqueda v12 · filtro estadístico de entradas (meta-etiquetado)

Eventos en desarrollo (2020-10→2026-09): **15961** · G0 (etiquetas barajadas): AUC 0.502 → FALLA

## Fuera de muestra (walk-forward trimestral 2022-10→2026-09), riesgo unitario

| Configuración · modelo | Tomadas | Ops/año | Acierto | Empate | R media | t (día) | Trim. + | ×2 costes | AUC | Brier skill |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 2R | logistica | 0% | 3 | 60% | 32% | +0.563 | 1.41 | 2/16 | +0.433 | 0.543 | +0.003 |
| C1 2R | boosting | 0% | 2 | 67% | 48% | +0.450 | 0.86 | 4/16 | +0.314 | 0.558 | +0.008 |
| C1 2R | bosque | 0% | 5 | 38% | 45% | -0.157 | -0.61 | 5/16 | -0.331 | 0.562 | +0.009 |
| C1 2R | media | 0% | 1 | 50% | 23% | +0.320 | 0.00 | 1/16 | +0.150 | 0.560 | +0.009 |
| C2 3R | logistica | 0% | 3 | 64% | 47% | +0.174 | 0.85 | 3/16 | -0.019 | 0.547 | +0.004 |
| C2 3R | boosting | 0% | 4 | 67% | 51% | +0.242 | 1.02 | 6/16 | +0.015 | 0.560 | +0.009 |
| C2 3R | bosque | 0% | 2 | 67% | 42% | +0.510 | 1.25 | 4/16 | +0.310 | 0.565 | +0.009 |
| C2 3R | media | 0% | 1 | 100% | 100% | +0.794 | 4.08 | 3/16 | +0.671 | 0.562 | +0.010 |
| C3 2R + protección (promediar 1 vez) | logistica | 0% | 6 | 80% | 79% | +0.010 | 0.08 | 8/16 | -0.027 | 0.635 | +0.105 |
| C3 2R + protección (promediar 1 vez) | boosting | 0% | 5 | 75% | 75% | +0.001 | 0.01 | 3/16 | -0.037 | 0.646 | +0.120 |
| C3 2R + protección (promediar 1 vez) | bosque | 0% | 9 | 68% | 72% | -0.049 | -0.40 | 5/16 | -0.097 | 0.648 | +0.118 |
| C3 2R + protección (promediar 1 vez) | media | 0% | 3 | 70% | 74% | -0.058 | -0.30 | 3/16 | -0.096 | 0.648 | +0.120 |

Referencia «tomar todas»: C1 2R: 10704 ops, acierto 36%, R -0.223 · C2 3R: 10704 ops, acierto 35%, R -0.228 · C3 2R + protección (promediar 1 vez): 10704 ops, acierto 43%, R -0.087

## Puertas (media de los 3 modelos)

**C1 2R** — 1/7 · p frente a tomar todas 0.243 · DSR nan · Sharpe anual 0.00
- ❌ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥600, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ✅ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥250 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento por temporalidad): 2 ops, final 1000 USDT, mes medio -0.0% (mediana -0.0%), meses negativos 1/2, caída máx. 0%, riesgo medio 0.62%, apalancamiento medio 15m 2.0x, 1h 0.1x (máx. 2.0x)

**C2 3R** — 1/7 · p frente a tomar todas 0.000 · DSR nan · Sharpe anual 0.00
- ❌ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥600, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ✅ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥250 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento por temporalidad): 4 ops, final 1017 USDT, mes medio +0.5% (mediana +0.5%), meses negativos 0/3, caída máx. 0%, riesgo medio 0.62%, apalancamiento medio 1h 0.7x (máx. 1.8x)

**C3 2R + protección (promediar 1 vez)** — 0/7 · p frente a tomar todas 0.380 · DSR nan · Sharpe anual 0.00
- ❌ G0 técnico (barajado AUC≤0,52)
- ❌ G1 n≥600, t≥3, R>0 sin 2025-07→
- ❌ G2 mejor que tomar todas (p<0,10) y acierto ≥ empate+3
- ❌ G3 ≥10/16 trimestres positivos
- ❌ G4 R>0 a costes ×2
- ❌ G5 DSR≥0,95
- ❌ G6 ≥250 ops/año y Sharpe<5
- Cartera (1.000 USDT, Kelly/4 entre 0,25 % y 1 %, ≤2 posiciones, tope de apalancamiento por temporalidad): 10 ops, final 997 USDT, mes medio -0.1% (mediana +0.0%), meses negativos 2/5, caída máx. 1%, riesgo medio 0.85%, apalancamiento medio 1h 0.3x (máx. 0.5x)

## Decisión

- Elegida: **ninguna**
- Ninguna configuración pasa todas las puertas: no hay papel (regla prerregistrada).
