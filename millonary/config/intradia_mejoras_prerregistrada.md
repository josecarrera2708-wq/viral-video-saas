# Mesa intradía · Ciclo de mejora (prerregistro v1) — fijado ANTES de ejecutar

Motivo: el examen mostró expectativa negativa en los 14 traders por un problema estructural de costes (≈12 pb de ida y vuelta ≈ 0,2 R con stops de 1-2 ATR de 1 h).
El examen sellado (2025-07→2026-08) ya se consumió: estas candidatas se evalúan SOLO con construcción (2020-23) y validación (2024-25.06). Nada del examen se usa.

## Candidatas: 5 operadores × 14 traders = 70 pruebas (se suman al registro; total previo 142)
M1 filtro de tendencia: solo entradas a favor del signo de (cierre − EMA 800 h) · M2 stops ×2 (mismo TP en R: objetivos más lejanos, menos operaciones por unidad de R) ·
M3 solo sesión 07:00-21:00 UTC · M4 stop mínimo: se descartan entradas con stop < 0,8 % del precio (el coste pesa ≤ 0,15 R) ·
M5 dejar correr: TP ×1,5 y salida por tiempo ×2.

## Etapas
E1 construcción: R media de la variante ≥ R base + 0,05 · E2 validación: R media variante > R base Y R media variante > 0 (rentable tras costes)
→ pasa a SOMBRA hacia delante (papel, Deribit). Se informa el p unilateral (t-test de R) con Holm sobre las 70 como dato, no como puerta.
E3 hacia delante: ≥ 150 operaciones cerradas de la variante, R media > R base y probabilidad posterior P(E[R] > 0) ≥ 0,90 → candidata a Fase 2 (aprobación expresa del dueño, tamaño mínimo).
E4 retirada: con ≥ 150 operaciones y R media ≤ 0.
