# Ciclo de mejora continua (Laboratorio) · Prerregistro v1 — fijado ANTES de ejecutar

Fecha: 2026-09-29. Objetivo del dueño: que las estrategias se perfeccionen cada vez más, sin autoengaño.

## Candidatas de mejora: 5 operadores × 15 traders = 75 pruebas (se suman al registro; total previo 53)
O1 filtro EMA200 (solo largos sobre la EMA200, solo cortos bajo ella) · O2 solo largos · O3 tamaño según volatilidad
(pos × clip(0,25/σ_anual EWMA 45 d, 0,25, 2)) · O4 stop chandelier 3×ATR14 desde el extremo (vuelve a entrar solo con una señal nueva) ·
O5 «parte fuerte del canal» (largos solo en el tercio alto del rango de 20 velas, cortos solo en el bajo).
Añadir un operador nuevo = prueba nueva, con su propia línea en el registro; nunca se retoca uno existente.

## Etapas (una candidata solo avanza si supera la anterior)
E1 Construcción (train 2020-2023): mejora del Sharpe ≥ +0,15 frente al trader base.
E2 Validación (examen 2024-01→2025-06, SEGUNDA mirada al examen, anotada): mejora del Sharpe > 0. → pasa a SOMBRA hacia delante.
   Se informa también el p bootstrap (bloques) con Holm sobre las 75 (informativo, no puerta).
E3 Sombra hacia delante desde 2026-09-29: se mide cada semana.
E4 Adopción (solo en sombra; jamás toca capital): ≥ 90 días hacia delante, mejora del Sharpe ≥ +0,3, caída ≤ 1,2× la base y
   p (bloques) < 0,10 con Holm sobre las candidatas en sombra. Adoptada = candidata a Fase 2; el dinero real exige aprobación del dueño.
E5 Retirada: tras 90 días, si la mejora hacia delante ≤ 0, se retira y se anota.
