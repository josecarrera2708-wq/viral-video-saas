# Fase 2 · lote 2 · Entrada maker (orden límite) · Prerregistro v1 — antes de ejecutar sobre datos reales

Fecha 2026-10-03. Motivo: en las mesas de 15 min, 1 h e intradía el coste (≈ 0,2–0,3 R por operación) se come el margen. Las mesas de
mercado (market makers) cobran la horquilla en vez de pagarla. Pregunta: ¿entrar con orden límite convierte alguna trader en positiva?
Nada en marcha se toca: `src/maker/engine.py` es una COPIA del motor con la entrada cambiada; `src/backtest/engine.py` sigue intacto (test).

## Regla (única diferencia con el motor)
Orden límite al precio de cierre de la vela de la señal, válida UNA vela. Se llena solo si el precio la cruza 1 pb (misma regla de cola que el
TP), al precio límite (o mejor si la vela abre más allá); comisión maker 0,02 %, sin deslizamiento. Sin llenado → la señal se pierde.
En la vela del llenado no cuenta el TP (pudo tocarse antes); el stop sí (conservador). Stops y salidas por tiempo siguen a mercado (taker).
Tamaño idéntico al motor original. Selección adversa incluida: si el precio se escapa a favor, no se entra.

## Universo (40 pruebas nuevas: n.º 270–309)
Las 40 traders BASE: intradía I01–I14 (Binance 1 h, periodos de su prerregistro) y las 13 de la mesa de 15 min y las 13 de la mesa de 1 h
(Deribit congelado en paper_state/mesa15/hist.parquet, periodos de la mesa de 15 min). Aprendices A/C no entran.
Aviso honesto: los exámenes ya se abrieron una vez (segunda mirada); por eso se exige validación Y examen, Holm sobre las 40 y costes ×2.

## Contraste (`src/maker/evaluar.py`, ejecución única)
M1 R media > 0 en validación y examen · M2 p unilateral de la R del examen con Holm (40) < 0,10 · M3 R > 0 con costes ×2 ·
M4 ≥ 0,3 operaciones/día en el examen · M5 sin liquidación y caída < 40 %. **Certificada = M1–M5.**
Diagnóstico: tasa de llenado, ΔR maker − taker por periodo, cuántas traders pasan a R > 0.

## Después
Una certificada iría a papel como variante «· M» de su mesa (sin tocar la original). Si ninguna certifica pero el maker mejora R en la mayoría,
se anota como mejora de ejecución candidata para la sombra. **Dinero real: nada** sin ≥ 90 días en papel y aprobación EXPRESA del dueño.
