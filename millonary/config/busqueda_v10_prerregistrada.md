# Búsqueda v10 · confluencia de patrones (prerregistro, 2026-10-06)

Petición del dueño: «sigue buscando más combinaciones de patrones; quiero que mi capital gane un 30 % mensual o más». Este documento y el código
(`src/busqueda/v10.py`, `src/busqueda/evaluate_v10.py`) se registran en git ANTES de ejecutar. Pruebas nº 2013-2044 (32 variantes).
La mesa de trading en marcha no se toca.

## Qué se combina
- **Grupos:** doble suelo, triple suelo/techo y bandera en 1 h; bandera en 4 h. Patrones idénticos a v6-v9.
- **Confluencia:** el patrón solo cuenta si OTRO patrón distinto (de esos tres) dio señal en la misma dirección en las 24 h anteriores.
- **Combinaciones:** B1 confluencia sola · B2 + tendencia (EMA 50 días) · B3 + funding a contrapié · B4 + compresión de volatilidad.
- **Salidas:** TP 3R y dejar correr (EMA50).
- Antes de registrar solo se contaron cuántas señales hay (sin mirar resultados): la bandera en 4 h casi no tiene confluencias (2-9 en seis años).

## Evaluación y mesa
- Evaluación idéntica a v2-v8; DSR con n_trials = 32.
- Mesa: mejor elegible por grupo que además gane en el examen; como mucho 3. Códigos R01… Empiezan a las 00:00 UTC siguientes al commit de los resultados.

## Medición del 30 % mensual (aparte, no cambia reglas)
`src/busqueda/objetivo_mensual.py` → `reports/objetivo_mensual.md`: rentabilidad mensual y caída de la mesa actual según el riesgo por operación.
