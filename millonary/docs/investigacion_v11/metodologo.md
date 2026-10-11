# Metodólogo · Método v11: estrategias intradía 2R-3R sin engañarnos

Las cifras propias salen de fórmulas o de simulaciones con datos SINTÉTICOS (scripts en `scratchpad/agentes/metodologo_sim/`). No hay backtests ni resultados con datos de BTC. Cada fuente lleva una etiqueta: [revisado], [documento de trabajo], [interés comercial] u [opinión].

## 0. Lo esencial
1. **Sin ventaja, 2R:1R acierta el 33,3 %.** Con nuestros costes, el empate está entre el 36 % y el 46 %, según el stop. Para ganar «más de las que se pierden» con 2R haría falta una ventaja que ningún sistema documentado tiene.
2. **El meta-etiquetado anterior falló por diseño.** Tenía 40 operaciones por modelo y umbral 0,5. Con 2R, el umbral correcto ronda 0,38.
3. **El examen 2025-07→2026-09 está quemado.** Pasa a desarrollo. El apartado limpio nuevo es la pre-muestra 2017-10→2019-12, más papel hacia delante con prueba secuencial.
4. **Demostrar +0,15 R por operación exige unas 540 operaciones.** Con 20-30, no se distingue +0,2 R de −0,3 R.
5. **La orden límite aporta poco (+0,01 a +0,04 R).** Las palancas reales son el stop más ancho que permita el límite de 4 h y hacer menos operaciones, pero mejores.
6. **Hacia delante se confirma una sola hipótesis.** Si falla, se para.

## 1. Meta-etiquetado con triple barrera

**Etiqueta, igual para todos los eventos:**
- Entrada en la apertura de la vela de 5 min que sigue a la señal (de 15 min o 1 h).
- Stop s = máx(0,50 %; 0,75·ATR14 de 1 h), ≈0,6 σ de 4 h.
- TP = b·s, con b ∈ {2, 3}; barrera de tiempo de 4 h.
- El recorrido se mira en velas de 5 min. Si stop y TP caen en la misma vela, cuenta el stop.
- Se guarda el R neto (comisiones, deslizamiento y funding); y = 1 si R neto > 0.

**Por qué falló `src/incubator/meta.py`:**
- **Umbral 0,5 (línea 66).** Con una tasa base de aciertos del 30-45 % y variables débiles, un modelo calibrado casi nunca supera 0,5, así que veta casi todo.
- **Muy pocos datos.** Con `MIN_TRAIN_OPS = 40`, un modelo por trader y 6 variables quedan ~2 positivos por variable. El mínimo es 10-20 (Peduzzi 1996; Riley 2020); el modelo era ruido.
- **`hour` lineal de 0 a 23.** La logística trata las 23 h y las 0 h como extremos opuestos.
- **Etiqueta ret>0 en seguidores de tendencia de 4 h.** El beneficio viene de pocas ganadoras grandes, y filtrar por probabilidad corta esa cola.
- **Sin potencia.** Un solo ajuste (2020-2023), sin reentrenar, juzgado por la diferencia de Sharpe diario.

**Prueba sintética** (`c_meta.py`: 40.000 señales, empate 0,381, media de 20 repeticiones):

| Método | Tomadas | Acierto | R/op | R por 1.000 señales |
|---|---|---|---|---|
| Sin filtro | 100 % | 0,352 | −0,09 | −90 |
| Oráculo (p real > empate) | 36 % | 0,462 | +0,25 | +91 |
| Logística + 0,5, entrenada con 40 ops | 24 % | 0,388 | +0,02 | +8 (ruido) |
| Logística + 0,5, entrenada con 4.000 ops | 6 % | 0,535 | +0,48 | +30 |
| Logística + umbral por esperanza, 4.000 ops | 30 % | 0,453 | +0,23 | +68 |
| Media de 3 modelos calibrados, por esperanza | 27 % | 0,466 | +0,26 | +71 |

El umbral 0,5 veta el 94 % y pierde más de la mitad del beneficio. Con 40 casos no se aprende nada.

**Modelos.** Un solo modelo agrupado por configuración, con todos los eventos de todos los setups. No se elige un ganador: se usa la media de tres probabilidades calibradas.
- **Logística L2:** C ∈ {0,03; 0,1; 0,3}, elegido por validación interna purgada.
- **`HistGradientBoosting`:** profundidad 3, tasa 0,05, ≤400 árboles con parada temprana, hoja ≥200, L2 = 1.
- **Bosque aleatorio:** 500 árboles, profundidad 6, hoja ≥100, `max_samples` = unicidad media.
- **Común a los tres:**
  - pesos por unicidad de etiquetas solapadas (López de Prado);
  - calibración isotónica fuera de pliegue (mejora el tamaño, según Meyer et al. 2023);
  - exigencia de Brier skill > 0.

