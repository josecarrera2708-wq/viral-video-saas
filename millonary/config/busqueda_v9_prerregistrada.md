# Búsqueda v9 · alto acierto (prerregistro, 2026-10-06)

Petición del dueño: «quiero que ganemos entre el 70 y el 80 % de las operaciones o más». Este documento y el código (`src/busqueda/v9.py`,
`src/busqueda/evaluate_v9.py`) se registran en git ANTES de ejecutar. Pruebas nº 1923-2012 (90 variantes). La mesa de trading en marcha no se toca.

## Idea
El acierto sube si el objetivo está cerca y el stop lejos. El riesgo es que cada ganancia sea pequeña y una pérdida se coma varias.
Por eso se exige a la vez acierto ≥70 % Y ganancia neta (R>0) después de costes.

## Qué se prueba
- **Grupos:** doble suelo, triple suelo/techo y bandera en 1 h; bandera en 4 h. Patrones idénticos a v6-v8.
- **Confirmaciones:** A0 ninguna · A1 triple confirmación (tendencia + volumen + funding) · A2 horario de Wall Street + RSI no extremo ·
  A3 patrón dentro de patrón (solo 1 h).
- **Salidas:** objetivo a 0,5 R, 0,75 R o 1 R; stop del patrón ×1 o ×1,5. Sin salida por tendencia; tiempo máximo 72 velas (1 h) o 42 (4 h).

## Evaluación y mesa
- Periodos, motor, costes y puertas G1-G5 idénticos a v2-v8; DSR con n_trials = 90.
- **Elegible:** R>0 en construcción y validación, ≥30 ops en validación y **acierto ≥70 % en construcción y en validación**.
- **Mesa:** entra la mejor elegible por grupo que además gane en el examen con **acierto ≥70 %**; como mucho 2. Códigos S01, S02.
  Empiezan a las 00:00 UTC siguientes al commit de los resultados.
- Si ninguna cumple, no entra nadie y se dice.
