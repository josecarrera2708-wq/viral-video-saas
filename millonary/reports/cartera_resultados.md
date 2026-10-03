# Gestor de cartera (Fase 1) · resultados históricos (2020-01-01 → 2026-10-01)

Aprobadas para papel: **1/4** · pruebas acumuladas: 265

| Cartera | Sharpe | B | C | ×2 costes | CAGR | USDT/mes sobre 1.000 | caída | CVaR95 día | Calmar | p Holm | DSR | Puertas | Aprob. |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| (ref) N Núcleo v1 | 1.03 | 1.10 | 0.93 | — | +18.2% | +14.0 | 25% | 1.99% | 0.74 | — | — | — | — |
| (ref) F06 carry solo | 7.03 | 7.53 | 7.43 | — | +10.9% | +8.7 | 3% | 0.13% | 4.04 | — | — | — | — |
| (ref) 50/50 núcleo+carry (papel actual) | 1.50 | 1.64 | 1.28 | — | +14.8% | +11.5 | 11% | 1.06% | 1.35 | — | — | — | — |
| K1 Paridad de riesgo núcleo+carry | 2.47 | 2.44 | 5.86 | 2.03 | +11.0% | +8.7 | 9% | 0.41% | 1.22 | 0.136 | 1.00 | 4/5 | — |
| K2 HRP de los 10 bolsillos | 2.70 | 2.73 | 7.36 | 2.15 | +10.9% | +8.7 | 5% | 0.35% | 2.24 | 0.136 | 1.00 | 4/5 | — |
| K3 50/50 núcleo+carry + control de caída | 1.31 | 1.46 | 1.09 | 1.00 | +9.0% | +7.2 | 8% | 0.76% | 1.15 | 0.095 | 0.71 | 4/5 | — |
| K4 HRP 10 bolsillos + control de caída | 4.48 | 4.79 | 4.78 | 2.39 | +6.7% | +5.4 | 2% | 0.13% | 4.06 | 0.000 | 1.00 | 5/5 | ✔ |

Por año (retorno):

| Cartera | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| N Núcleo v1 | +66% | +5% | -15% | +42% | +43% | -5% | +9% |
| F06 carry solo | +17% | +34% | +1% | +7% | +12% | +5% | +0% |
| 50/50 núcleo+carry (papel actual) | +39% | +19% | -7% | +24% | +27% | +0% | +4% |
| K1 Paridad de riesgo núcleo+carry | +18% | +32% | -0% | +9% | +14% | +4% | +1% |
| K2 HRP de los 10 bolsillos | +18% | +34% | +1% | +7% | +12% | +5% | +0% |
| K3 50/50 núcleo+carry + control de caída | +19% | +15% | -5% | +13% | +20% | -1% | +2% |
| K4 HRP 10 bolsillos + control de caída | +5% | +28% | -0% | +4% | +9% | +1% | -0% |

Pesos HRP actuales: F06 99%, F01 1%, F02 0%, N 0%, F03 0%, F07 0%
Pesos HRP medios: F06 92%, F01 3%, N 3%, F03 1%, F02 0%, F04 0%, F07 0%, F05 0%, F08 0%, F09 0%
Días con exposición reducida por el control de caída: K3 94%, K4 59%
PBO: familia_K_mas_nucleo (CSCV s=16) = 0.34; fondos_F01-F09_sin_carry (CSCV s=16, diagnóstico) = 0.76

USDT/mes = equivalente mensual compuesto del CAGR sobre 1.000 USDT (USDT, no euros). Periodos: B 2020-01→2023-12 · C 2024-01→hoy.