**Variables (lista cerrada).** Solo datos hasta el cierre de la señal; las métricas de 5 min van retrasadas una vela.
- **Volatilidad:** σ de 1 h y de 24 h, y su cociente; percentil a 30 días del ATR de 1 h.
- **Coste:** coste en R = coste de ida y vuelta / s.
- **Tiempo:** seno y coseno de la hora; sesión UTC (0-7, 7-13, 13-21, 21-24); fin de semana; minutos al funding.
- **Tendencia (firmada por el lado):**
  - rendimiento de 1 h, 4 h, 24 h y 7 d, en σ;
  - distancia a la EMA200 de 1 h y a la EMA50 de 4 h, en ATR.
- **Flujo:** desequilibrio taker (taker_buy/volumen − 0,5) de 1 h y 4 h, en z; volumen frente a la misma hora de los últimos 20 días.
- **Posicionamiento:**
  - ΔOI de 4 h y 24 h, y signo(rendimiento de 4 h)·ΔOI;
  - funding liquidado (en z) y prima de la última hora;
  - z de los ratios largo/corto.
- **Niveles:**
  - «hueco» hasta el máximo/mínimo de 24 h y de 7 d, en unidades de s (si es menor que b, el TP tiene que romperlo);
  - posición en el rango de 24 h.
- **Señal:** familias de setup que dispararon; nº de setups a favor y en contra en los últimos 60 min.
- **Régimen:** Fear & Greed del día anterior.

**Umbral por esperanza, en cada operación.** Se opera si EV = p̂·W_i − (1−p̂)·L_i ≥ +0,05 R.
- W_i = W̄ − c_w,i y L_i = L̄ + c_l,i, con W̄ y L̄ medias brutas del entrenamiento y c el coste de esa operación.
- Con W ≈ 1,92 y L ≈ 1,09, el umbral queda en p̂ ≥ 0,38.

**Tamaño: Kelly fraccional acotado.**
- p̃ = p̄ + 0,5·(p̂ − p̄); f* = p̃/L − (1−p̃)/W.
- Riesgo = 0,25·f*, acotado entre el 0,25 % y el 1 %.
- Ejemplos: p̃ = 0,38 → 0,64 %; p̃ = 0,40 → 1 %.
- Kelly completo (5-8 %) es inviable con una p estimada (MacLean, Thorp y Ziemba).
- Los contrastes se hacen en R con riesgo unitario; el tamaño solo afecta al capital y a la caída.

## 2. Validación y número de operaciones
- **Walk-forward anclado:**
  - entrena 2020-10→2022-09 y reajusta cada trimestre;
  - 16 trimestres de prueba (2022-10→2026-09);
  - purga de los eventos cuya etiqueta acaba dentro de la prueba.
- **CPCV:**
  - 10 grupos con 2 de prueba: 45 divisiones y 9 caminos fuera de muestra;
  - purga de 4 h y embargo de 21 días (≈1 % de la muestra).
- **Errores:** agrupados por día y bootstrap por bloques semanales, porque las operaciones simultáneas no son independientes.

**Operaciones necesarias** (una cola, α = 5 %, potencia del 80 %; σ_R ≈ 1,4 con 2R y 1,8 con 3R):

| Ventaja real | +0,10 R | +0,15 R | +0,20 R | +0,25 R | +0,30 R |
|---|---|---|---|---|---|
| 2R | 1.212 | 539 | 303 | 194 | 135 |
| 3R | 2.003 | 890 | 501 | 321 | 223 |

En acierto, con 2R y empate en 0,38:

| Acierto sobre el empate | +5 puntos | +8 puntos | +10 puntos |
|---|---|---|---|
| Operaciones necesarias | ~590 | ~230 | ~150 |

- Con 30 operaciones, el error estándar de la R media es de ±0,26 R. Las puertas actuales (≥20 o ≥30) no tienen potencia.
- Con Holm sobre 3 hipótesis, las cifras se multiplican por ~1,4.

## 3. Descubrimientos falsos y el examen quemado

