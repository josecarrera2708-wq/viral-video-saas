# Búsqueda v6 · más combinaciones de patrones (prerregistro, 2026-10-05)

Petición del dueño: «sigue buscando más combinaciones de patrones». Este documento y el código (`src/busqueda/v6.py`, `src/busqueda/evaluate_v6.py`)
se registran en git ANTES de ejecutar. Pruebas nº 1686-1797 (112 variantes). La mesa de trading en marcha no se toca.

## Qué se combina
- **Grupos** (los patrones que ganaron en v4/v5):
  - Doble suelo y triple suelo/techo, en 1 h y 4 h.
  - Bandera/banderín, en 1 h y 4 h.
  - Cuatro velas seguidas, en 4 h.
- **Combinaciones nuevas:**
  - P1 tendencia superior + volumen de ruptura.
  - P2 tendencia + barrido de liquidez.
  - P3 tendencia + volatilidad comprimida.
  - P4 volumen + compresión.
  - P5 barrido + volumen.
  - P6 funding a contrapié: largo solo si el funding de las últimas 24 h está por debajo de su mediana de 30 días; corto, por encima.
  - P7 tendencia + funding.
  - P8 vela de ruptura fuerte: cierra en el 25 % extremo del rango y a favor.
  - P9 entrada en el RETESTEO: tras la ruptura, se espera ≤10 velas a que el precio vuelva a la línea de cuello y cierre del lado bueno. Se anula si antes cierra más allá del extremo del patrón.
- P2 y P5 solo se aplican a los giros. P9 no se aplica a las velas seguidas.
- **Salidas:** TP 3R y dejar correr.
- **Definiciones:** tendencia, volumen, compresión y barrido como en la v5. Patrones idénticos a la v4/v5.

## Evaluación
Idéntica a v2-v5: mismos periodos, motor, costes y elegibilidad (≥30 ops en validación). Puertas G1-G5 con DSR n_trials = 112.

## Mesa de trading (regla fijada ANTES de ver resultados)
- Por cada grupo y temporalidad, entra la mejor variante elegible (t de validación) que además GANE en el examen.
- Como mucho 4 traders nuevos, los de mayor t de validación. Códigos W01…, con apodo de pintor.
- Empiezan a las 00:00 UTC siguientes al commit de los resultados.
- Los traders actuales no cambian.
