# Búsqueda v12 · filtro estadístico de entradas (prerregistro, 2026-10-07)

Petición del dueño: «no se puede entrar en todo lo que se vea; hay que filtrar las entradas por estadística antes de entrar», e incluir el
apalancamiento según la temporalidad de la entrada. Diseño: meta-etiquetado según el protocolo del metodólogo
(`docs/investigacion_v11/metodologo.md`, §1-§4 y §8), con las simplificaciones indicadas abajo. Este documento, el código
(`src/busqueda/v12.py`, `evaluate_v12.py`) y las pruebas (`tests/test_busqueda_v12.py`) se registran en git ANTES de ejecutar.
Pruebas nº 2075-2086 (3 configuraciones × 4 modelos). La mesa en marcha y S01 no se tocan.

## Eventos (señales primarias, sin elegirlas por resultados)
- Todas las señales ya programadas: mesa intradía de 1 h (14 setups, `intraday/setups.py`), mesa de 15 min (13, `desk15/setups.py`),
  patrones de 1 h de v7 (doble suelo, triple suelo/techo, bandera) y los 6 setups de v11 (S1-S6). Señal al cierre de su vela.
- Racimos: señales a menos de 60 min de la primera del racimo forman un evento; si el racimo tiene direcciones opuestas, se descarta.
  El evento usa la hora, la temporalidad y el setup de la PRIMERA señal; nº de setups simultáneos y origen como variables.
- Desarrollo D: 2020-10-01 → 2026-09-28 (≈16.000 eventos).

## Etiqueta (barreras iguales para todos)
- Entrada a mercado en la apertura de la vela de 5 min siguiente. Stop s = máx(0,50 %; 0,75·ATR14 de 1 h); si s > 3 %, no se opera.
- Barrera de tiempo 4 h. Simulador `sim5` (5 min, primero lo adverso, costes taker 0,05 %, maker 0,02 %, deslizamiento 2 pb, funding).
- Etiqueta = R neta > 0. Cada evento se simula aislado.

## Configuraciones (3)
- **C1 2R:** objetivo 2R.  **C2 3R:** objetivo 3R.
- **C3 2R + protección:** la regla del dueño (promediar una vez en −1R, stop común en −2R, objetivo precio medio + 0,1R).

## Modelo (lista cerrada de variables; todo hasta el cierre de la señal)
- Volatilidad (σ 1 h de 24 h, cociente 24 h/7 d, percentil del ATR), coste en R, stop en %, hora (seno/coseno), sesión UTC, fin de semana,
  minutos al funding, rendimientos de 1/4/24/168 h en σ, distancia a la EMA200 de 1 h y a la EMA50 de 4 h en ATR, flujo taker de 1 y 4 h (z),
  volumen frente a la misma hora de 20 días, ΔOI de 4 y 24 h, signo(rend. 4 h)·ΔOI, z de los ratios largo/corto, prima, funding (z),
  Fear & Greed del día anterior, huecos hasta el máx./mín. de 24 h y 7 d en unidades de s, posición en el rango de 24 h, lado,
  nº de setups, origen y temporalidad. Firmadas por el lado. Métricas de Binance desde su sello + 10 min.
- Media de 3 modelos calibrados (isotónica, 3 pliegues contiguos), con pesos 1/nº de etiquetas solapadas:
  logística L2 (C = 0,1), boosting (profundidad 3, tasa 0,05, ≤400 árboles con parada temprana, hoja ≥200, L2 = 1),
  bosque (300 árboles, profundidad 6, hoja ≥100, max_samples 0,5).
- **Filtro:** se opera solo si EV = p·(W̄ − c) − (1 − p)·(L̄ + c) ≥ +0,05 R (W̄, L̄ medias brutas del entrenamiento; c = coste en R).
- **Tamaño:** Kelly/4 encogido (p̃ = p̄ + 0,5·(p − p̄)), riesgo entre 0,25 % y 1 % del capital. ≤2 posiciones, riesgo abierto ≤2 %, nunca opuestas.
- **Apalancamiento por temporalidad (tope):** señal de 5-15 min ≤10x, 1 h ≤5x, 2 h o más ≤3x. El apalancamiento efectivo sale del riesgo y
  del stop (nocional = riesgo / stop); si superara el tope, se recorta el riesgo. Se informa el apalancamiento usado.

## Validación (fuera de muestra)
- Walk-forward anclado: reentreno cada trimestre con todo lo anterior desde 2020-10, purgando etiquetas que acaban dentro de la prueba;
  16 trimestres de prueba 2022-10 → 2026-09. Simplificación frente al metodólogo: sin CPCV, PBO ni SPA (se sustituyen por G2-G3).
- Referencia: «tomar todas» las señales con las mismas barreras.

## Puertas (sobre la media de los 3 modelos; todas)
| Puerta | Criterio |
|---|---|
| G0 | Técnico: con etiquetas barajadas por días (C1), AUC ≤ 0,52 y sin mejora > 0,02 R frente a tomar todas |
| G1 | n ≥ 600, t ≥ 3,0 agrupada por día, y E[R] > 0 también sin 2025-07 → 2026-09 |
| G2 | Mejor que tomar todas (bootstrap por semanas, p < 0,10) y acierto ≥ empate realizado + 3 puntos |
| G3 | ≥ 10 de 16 trimestres con E[R] > 0 |
| G4 | E[R] > 0 con costes ×2 |
| G5 | DSR ≥ 0,95 con N = 300 + 12 |
| G6 | ≥ 250 operaciones al año y Sharpe anual < 5 (si no, auditoría de fuga) |

## Decisión
- Pasa la configuración con mayor cota inferior al 95 % de E[R]. Se reentrena con todo D, se congela (pickle + sha256 en `models/v12/`) y se hace commit.
- **Pre-muestra 2017-10 → 2019-12 (contado, una sola vez):** gemelo sin OI/prima/funding/Fear & Greed ni setups S4/S5, entrenado en D.
  E[R] ≤ −0,05 → falsado (se para); E[R] > 0 con p < 0,05 → apoyo; otro → no concluyente (se sigue).
- **Papel:** si no queda falsado, trader V01 desde las 00:00 UTC siguientes al commit del modelo congelado, sin reentrenar.
  Hipótesis única E[R neta] > 0; miradas a 150, 300 y 450 operaciones: éxito z ≥ 3,0 (150, 300) o z ≥ 1,66 (450);
  futilidad z ≤ −0,87 (150) o z ≤ 0,5 (300); máximo 12 meses.
- Si ninguna pasa: no hay papel, se registran las 12 pruebas y no se rescata ninguna variante.
- Dinero real: nunca sin ≥ 90 días de papel con éxito y la aprobación EXPRESA del dueño.