| Herramienta | Uso en v11 |
|---|---|
| DSR | N efectivo de TODO el registro, no `len(rows)` |
| PBO/CSCV | Sobre las 16 estrategias v11; umbral 0,30 |
| SPA de Hansen + StepM de Romano-Wolf | ¿Alguna bate a «no operar» y a «tomar todas»? Mejor que la Reality Check de White: estudentiza y no se diluye. Bootstrap estacionario con bloque de 5 días (`arch`). |
| Holm | Lo confirmatorio |
| BH (q = 0,10) | Lo exploratorio (Benjamini-Yekutieli si hay dependencia) |
| t ≥ 3 | Lo minado (Harvey, Liu y Zhu) |

**Sharpe anual necesario para la DSR** (4 años de datos diarios):

| N pruebas | 1 | 16 | 100 | 300 | 2.044 |
|---|---|---|---|---|---|
| DSR ≥ 0,80 | 0,42 | 1,32 | 1,69 | 1,87 | 2,15 |
| DSR ≥ 0,95 | 0,82 | 1,72 | 2,09 | 2,27 | 2,55 |

- Con 1,5 operaciones al día, el Sharpe anual ≈ 16,7·E[R]. Por tanto, N = 300 y DSR ≥ 0,95 equivalen a E[R] ≥ 0,14 R.
- Las 2.044 pruebas son en gran parte duplicadas. El N efectivo se calcula agrupando sus series (ONC; López de Prado y Lewis 2019), con un mínimo de 300.

**El examen está quemado.** Las búsquedas v2 a v10 lo usaron para elegir: la regla «mejor elegible que GANE en el examen» está en `evaluate_v8.py` y `evaluate_v10.py`, líneas 43-49. Pasa a desarrollo y se informa aparte, sin puerta.

**Apartado limpio nuevo:**
- **A) Pre-muestra 2017-10-01→2019-12-31.**
  - Contado de 15 min y 1 h, sin los días 2018-02-08→11.
  - Nunca se ha usado en intradía: el núcleo y los fondos solo la usaron en 4 h y diario.
  - Se aplica una vez un gemelo con solo precio, volumen y flujo taker (no hay OI ni funding).
  - Con unas 800 operaciones, la potencia supera el 90 % para +0,15 R.
- **B) Papel hacia delante, secuencial.**
  - El modelo se congela (hash en git) antes de que existan los datos. Se puede calcular a diario con Binance Vision.
  - Miradas a las 150, 300 y 450 operaciones.
  - Éxito: z ≥ 3,0 en las dos primeras, o z ≥ 1,66 en la última.
  - Futilidad: z ≤ −0,87 a las 150, o z ≤ 0,5 a las 300.
  - Simulado: α = 4,6 %; potencia del 74 % para +0,15 R y del 92 % para +0,20 R; sin ventaja, se para hacia la operación 315.

## 4. Combinar sin duplicar
- **El problema de las copias.** 18 traders con correlación media de 0,5 equivalen a 18/(1+17·0,5) ≈ 1,9 apuestas independientes. Repetir la misma entrada solo multiplica el tamaño.
- **Familias.** Dos traders con un índice de Jaccard de entradas ≥ 0,5 (misma dirección, ±60 min) son una familia. Cada familia cuenta como una estrategia: una posición, un presupuesto de riesgo y una sola prueba en el N efectivo.
- **En v11, la coincidencia es información.**
  - Las entradas en la misma dirección dentro de 60 min forman un solo evento.
  - Si hay entradas opuestas en esos 60 min, se descartan.
  - El nº de setups que coinciden entra como variable.
  - El modelo agrupado ya es un apilado (stacking); votar «k de n» es un caso particular peor. No se añade otra capa.
- **Cartera:**
  - riesgo abierto ≤ 2 % y como mucho 2 posiciones;
  - nunca posiciones opuestas;
  - estrategias con correlación diaria > 0,5 comparten presupuesto (HRP o igual riesgo por familia), nunca repartido por el resultado reciente.

## 5. Costes y órdenes límite

**Coste de una perdedora y acierto de empate.** «Actual» = el motor de hoy (entrada a mercado y TP maker). «Límite» = cota optimista, sin selección adversa.

