# Búsqueda v11 · intradía 2R/3R con entrada de protección (prerregistro, 2026-10-07)

Petición del dueño: estrategias de 15 min a 3-4 h con objetivo 2:1 o 3:1, buscadas por un equipo de agentes, más la «entrada de protección»
(si va en contra, meter otra entrada una sola vez). Este documento, el código (`src/busqueda/v11.py`, `evaluate_v11.py`, `sim5.py`,
`intradia5.py`) y las pruebas se registran en git ANTES de ejecutar. Pruebas nº 2045-2074 (30 variantes). La mesa en marcha no se toca.

## Investigación previa
Cinco agentes (informes en `docs/investigacion_v11/`): cazador académico, cazador de traders, cazador de flujo, metodólogo y protector.
Conclusiones que fijan este diseño:
- Con 2R y nuestros costes, el acierto de empate es 36-46 % según el stop; ganar más operaciones de las que se pierden con 2R no tiene respaldo publicado.
- La «entrada de protección» no cambia la esperanza: sube el acierto y agranda la pérdida rara. Se prueba igualmente, con controles justos.
- El examen 2025-07→2026-09 está muy usado: se informa, pero no basta. Se añade una **pre-muestra limpia 2017-10→2019-12** (contado, nunca usada en intradía).
- Corrección de datos: las métricas de Binance (OI) cambiaron de convención el 2024-03-04; se usan desde su sello + 10 min.

## Setups (parámetros de las fuentes; señal al cierre, ejecución en velas de 5 min)
- **S1 ORB 60 min de Nueva York + volumen relativo:** rango 09:30-10:30 NY (hora de NY con cambio de horario; días hábiles sin festivos
  federales de EE. UU.); volumen del rango ≥ media de los 14 días previos; solo en la dirección del rango; primer cierre de 5 min fuera del rango
  antes de las 12:00 NY; stop en el otro extremo.
- **S2 ORB 15 min:** igual con rango 09:30-09:45.
- **S3 Reversión tras salto ≥3σ en velas de 2 h:** σ de las 360 barras previas; a contrapié; stop 1σ; salida a las 2 h.
- **S4 Rebote tras cascada:** vela de 1 h ≤ −4σ (o ≥ +4σ), ΔOI de 60 min ≤ p5 de 30 días, volumen ≥ p95, flujo taker a favor del movimiento;
  a contrapié; stop clip((C−L)+0,25·ATR; 1-3 ATR).
- **S5 Squeeze:** media de 8 h de la prima ≤ p5 (≥ p95) de 90 días, ΔOI de 24 h ≥ p80, ruptura del máximo (mínimo) de 24 h; a favor.
- **S6 VWAP de Nueva York:** VWAP desde las 09:30 NY; entre 10:00 y 14:00, ≥6 cierres por debajo y cierre por encima con volumen ≥ media de 20
  → largo (corto simétrico); stop en el extremo del tramo ∓ 0,1·ATR; una por lado y día.
- Stop válido entre 0,35 % y 3 % del precio; si no, no se opera. Salida por tiempo 4 h (S3: 2 h). Una posición a la vez por variante.

## Gestiones (5) · todas a igual riesgo máximo (0,5 % del capital si salta todo)
- **2R** y **3R**: stop 1R, objetivo 2R / 3R.
- **C2 (control):** una sola entrada con stop al doble de distancia y objetivo en el mismo precio que 2R.
- **P3 protección «promediar una vez» (la regla del dueño):** sin stop en −1R; en −1R se añade otra entrada igual (orden límite);
  stop común en −2R; tras añadir, objetivo en el precio medio + 0,1R (recuperar la pérdida y los costes). Una sola vez.
- **P4 protección «girar una vez»:** en −1R se cierra y se abre la contraria del mismo tamaño, stop en la entrada original, objetivo 2R. Una sola vez.
- Dentro de una vela de 5 min, primero lo adverso. Costes: taker 0,05 %, maker 0,02 %, deslizamiento 2 pb.

## Evaluación y paso a papel
- Construcción 2020-03→2024-01, validación 2024-01→2025-07, examen 2025-07→2026-09; pre-muestra 2017-10→2019-12 (solo S1, S2, S3, S6).
- Elegible: R>0 en construcción y validación con ≥30 ops en validación. Puertas G1-G5 como en v2-v10 (DSR con n_trials = 30).
- **A papel** solo si: certificada 5/5, **o** elegible + R>0 en el examen + R>0 en la pre-muestra con ≥30 ops.
  Como mucho 2 (mejor t de validación, una por setup). Códigos S01, S02; empiezan a las 00:00 UTC siguientes al commit de los resultados.
- Se informa el acierto de cada variante y la comparación de gestiones (acierto y R media).
- El meta-etiquetado propuesto por el metodólogo (modelo que elige qué señales tomar) queda para una v12 con su propio prerregistro.
