# Búsqueda v8 · combinaciones de las mejores confirmaciones (prerregistro, 2026-10-06)

Petición del dueño: «sigue buscando combinaciones de patrones; busco más de un 30 % mensual». Este documento y el código (`src/busqueda/v8.py`,
`src/busqueda/evaluate_v8.py`) se registran en git ANTES de ejecutar. Pruebas nº 1879-1922 (44 variantes). La mesa de trading en marcha no se toca.

## Qué se combina
- **Grupos:** doble suelo, triple suelo/techo y bandera en 1 h; bandera en 4 h. Patrones y filtros idénticos a v6/v7.
- **Combinaciones:**
  - R1 patrón dentro de patrón + funding a contrapié.
  - R2 patrón dentro de patrón + volumen.
  - R3 horario de Wall Street + RSI no extremo.
  - R4 tendencia + compresión + volumen.
  - R5 triple confirmación + RSI no extremo.
  - R6 horario de Wall Street + funding.
- R1 y R2 solo se aplican en 1 h.
- **Salidas:** TP 3R y dejar correr (EMA50).

## Evaluación y mesa
- Evaluación idéntica a v2-v7, con DSR n_trials = 44.
- Regla de la mesa: igual que en la v7. Entra la mejor variante elegible por grupo que además gane en el examen; como mucho 3. Códigos T01…
- Empiezan a las 00:00 UTC siguientes al commit de los resultados.

## Nota sobre el objetivo del 30 % mensual
Se mide aparte, sin tocar ninguna regla: qué rentabilidad mensual y qué caída da la mesa actual con riesgos por operación de 0,5 %, 1 %, 2 % y 3 %, usando sus operaciones del examen.
