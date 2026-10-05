# Búsqueda v5 · patrones ligados a una confirmación + consolidación de mesas (prerregistro, 2026-10-05)

Petición del dueño: «sigue buscando patrones; si doble y triple techo funcionan, lígalos con otra cosa y vemos qué tal va. No quiero muchas mesas:
quiero eliminar las que no rinden». Este documento y el código (`src/busqueda/v5.py`, `src/busqueda/evaluate_v5.py`) se registran en git ANTES de
ejecutar. Pruebas nº 1518-1685 (168 variantes). El modelo fondo de inversión no se toca: núcleo, carry, fondos, K4, primas y acumulación.

## Qué se liga (confluencia clásica de los traders de patrones)
- **Patrones** (los que dieron señal en la v4):
  - Doble suelo y doble techo.
  - Triple suelo/techo.
  - Bandera/banderín.
  - Nuevo: cuña descendente/ascendente (Bulkowski).
- **Confirmación, condición Y en la vela de ruptura:**

| Código | Confirmación | Patrones |
|---|---|---|
| K0 | ninguna (control, idéntico a la v4; lo comprueba el código) | todos |
| K1 | divergencia RSI(14) entre el primer y el último extremo | solo giros |
| K2 | volumen de ruptura ≥1,5× la media de 20 | todos |
| K3 | tendencia de temporalidad superior: cierre al lado correcto de la EMA de 50 días | todos |
| K4 | barrido de liquidez: el último extremo supera al anterior («spring/upthrust») | solo giros |
| K5 | la ruptura deja una ineficiencia (FVG) | todos |
| K6 | volatilidad comprimida antes de la ruptura (ATR14 < 0,9 × ATR100) | todos |

- **Cuña:** solo K0 y K3.
- **Temporalidades:** 1 h y 4 h. **Salidas:** TP 2R, TP 3R y dejar correr (las mejores de la v4).
- **Total:** 168 variantes.

## Evaluación
Idéntica a v2-v4: mismos periodos, motor, costes, elegibilidad (≥30 ops en validación) y puertas G1-G5. DSR con n_trials = 168.

## Consolidación de mesas (decisión del dueño, 2026-10-05) — UNA sola mesa de trading activa
1. **Se detienen** la mesa intradía I01-I14, la mesa de 15 min y la mesa de 1 h. En papel desde el 29-09 o el 02-10 suman −6,6 R, −30,5 R y −15,3 R, y ya perdían en su histórico. Sus archivos quedan congelados como registro y la rutina deja de ejecutarlas.
2. **Mesa de patrones = la única mesa de trading activa.** Empieza el 2026-10-06 00:00 UTC y se queda con los traders que GANARON en el examen 2025-07 → 2026-09 (fuera de muestra):
   - De la v4: Y01 doble suelo, Y02 triple suelo/techo, Y04 bandera y Y07 FVG diario. Fuera Y03, Y05 y Y06, que perdieron en el examen.
   - De la mesa nueva (que no llega a arrancar): X07 conjunto CTA 4 h y X08 MAX 20 días. Fuera X01-X06 y X09, que perdieron en el examen.
   - De la v5: por cada patrón, la mejor variante elegible CON confirmación (K1-K6), por t de validación, solo si además gana en el examen. Códigos Z01…
3. Las reglas de cada trader no cambian. Los que no rindan en papel se retiran en la revisión de los 90 días.