| Stop | Coste perdedora, actual / límite | Empate 2R | Empate 3R |
|---|---|---|---|
| 0,30 % | 0,47 / 0,30 R | 46,3 / 41,1 % | 35,2 / 31,2 % |
| 0,50 % | 0,28 / 0,18 R | 41,3 / 38,1 % | 31,2 / 28,8 % |
| 0,75 % | 0,19 / 0,12 R | 38,7 / 36,5 % | 29,2 / 27,5 % |
| 1,00 % | 0,14 / 0,09 R | 37,4 / 35,7 % | 28,1 / 26,9 % |
| 1,50 % | 0,09 / 0,06 R | 36,0 / 34,9 % | 27,1 / 26,3 % |

**El stop ancho choca con el límite de 4 h** (martingala sintética, volatilidad anual del 50 %, 2R):

| Stop | TP / stop / tiempo | E[R] sin ventaja, mercado / límite |
|---|---|---|
| 0,50 % | 28 / 60 / 12 % | −0,22 / −0,12 R |
| 0,75 % | 15 / 46 / 40 % | −0,16 / −0,09 R |
| 1,00 % | 5 / 33 / 62 % | −0,13 / −0,08 R |

Con un stop ancho, el sistema pasa a depender de la salida por tiempo: el acierto sube hacia el 50 %, pero ya no es 2R. Con 3R y el stop del §1, el TP solo llega en ≈7 % de las operaciones.

**Selección adversa** (sintético con pasos de 5 s, stop 0,6 %, 2R; R por SEÑAL):

| Entrada | Sin ventaja | Ventaja moderada | Ventaja fuerte |
|---|---|---|---|
| Mercado | −0,223 | +0,057 | +0,329 |
| Límite, «basta con tocar» | −0,149 | +0,110 | +0,356 |
| Límite atravesada 3 pb | −0,164 | +0,051 | +0,252 |
| Límite 5 min y luego mercado | −0,212 | +0,064 | +0,336 |

- **La límite pura pierde ganadoras.** Con ventaja fuerte se llena en el 75 % de las buenas y en el 79 % de las malas, y queda 0,08 R por debajo de la entrada a mercado.
- **Suponer que «tocar = llenar» infla ~0,05 R.**
- **La entrada híbrida gana unos 0,01 R.** La prueba maker del propio proyecto midió +0,04 R. No rescata nada.

**Simulación honesta con velas de 5 min:**
1. La límite se llena solo si la vela la ATRAVIESA en 3 pb. Sensibilidad con 0 y con 10 pb.
2. En la vela del llenado cuenta el stop, no el TP.
3. Si no se llena, la operación se pierde o se entra a mercado más 2 pb.
4. Se mide el llenado de ganadoras frente a perdedoras, tomando el resultado a mercado como contrafactual.
5. Deslizamiento del stop: máx(2 pb; 10 % del rango de la vela). El TP maker se llena con 1 pb atravesado (3 pb en estrés).

## 6. Cifras realistas

| Estudio | Cifras | Tipo |
|---|---|---|
| Momentum intradía en SPY (Zarattini, Aziz y Barbon 2024) | 19,6 % anual, Sharpe 1,33, neto (2007-2024) | Documento de trabajo [interés comercial] |
| ORB de 5 min en «stocks in play» | Sharpe 2,81; más del 1.600 % (2016-2023) | Ídem; sin historial real |
| Momentum intradía del mercado (Gao et al.) | R² fuera de muestra del 1,8 %; 6,3 % anual bruto | Revisado |
| ~15.000 reglas técnicas en cripto (Hudson y Urquhart 2021) | **Sin predictibilidad en Bitcoin fuera de muestra** | Revisado |
| Tendencia 1880-2016 (Hurst, Ooi y Pedersen) | Sharpe 0,76 tras comisiones 2/20 | Revisado (AQR) |
| Day traders de Brasil (Chague et al.) | El 97 % de los que persisten pierde | Revisado |
| Day traders de Taiwán (Barber et al. 2014) | Menos del 1 % gana de forma predecible | Revisado |
| 888 algoritmos de Quantopian | R² < 0,025 entre el Sharpe dentro y fuera de muestra | Documento de trabajo |
| «70 % de acierto con 3R», «30 % al mes» | Sin auditar | Marketing |

**Qué esperar:**
- Un intradía bueno y documentado tiene un Sharpe neto de 1 a 1,5. Por encima de 2,5 solo aparece en backtests comerciales; un Sharpe > 5 en los nuestros indica un error.
- Con 2R, un sistema bueno acierta el 40-45 % y saca de +0,1 a +0,25 R por operación.
- Con +0,15 R, 1,5 operaciones al día y un 0,5 % de riesgo, saldría ≈ +3,4 %/mes, con caídas del 10-15 %. El 30 % mensual no tiene respaldo.

