# Búsqueda v2 · acción de precio a favor de tendencia (15 min · 1 h · 4 h · diario)

Variantes: **768** · elegibles (R>0 en construcción y validación, ≥30 ops): **176** · finalistas al examen: **20** · certificadas: **0**

## Qué funciona mejor de media (R por operación; construcción / validación)

**tf**: 15m -0.341 / -0.227 · 1d +1.048 / +0.146 · 1h -0.025 / +0.019 · 4h +0.195 / +0.117

**setup**: S1 Ruptura 20 velas +0.597 / +0.092 · S2 Retroceso a EMA20 +0.117 / -0.015 · S3 Barra interior +0.246 / +0.019 · S4 Envolvente en retroceso +0.016 / -0.039 · S5 Pin bar en retroceso -0.106 / -0.052 · S6 Cruce EMA 9/21 +0.445 / +0.077

**modo**: ambos +0.108 / -0.003 · solo_largos +0.330 / +0.031

**stop**: 1ATR +0.250 / -0.053 · 2ATR +0.237 / +0.043 · 3ATR +0.193 / +0.060 · estructura +0.197 / +0.005

**salida**: TP2 -0.039 / -0.049 · TP3 +0.005 / -0.025 · TP5 +0.073 / +0.026 · dejar_correr +0.837 / +0.103

## Finalistas (examen 2025-07 → 2026-09)

| Variante | Ops/día | Acierto | R constr. | R valid. | R examen | R ×2 costes | Caída | p Holm | DSR | Puertas | Cert. |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 4h | S3 Barra interior | solo_largos | 2ATR | TP2 | 0.09 | 38% | +0.119 | +0.436 | -0.055 | -0.108 | 3% | 1.00 | 0.00 | 1/5 | — |
| 4h | S6 Cruce EMA 9/21 | solo_largos | 2ATR | TP2 | 0.05 | 30% | +0.106 | +0.529 | -0.219 | -0.275 | 4% | 1.00 | 0.00 | 1/5 | — |
| 4h | S2 Retroceso a EMA20 | solo_largos | estructura | TP3 | 0.08 | 27% | +0.127 | +0.443 | -0.142 | -0.222 | 6% | 1.00 | 0.00 | 1/5 | — |
| 4h | S2 Retroceso a EMA20 | solo_largos | estructura | TP5 | 0.07 | 26% | +0.061 | +0.574 | -0.085 | -0.167 | 7% | 1.00 | 0.00 | 1/5 | — |
| 4h | S1 Ruptura 20 velas | solo_largos | 2ATR | TP2 | 0.06 | 37% | +0.249 | +0.392 | +0.033 | -0.017 | 2% | 1.00 | 0.00 | 2/5 | — |
| 4h | S3 Barra interior | ambos | 2ATR | TP2 | 0.19 | 38% | +0.101 | +0.288 | -0.037 | -0.083 | 5% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | ambos | estructura | TP2 | 0.17 | 36% | +0.090 | +0.287 | -0.126 | -0.177 | 7% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | estructura | TP3 | 0.07 | 40% | +0.238 | +0.436 | +0.044 | -0.016 | 3% | 1.00 | 0.00 | 2/5 | — |
| 1h | S6 Cruce EMA 9/21 | solo_largos | estructura | TP5 | 0.19 | 33% | +0.022 | +0.366 | +0.053 | -0.064 | 7% | 1.00 | 0.00 | 2/5 | — |
| 4h | S2 Retroceso a EMA20 | solo_largos | 2ATR | TP2 | 0.08 | 31% | +0.133 | +0.331 | -0.122 | -0.179 | 5% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | 3ATR | TP5 | 0.05 | 48% | +0.219 | +0.475 | +0.325 | +0.282 | 2% | 1.00 | 0.00 | 3/5 | — |
| 4h | S6 Cruce EMA 9/21 | ambos | 2ATR | TP2 | 0.11 | 35% | +0.067 | +0.355 | -0.148 | -0.197 | 5% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | estructura | TP5 | 0.06 | 36% | +0.325 | +0.492 | +0.046 | -0.015 | 4% | 1.00 | 0.00 | 2/5 | — |
| 4h | S2 Retroceso a EMA20 | solo_largos | 2ATR | TP3 | 0.07 | 25% | +0.114 | +0.396 | -0.079 | -0.137 | 5% | 1.00 | 0.00 | 1/5 | — |
| 4h | S1 Ruptura 20 velas | ambos | 2ATR | TP2 | 0.13 | 33% | +0.108 | +0.274 | -0.035 | -0.077 | 5% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | 2ATR | TP5 | 0.07 | 38% | +0.396 | +0.493 | +0.239 | +0.178 | 3% | 1.00 | 0.00 | 3/5 | — |
| 4h | S6 Cruce EMA 9/21 | solo_largos | 2ATR | TP3 | 0.05 | 23% | +0.090 | +0.523 | -0.222 | -0.281 | 4% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | 1ATR | TP5 | 0.10 | 21% | +0.130 | +0.508 | -0.013 | -0.122 | 6% | 1.00 | 0.00 | 1/5 | — |
| 4h | S3 Barra interior | solo_largos | 3ATR | TP3 | 0.05 | 46% | +0.149 | +0.364 | +0.263 | +0.225 | 2% | 1.00 | 0.00 | 3/5 | — |
| 4h | S3 Barra interior | ambos | estructura | TP3 | 0.16 | 35% | +0.106 | +0.293 | -0.053 | -0.109 | 6% | 1.00 | 0.00 | 1/5 | — |
