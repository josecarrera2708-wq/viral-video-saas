# Búsqueda v13 · swing de 1 a 3 días con filtro estadístico (prerregistro, 2026-10-07)

Petición del dueño tras v12: «sí, prepara la v13 swing de 1 a 3 días». Motivo: en v12, con operaciones de ≤4 h, las comisiones costaban
~0,2-0,35 R por operación. Con stops de swing (≥2 %), el coste baja a ≤0,07 R. Se registran en git ANTES de ejecutar este documento,
`src/busqueda/v13.py`, `evaluate_v13.py` y `tests/test_busqueda_v13.py`. Pruebas nº 2087-2098 (3 configuraciones × 4 modelos).
Lo que está en marcha (mesa de patrones, S01, fondos, carry) no se toca.

## Igual que v12 (`config/busqueda_v12_prerregistrada.md`)
Modelo (media de logística, boosting y bosque calibrados; mismas variables), filtro EV ≥ +0,05 R, Kelly/4 entre 0,25 % y 1 %,
≤2 posiciones, riesgo abierto ≤2 %, nunca opuestas, walk-forward trimestral 2022-10 → 2026-09 con purga, pre-muestra 2017-10 → 2019-12
con el gemelo, papel secuencial (150/300/450 operaciones) y nunca dinero real sin ≥90 días de papel con éxito y la aprobación EXPRESA del dueño.

## Cambios de v13
- **Señales:** mesa de 1 h (14 setups), patrones v7 (doble suelo, triple suelo/techo, bandera) en 1 h **y 4 h**, setups v11 (S1-S6).
  Sin la mesa de 15 min. Racimos de **4 h** (misma dirección = un evento; opuestas = fuera).
- **Barreras:** stop s = máx(**2 %**; **2·ATR14 de 4 h**), si s > 8 % no se opera; objetivo 2R / 3R; **barrera de tiempo 72 h**.
  Configuraciones: C1 2R, C2 3R, C3 2R + protección (promediar una vez en −1R, stop común −2R, objetivo precio medio + 0,1R).
- **Apalancamiento (tope):** 3x para señales de ≤2 h, 2x para 4 h. El efectivo sale de riesgo / stop (con 1 % y stop 3 %, 0,33x).
- **Puertas (media de los 3 modelos), todas:** G0 técnico (barajado AUC ≤ 0,52 y sin mejora > 0,02 R); G1 n ≥ **400**, t ≥ 3,0 por día y
  E[R] > 0 sin 2025-07 →; G2 mejor que tomar todas (p < 0,10) y acierto ≥ empate + 3 puntos; G3 ≥ 10/16 trimestres positivos;
  G4 R > 0 a costes ×2; G5 DSR ≥ 0,95 con N = 300 + 24; G6 ≥ **100** operaciones al año y Sharpe < 5.
  (n y ops/año más bajos que v12 porque el swing opera menos: ≈ 3.400 eventos en desarrollo, ≈ 2.250 fuera de muestra.)
- Decisión, congelado (`models/v13/`), pre-muestra y papel (trader W01) como en v12. Si ninguna pasa: no hay papel y no se rescata nada.
