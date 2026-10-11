# Búsqueda v7 · más combinaciones de patrones (prerregistro, 2026-10-06)

Petición del dueño: «sigue buscando más combinaciones de patrones». Este documento y el código (`src/busqueda/v7.py`, `src/busqueda/evaluate_v7.py`)
se registran en git ANTES de ejecutar. Pruebas nº 1798-1878 (81 variantes). La mesa de trading en marcha no se toca.

## Qué se combina
- **Grupos:** doble suelo, triple suelo/techo y bandera/banderín, en 1 h y 4 h. Patrones idénticos a v4-v6.
- **Combinaciones nuevas:**
  - Q1 tendencia superior + volumen de ruptura + funding a contrapié (triple confirmación).
  - Q2 funding a contrapié + volumen.
  - Q3 «patrón dentro de patrón», solo en 1 h: en las últimas 24 h se cerró en 4 h un doble suelo, triple o bandera en la MISMA dirección.
  - Q4 ruptura en horario de Wall Street: vela cerrada entre las 13 y las 21 UTC en 1 h; velas de 12 y 16 UTC en 4 h.
  - Q5 RSI(14) no extremo: <70 en largos, >30 en cortos, para no comprar tarde.
- **Salidas:**
  - TP 3R.
  - Dejar correr: cierre al otro lado de la EMA50.
  - Dejar correr rápido (NUEVA): cierre al otro lado de la EMA20.
- **Total:** 81 variantes.

## Evaluación
Idéntica a v2-v6: mismos periodos, motor, costes y elegibilidad. Puertas G1-G5 con DSR n_trials = 81. El total acumulado del proyecto (1.878) se informa aparte.

## Mesa de trading (regla fijada ANTES de ver resultados)
- Por cada grupo y temporalidad, entra la mejor variante elegible (t de validación) que además GANE en el examen.
- Como mucho 3 traders nuevos, los de mayor t de validación. Códigos U01…, con apodo de pintor.
- Empiezan a las 00:00 UTC siguientes al commit de los resultados.
- Los traders actuales no cambian.