## 7. Cambios concretos en el código
1. **`backtest/engine.py`:**
   - recorrido en 5 min para señales de 15 min o 1 h; hoy, en velas de 1 h, «stop primero» decide muchas operaciones;
   - nuevos parámetros `entry_mode` (mercado / límite / límite→mercado), `fill_through` (3 pb) y `wait_bars`;
   - R contrafactual de las señales no llenadas;
   - `risk_frac` por señal.
2. **`maker/engine.py`:** la límite vale toda una vela de 1 h y se juzga con su mínimo, sin saber si antes llegó el stop. Hay que pasarla a 5 min (§5).
3. **`robustness/stats.py`:**
   - añadir PSR, MinTRL, SPA y StepM (instalar `arch`);
   - añadir bootstrap estacionario, N efectivo y t agrupada por día;
   - cambiar `monte_carlo` a bloques.
4. **`busqueda/evaluate_v*.py` y `funnel.py`:**
   - DSR con el N efectivo del registro;
   - `var_sr` del mismo periodo que el Sharpe deflactado (hoy, validación frente a construcción + validación);
   - no elegir nunca con el examen;
   - Holm o SPA sobre todas las variantes probadas;
   - ≥300 operaciones.
5. **`intraday/evaluate.py`:**
   - empate realizado, intervalo de Wilson, coste en R y t agrupada;
   - `mc_band` por semanas;
   - `truncation_ok` extendido a variables y etiquetas.
6. **`incubator/meta.py`:** retirarlo.
7. **Nuevo `src/v11/`:** `labels.py` (numba), `features.py`, `cv.py` (con pruebas unitarias de purga y embargo), `meta.py`, `portfolio.py`, `evaluar.py` y `adelante.py`.

## 8. PROTOCOLO v11 (para prerregistrar)

**Paso 0 — Registro.**
- Commit del protocolo, del código y de las pruebas unitarias ANTES de usar BTC.
- Pruebas nuevas: 16 (4 configuraciones × [3 modelos + media]), más el gemelo y el papel.
- El acumulado pasa a 2.062.

**Paso 1 — G0 técnico** (no cuenta como prueba):
- prueba de truncamiento de variables y etiquetas;
- purga y embargo sin solapes, comprobados con datos sintéticos;
- etiquetas barajadas por días: AUC ≤ 0,52 y sin mejora de E[R].

**Paso 2 — Datos y eventos.**
- **Datos:** perpetuo de Binance en 5 min, 15 min y 1 h; métricas de 5 min; funding; prima; Fear & Greed.
- **Desarrollo D:** 2020-10-01→2026-09-30.
- **Señales primarias:** todos los setups ya programados en 15 min y 1 h, sin elegirlos por resultados: `intraday/setups.py`, los patrones de 1 h de `busqueda/v7.py` y `desk15/setups.py`.
- **Agrupado y barreras:** según el §1 y el §4.

**Paso 3 — Configuraciones (4).**
- b ∈ {2, 3} × entrada ∈ {mercado; límite 5 min y luego mercado}.
- Todas con la media de los 3 modelos, EV ≥ +0,05 R y Kelly/4 encogido entre el 0,25 % y el 1 %.

**Paso 4 — Validación.**
- Walk-forward trimestral y CPCV 10/2 sobre D.
- Series diarias en R de las 16 estrategias y de la referencia «tomar todas».

**Paso 5 — Puertas en D (todas):**

| Puerta | Criterio |
|---|---|
| G1 | WF: n ≥ 600 y t ≥ 3,0 (agrupada por día) de la E[R] neta; E[R] > 0 también sin 2025-07→2026-09 |
| G2 | SPA frente a «tomar todas»: p < 0,10; acierto ≥ empate + 3 puntos |
| G3 | CPCV: al menos 7 de 9 caminos con E[R] > 0 |
| G4 | PBO ≤ 0,30 |
| G5 | Costes ×2 y travesía de 6 pb: E[R] > 0 |
| G6 | DSR ≥ 0,95 con N = máx(300; N efectivo ONC) + 16 |
| G7 | ≥ 250 operaciones al año y Sharpe < 5 (si no, auditoría de fuga) |

**Paso 6 — Elección.**
- Pasa la configuración con mayor cota inferior al 95 % de E[R] en el walk-forward.
- Se reentrena con todo D, se congela (hash) y se hace commit.
- Solo sigue esa configuración.

