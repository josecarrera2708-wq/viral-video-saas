# Prueba de anchura del stop (mesas de 15 min y de 1 h) · Prerregistro — antes de ejecutar

Pregunta del dueño: ¿el stop está demasiado ajustado? Se prueba multiplicar por m ∈ {1,0 (actual), 1,5, 2,0} el stop de cada señal de los 13 traders BASE (`src/desk15/stops.py`); el TP en R se escala con el stop y el riesgo por operación sigue siendo 0,5 % (posición menor con stop mayor).
- **Decide la VALIDACIÓN** (2024-07→2025-10): un m «gana» si la media de las 13 R medias supera a ×1,0 y mejora en ≥ 9/13 traders. El examen (2025-10→2026-09-29) solo CONFIRMA; en la mesa de 15 min ya se vio una vez, así que aquí es una segunda mirada y no puede certificar nada.
- **Nada cambia** en las mesas en marcha. Si un m gana y se confirma, se abre una variante paralela en papel (prerregistro nuevo) y la adopción exige datos hacia delante + aprobación del dueño.
