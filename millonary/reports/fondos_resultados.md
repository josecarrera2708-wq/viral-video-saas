# Mesa de fondos · resultados históricos (2017-08-18 → 2026-10-01; evaluación desde 2018-09, carry desde 2020)

Certificadas: **1/10** · Aportan al núcleo (mezcla 50/50 en riesgo mejora su Sharpe): **1**
Referencias: núcleo v1 Sharpe 1.04 (caída 25%); comprar y mantener Sharpe 0.81 (caída 77%)

| Estrategia | Sharpe | A | B | C | ×2 costes | CAGR | caída | ops | p Holm | DSR | corr. núcleo | mezcla vs núcleo | Kelly | Puertas | Cert. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F01 Tortugas S1 (Dennis, 20/10) | 0.42 | 0.67 | 0.51 | 0.08 | 0.34 | +4.6% | 17% | 126 | 0.633 | 0.04 | +0.59 | 0.83 vs 1.04 | 3.3× | 3/5 | — |
| F02 Tortugas S2 (Dennis, 55/20) | 0.18 | -0.21 | 0.43 | -0.08 | 0.10 | +1.5% | 32% | 99 | 0.675 | 0.01 | +0.53 | 0.50 vs 1.04 | 1.0× | 2/5 | — |
| F03 Momentum 12 m (AQR/MOP) | 0.37 | -0.87 | 0.70 | 0.56 | 0.37 | +6.6% | 53% | 98 | 0.633 | 0.04 | +0.32 | 0.81 vs 1.04 | 1.4× | 2/5 | — |
| F04 Media 200 d (Tudor Jones) | 0.72 | 0.86 | 0.72 | 0.64 | 0.71 | +24.4% | 68% | 65 | 0.180 | 0.21 | +0.78 | 0.98 vs 1.04 | 1.6× | 3/5 | — |
| F05 Ruptura de volatilidad (L. Williams) | 0.69 | 1.47 | 0.59 | 0.35 | 0.07 | +18.8% | 63% | 1172 | 0.173 | 0.18 | +0.50 | 0.98 vs 1.04 | 2.1× | 3/5 | — |
| F06 Carry de funding (cash-and-carry) | 7.03 | — | 7.53 | 7.44 | 4.64 | +10.9% | 3% | 98 | 0.000 | 1.00 | -0.02 | 4.60 vs 1.03 | 475.7× | 5/5 | ✔ |
| F07 Volatilidad gestionada (Moreira-Muir) | 0.52 | 0.15 | 0.57 | 0.63 | 0.51 | -3.0% | 95% | 314 | 0.391 | 0.09 | +0.71 | 0.82 vs 1.04 | 0.5× | 3/5 | — |
| F08 Turtle Soup +1 (Raschke) | -1.32 | -1.29 | -1.95 | -0.70 | -1.45 | -1.9% | 16% | 61 | 1.000 | 0.00 | -0.03 | 0.27 vs 1.04 | -88.4× | 1/5 | — |
| F09 NR7 (Crabel) | 0.59 | 1.36 | 0.37 | 0.50 | 0.09 | +2.4% | 7% | 419 | 0.315 | 0.10 | +0.04 | 0.92 vs 1.04 | 14.5× | 3/5 | — |
| F10 Cartera multiestrategia (paridad de riesgo) | 0.24 | -0.61 | 0.58 | 2.02 | 0.18 | +2.6% | 47% | 101 | 0.675 | 0.02 | +0.24 | 0.66 vs 1.04 | 1.3× | 2/5 | — |

Kelly = apalancamiento de Kelly completo sobre el tamaño de la propia estrategia (μ/σ²); se usa como mucho ¼–½ Kelly por la incertidumbre de μ.
Periodos: A 2018-09→2019-12 · B 2020-01→2023-12 · C 2024-01→hoy. p = media diaria > 0 (HAC), Holm sobre las 10.