**Paso 7 — Pre-muestra (una sola ejecución).** Gemelo con costes del perpetuo, sin los setups que necesitan OI o funding.
- E[R] ≤ −0,05 R → **falsado**: se para.
- E[R] > 0 con p < 0,05 (bloques semanales) → **apoyo**.
- Cualquier otro resultado → no concluyente: se sigue.

**Paso 8 — Papel.**
- **Arranque:** 00:00 UTC del día siguiente al commit del Paso 6, sin reentrenar.
- **Hipótesis única:** E[R neto] > 0.
- **Fronteras:** las del §3. Máximo 450 operaciones o 12 meses; al llegar a 12 meses, mirada final con z ≥ 1,66.
- **Controles no decisorios:** acierto y reparto de salidas dentro de la banda 5-95 % del walk-forward; pendiente de calibración ≥ 0,5.

**Éxito.** «v11 certificada en papel» exige pasar G0-G7, que la pre-muestra no quede falsada y éxito en el papel. Para dinero real siguen haciendo falta ≥ 90 días de papel y la aprobación EXPRESA del dueño, con tamaño mínimo.

**Si nada pasa:**
- **Si falla D:** no hay papel. Se registran las 16 pruebas, se publica el negativo y no se rescata ninguna variante en D.
- **Si la pre-muestra queda falsada, o el papel acaba en futilidad o sin concluir:** se archiva v11. Esos datos no vuelven a usarse para elegir, y una v12 necesitaría prerregistro y una ventana nueva.
- **Conclusión:** el intradía 2R-3R en BTC no es demostrable con estos datos y costes.
  - El capital sigue en lo ya aprobado: núcleo, carry y K4.
  - La única vía razonable es un estudio nuevo de swing de 1-3 días, con costes ≤ 0,05 R.

## Fuentes
- **Libro de referencia.** López de Prado (2018), *Advances in Financial Machine Learning*. https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086
- **Meta-etiquetado** [revisado; los autores venden software]:
  - Joubert (2022), JFDS. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4032018
  - Meyer, Barziy y Joubert (2023); Thumm et al. (2022). https://github.com/hudson-and-thames/meta-labeling
  - Crítica [opinión]. https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/
- **Sobreajuste y Sharpe** [revisado]:
  - DSR. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
  - PBO. https://papers.ssrn.com/abstract=2326253
  - PSR y MinTRL. https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier
  - N efectivo. https://ideas.repec.org/a/taf/quantf/v19y2019i9p1555-1565.html
- **Comparaciones múltiples** [revisado]:
  - White (2000). https://www.econometricsociety.org/publications/econometrica/2000/09/01/reality-check-data-snooping
  - Hansen (2005) y la librería `arch`. https://arch.readthedocs.io/en/latest/multiple-comparison/multiple-comparison-reference.html
  - Romano y Wolf (2005). doi:10.1111/j.1468-0262.2005.00615.x
  - Harvey, Liu y Zhu (2016). https://doi.org/10.1093/rfs/hhv059
- **Tamaño de muestra** [revisado]: Riley et al. (2020). https://doi.org/10.1136/bmj.m441 También Peduzzi et al. (1996).
- **Kelly** [revisado]: MacLean, Thorp y Ziemba. https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf
- **Órdenes límite** [revisado]:
  - Linnainmaa (2010). https://ideas.repec.org/a/bla/jfinan/v65y2010i4p1473-1506.html
  - Handa y Schwartz (1996). https://ideas.repec.org/a/bla/jfinan/v51y1996i5p1835-61.html
- **Sistemas intradía** [interés comercial]:
  - https://www.sfi.ch/fr/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy
  - https://papers.ssrn.com/abstract=4416622
  - https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/
- **Momentum intradía, Gao et al.** [revisado]:
  - https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html
  - Cifras: https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked
- **Reglas técnicas en cripto** [revisado]: Hudson y Urquhart (2021). https://reading-clone.eprints-hosting.org/85715
- **Tendencia** [revisado]: https://oxfordstrat.com/coasdfASD32/uploads/2016/03/A-Century-of-Evidence-on-Trend-Following-Investing.pdf
- **Day traders** [revisado]:
  - Chague et al. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3423101
  - Barber et al. https://ideas.repec.org/a/eee/finmar/v18y2014icp1-24.html
- **Quantopian** [documento de trabajo]: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2745220

*Nota: el cupo de búsquedas web se agotó al final. El DOI de Romano y Wolf y el enlace espejo de Hudson y Urquhart están sin comprobar.*
