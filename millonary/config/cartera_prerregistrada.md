# Gestor de cartera (Fase 1) · Prerregistro v1 — antes de ejecutar nada sobre datos reales

Fecha 2026-10-02. Petición del dueño: «una página completa, que gane por todos lados, así una cosa compensa la otra». Fase 1 = cómo se
REPARTE el capital entre lo que ya existe (no estrategias nuevas). Sistema aparte (`src/cartera/`); núcleo v1, carry, mesas y fondos no se tocan.
Código fijo en este commit: `src/cartera/gestor.py` (pesos, control de caída, medidas, CPCV) y `src/cartera/evaluar.py` (contraste).
Parámetros elegidos a priori (valores redondos, no mirando datos). Cambiar algo tras ejecutar = prueba nueva en el registro.

## Bolsillos (retornos diarios netos, ya calculados por sus módulos sin cambios)
N = núcleo v1 (`run_core`, mismos datos que la mesa de fondos) · F01–F09 de la mesa de fondos (F06 = carry de funding). F10 no entra (ya es una cartera).

## Carteras (4 pruebas nuevas: n.º 262–265)
| # | Cartera | Regla |
|---|---|---|
| K1 | Paridad de riesgo N + carry | peso ∝ 1/σ (180 d) |
| K2 | HRP de los 10 bolsillos | Hierarchical Risk Parity (López de Prado 2016): enlace simple sobre √(½(1−ρ)), bisección con varianza de grupo (180 d) |
| K3 | 50/50 en capital N + carry + control de caída | lo que corre hoy en papel (2 × 1.000) con el control de caída |
| K4 | K2 + control de caída | |

Comunes: pesos de capital decididos al cierre de cada fin de mes, aplicados desde el día siguiente; suma 1, sin apalancamiento; un bolsillo entra
cuando tiene ≥ 90 días con actividad en la ventana; coste 15 pb por unidad de capital movida (×cm).
Control de caída (Grossman-Zhou 1993, por escalones): m = máx(0,25; ⌊(1 − DD/20 %)/0,25⌋·0,25) con DD = caída de la cartera sin control,
decidido al cierre de t−1; lo no usado queda en USDT sin rendimiento; coste 15 pb × |Δm|.

## Periodo y contraste (ejecución única)
Evaluación 2020-01-01 → último día cerrado (el carry necesita el perpetuo). Subperiodos B 2020-01→2023-12, C 2024-01→hoy.
G1 Sharpe > núcleo con p (bootstrap estacionario por bloques de 20 d, 2.000 réplicas, Ledoit-Wolf) con Holm sobre las 4 < 0,10 ·
G2 Sharpe > núcleo en B y en C · G3 caída máxima ≤ la del núcleo · G4 Sharpe > 0 con costes ×2 (bolsillos y reajustes) ·
G5 Deflated Sharpe ≥ 0,80 con n = 265 y varianza nula 1/T. **Aprobada para papel = G1–G5.**
Informativo (no decide): CAGR, USDT/mes sobre 1.000, CVaR 95 % diario, Calmar, años, pesos HRP, días con control activo,
PBO (CSCV, 16 bloques) de la familia {N, K1–K4} y PBO diagnóstico de F01–F09 sin el carry.

## Filtro de admisión para la Fase 2 (estrategias nuevas)
Toda estrategia nueva que tenga parámetros elegidos con datos deberá pasar, además de las puertas de su prerregistro: PBO (CSCV) ≤ 0,5 en su
familia de variantes y Sharpe fuera de muestra > 0 en ≥ 75 % de los caminos CPCV (6 grupos, 2 de prueba, embargo 5 d; `gestor.cpcv_splits`).
Solo después entra como bolsillo del gestor.

## Aviso honesto
El carry tiene un Sharpe histórico ~7 con volatilidad ~1,5 %: cualquier regla por riesgo le dará casi todo el peso, así que estas carteras
ganarán en Sharpe y caída pero probablemente ganen MENOS en rentabilidad que el núcleo solo. Eso no se corrige con apalancamiento aquí.
**Dinero real: nada.** Solo con ≥ 90 días en papel y aprobación EXPRESA del dueño.
