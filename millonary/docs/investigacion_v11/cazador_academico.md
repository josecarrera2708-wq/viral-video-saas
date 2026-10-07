# Cazador académico: estrategias intradía de BTC con estadísticas publicadas

Fecha: 2026-10-06. No he hecho backtests con nuestros datos de BTC. Los únicos cálculos propios usan datos sintéticos (paseo aleatorio y t de Student) y van marcados. Etiquetas de evidencia: **[revista]** artículo revisado por pares, **[WP]** documento de trabajo, **[tesis]**, **[empresa]** research de una empresa, **[marketing]** afirmación sin método.
Límite: el presupuesto de búsquedas web se agotó al final. No pude hacer una última pasada por trabajos de 2025-2026 sobre estrategias de 1-4 h con costes.

## Conclusión

1. La predictibilidad intradía de BTC está documentada, pero los efectos bien medidos dan entre 0,5 y 10 pb por operación. Con 14 pb de coste mueren: Shen et al. (2022) se equilibran con 3-10 pb, Kim y Hansen (2026) miden 5-17 pb y Kitron y Wengrowicz (2026) 1,3 pb a 15 min.
2. Solo hay dos ideas cuyo margen bruto publicado podría superar nuestros costes:
   - la reversión tras saltos de 2 h (un estudio, con datos de 2015-2018);
   - la ORB en la apertura cash de EE. UU., con evidencia en acciones y futuros pero no en cripto.
3. La ORB que funciona en acciones usa un rango de 5 min y un stop del 10 % del ATR. En BTC eso cuesta 0,3-0,7 R por operación. Las versiones de 30-60 min sí aguantan los costes, pero en la propia fuente tienen un Sharpe de solo 0,21-0,40.
4. Con stop de 1R, objetivo de 2R y nuestros costes, hay que acertar al menos el 38-43 % para no perder. Ganar más operaciones de las que se pierden con objetivo 2R exigiría unos +0,5 R por operación, y ninguna fuente intradía de BTC respalda algo así.
5. Propongo prerregistrar solo 3 variantes, lo que lleva el total a 2.047 pruebas. Lo más probable es que fallen.

## Aritmética común (cálculo sintético)

Coste de 0,14 % expresado en R para una ORB. R va de la entrada al otro extremo del rango. Supuestos: volatilidad anual del 40-60 % y volatilidad en la apertura de 1 a 1,5 veces la normal.

| Rango | 5 min | 15 min | 30 min | 60 min |
|---|---|---|---|---|
| Anchura mediana | 0,11-0,26 % | 0,25-0,57 % | 0,39-0,88 % | 0,58-1,30 % |
| Coste mediano | 0,31-0,70 R | 0,18-0,41 R | 0,13-0,29 R | 0,09-0,21 R |

Acierto mínimo para R neta = 0 sin salidas por tiempo: p = (1+c)/(1+k), donde c es el coste en R y k el objetivo en R.

| Coste c | 0 | 0,15 R | 0,20 R | 0,30 R |
|---|---|---|---|---|
| Objetivo 2R | 33,3 % | 38,3 % | 40,0 % | 43,3 % |
| Objetivo 3R | 25,0 % | 28,7 % | 30,0 % | 32,5 % |

## Candidatas, ordenadas por solidez de la evidencia aplicable a BTC intradía

Criterio de orden: revisión por pares, tamaño de la muestra, prueba fuera de muestra, que sea BTC y que sea reciente.

### 1. Momentum intradía «noche + primera media hora → última media hora». Evidencia alta, NO viable

- **Fuentes:**
  - Shen, Urquhart y Wang (2022) **[revista]** Financial Review ([doi](https://doi.org/10.1111/fire.12290), [PDF](https://centaur.reading.ac.uk/100181/));
  - Gao, Han, Li y Zhou (2018) **[revista]** JFE ([doi](https://doi.org/10.1016/j.jfineco.2018.05.009));
  - Baltussen et al. (2021) **[revista]** JFE ([doi](https://doi.org/10.1016/j.jfineco.2021.04.029)).
- **Datos y estadísticas (Shen et al.):** BTC/USD de contado en 5 bolsas, 2013-2020, velas de 1 min.
  - R² = 1,44 % (β = 0,968, t = 4,38); con la penúltima media hora, que predice en contra, 2,12 %; fuera de muestra, 1,09-1,61 %.
  - Estrategia combinada: acierto 58,1 %, 16,7 % al año, Sharpe 1,72, sin costes. Punto de equilibrio: 3, 7 y 10 pb por operación.
  - Que el apalancamiento suba ese equilibrio, como dicen los autores, es un error: el coste crece con el nominal.
  - Gao et al. (SPY 1993-2013): R² 1,6 %, Sharpe 1,08. Baltussen et al.: más de 60 futuros, 1974-2020.
- **Reglas (de la fuente):**
  - El «cierre» del día son las 17:00 de Nueva York (21:00 o 22:00 UTC).
  - r1 va de las 17:00 NY del día anterior a 30 min después del pico de volumen de la apertura (entre las 09:00 y las 09:40 NY según la bolsa). r2 va de 16:00 a 16:30 NY.
  - A las 16:30 NY: largo si r1 > 0 y r2 < 0; corto si r1 ≤ 0 y r2 ≥ 0; en otro caso no se opera.
  - Salida a las 17:00 NY. No hay stop ni objetivo.
- **Frecuencia:** unas 0,5 operaciones al día.
- **Costes:** el bruto, 10 pb, es menor que 14 pb. Con órdenes maker (4 pb) quedarían 6 pb como mucho, antes de selección adversa. Una tenencia de 30 min sin stop no encaja en el esquema 1R/2R.
- **Riesgos:** son datos de contado de 2013-2020, y el mecanismo (provisión de liquidez) probablemente se ha erosionado.
- **Veredicto:** no probar.

### 2. Desequilibrio agresor al inicio de cada cuarto de hora. Evidencia media-alta, NO replicable

- **Fuente:** Kim y Hansen (2026) **[WP]** ([arXiv 2607.09426](https://arxiv.org/abs/2607.09426)).
- **Datos:** perpetuos USDT de Binance de 6 monedas, operación a operación, de 2021-01 a 2024-10.
- **Estadísticas:** el desequilibrio de los 10 primeros segundos tras xx:00/15/30/45 predice el rendimiento a 4-12 h con signo positivo (significativo al 95 % en 4 de 6 contratos) y a menos de 30 min con signo negativo. Efecto intercuartílico: 5-6 pb, y 9,8/16,9 pb a 8/12 h; los autores lo califican de «pequeño frente a los costes».
- **Reglas:** no reproducibles con velas de 5 min: la señal vive en 10 s y en aperturas de 1 y 5 min la fuente apenas encuentra predicción. Dato útil: excluir los cuartos de hora del funding (00/08/16 UTC) no cambia nada.
- **Veredicto:** descartar. Q05 usaba un sustituto (posición del cierre en la vela), no el volumen taker, pero la literatura no da motivos para repetirlo con el dato real.

### 3. Reversión tras «saltos» de 2 h. Evidencia media-baja, viable sobre el papel

- **Fuentes:**
  - De Nicola (2021) **[revista]** Ledger 6:58-80 ([enlace](https://ledger.pitt.edu/ojs/ledger/article/view/213)).
  - Apoyo parcial y reciente: Kitron y Wengrowicz (2026) **[WP]** ([arXiv 2608.21888](https://arxiv.org/abs/2608.21888)). Encuentran reversión a 15 min en el 90 % de 183 pares de Binance desde 2021, concentrada tras movimientos dirigidos por órdenes tomadoras, pero con solo 1,3 pb brutos.
- **Datos y estadísticas:** BTC/USD en Bitstamp, de 2015-03 a 2018-06, sin costes.
  - Correlación entre el salto y la barra siguiente de 2 h: −0,09 con todas las barras, −0,19 con saltos ≥3σ y −0,40 con saltos ≥6σ.
  - Beneficio bruto medio por operación (a contrapié, una barra):
    - a 2 h: 0,30 % (≥2σ), 0,49 % (≥3σ) y 0,74 % (≥4σ);
    - a 1 h, con ≥3σ: 0,21 %;
    - a 4 h, con ≥3σ: 0,33 %.
  - El autor señala 2 h como el horizonte más alto y consistente.
  - No publica acierto ni Sharpe. La versión sin umbral multiplicó el capital por 8,5 (sin reinvertir), frente a 0,99 ± 1,44 en 10.000 estrategias aleatorias.
- **Reglas:**
  - Con velas de 1 h se forman barras de 2 h alineadas a horas pares UTC. r = cierre / cierre anterior − 1.
  - σ es la desviación típica de r en las 360 barras previas. Es una adaptación para que sea causal: la fuente usa σ de toda la muestra.
  - Al cierre de la barra: si r ≥ +3σ, corto; si r ≤ −3σ, largo. Entrada en la apertura de la siguiente vela de 1 h.
  - Salida por tiempo a las 2 h (de la fuente).
  - Para encajar en el marco del dueño, y esto no está en la fuente: stop de 1R = 1σ y objetivo de 2R = 2σ.
  - Sin filtro de sesión y con una sola posición abierta a la vez.
- **Por qué 3σ:** es el menor umbral de la fuente cuyo bruto (0,49 %) supera los costes duplicados (0,28 %). Se elige por esa puerta de costes, no por el rendimiento.
- **Frecuencia:** con colas gruesas (t de Student con ν de 3 a 6, sintético), entre el 1,0 y el 1,4 % de las barras. Eso son 0,13-0,17 operaciones al día, unas 50-60 al año.
- **Costes:** R = σ de 2 h ≈ 0,6-0,9 %, así que el coste es de 0,15-0,23 R. El bruto publicado equivale a unos 0,55-0,8 R.
- **Diferencia con lo ya probado:** reacciona a un suceso (una sola barra de ≥3σ, ~1 % de las barras) y sale a las 2 h. No usa niveles de Bollinger, RSI ni VWAP. Su espejo, I10 (continuación tras vela grande), perdió en los tres periodos.
- **Riesgos:**
  - muestra única, antigua y de contado, y el propio autor prevé que el efecto desaparezca;
  - los umbrales de la fuente usan σ de toda la muestra, así que son optimistas;
  - nuestras reversiones I03, I04 e I06 perdieron;
  - los días de cascada (marzo de 2020, mayo de 2021, 10 de octubre de 2025) son el peor escenario;
  - justo después de un salto el deslizamiento puede superar los 2 pb.

### 4. ORB clásica en la apertura cash de EE. UU. con filtro «en juego». Evidencia alta fuera de cripto y débil en la versión que aguanta costes

- **Fuentes:**
  - Zarattini y Aziz (2023) **[WP]** ([SSRN 4416622](https://papers.ssrn.com/abstract=4416622));
  - Zarattini, Barbon y Aziz (2024) **[WP]**, en adelante ZBA ([SSRN 4729284](https://ideas.repec.org/p/chf/rpseri/rp2498.html));
  - Holmberg, Lönnbark y Lundström (2013) **[revista]** FRL ([enlace](https://ideas.repec.org/a/eee/finlet/v10y2013i1p27-33.html));
  - Tsai et al. (2019) **[revista]** IEEE Access ([doi](https://doi.org/10.1109/ACCESS.2019.2899177));
  - Lundström (2017) **[tesis]** ([enlace](https://swopec.hhs.se/umnees/abs/umnees0948.htm)).
- **Por qué podría trasladarse a BTC:** el volumen de BTC se dispara entre las 09:00 y las 09:40 NY (Shen et al. 2022); las 15:00 UTC son la hora de más volumen y EE. UU. tiene el 45 % de la liquidez ([Kaiko 2024](https://www.kaiko.com/resources/btc-etfs-impact-on-spot-market-structure) **[empresa]**); la volatilidad culmina hacia las 16 UTC ([Hansen, Kim y Kimbrough 2024](https://arxiv.org/abs/2109.12142) **[revista]**).
- **Estadísticas:**
  - **QQQ, 2016-2023:** rango de 5 min, stop en el otro extremo y objetivo de 10R o salida al cierre. 1.795 operaciones, acierto del 24 %, +0,13 R por operación y Sharpe 1,12. Es neto de comisiones, pero sin deslizamiento.
  - **ZBA, acciones «en juego»:** 7.000 valores, volumen relativo (RVOL) ≥ 100 % frente a los 14 días previos, los 20 primeros, stop del 10 % del ATR y salida al cierre.
    - Por duración del rango: 5 min, Sharpe 2,81 y acierto 48,4 %; 15 min, 1,43; 30 min, 0,21; 60 min, 0,40 y acierto 42 %.
    - Con RVOL < 100 %, −0,02 R por operación; con RVOL > 100 %, +0,08 R.
  - **Crudo, 1983-2011:** significativa, sobre todo entre 2000 y 2011.
  - **Futuros de índices, 2003-2013:** más del 8 % anual (p < 3 %).
  - **Lundström:** el rendimiento varía 150-200 pb al día entre el estado de volatilidad más alto y el más bajo.
  - **En contra:** Chen (2024) **[tesis]** ([enlace](https://thesis.lib.nccu.edu.tw/thesis/detail/5ee3a21ae846b1c833ff57e17695599b)). Con datos de 1 min de BTC, las rupturas de rango intradía son positivas en bruto, pero tras costes no superan comprar y mantener, y decaen desde 2017.
- **Reglas:**
  - **Días y hora de apertura:** solo días hábiles de la bolsa de Nueva York (NYSE). La apertura T0 son las 09:30 NY: 13:30 UTC con horario de verano de EE. UU. y 14:30 UTC en invierno.
  - **Rango:** máximo y mínimo de las 12 velas de 5 min entre T0 y T0+60 min.
  - **Filtro (de ZBA):** el volumen del rango debe ser al menos la media del mismo tramo en los 14 días hábiles previos.
  - **Dirección (de ZBA):** si el rango cerró por encima de su apertura, solo largos; si cerró por debajo, solo cortos; si cerró igual, no se opera.
  - **Señal y entrada:** la primera vela de 5 min que cierra fuera del rango en esa dirección da la señal. Se entra en la apertura de la vela siguiente.
  - **Stop y objetivo:** stop en el otro extremo del rango. Objetivo de 2R; la variante usa 3R.
  - **Salida y límite:** lo que llegue antes entre entrada + 4 h y las 16:00 NY. Una operación al día.
- **Por qué 60 min:**
  - El stop del 10 % del ATR y los rangos de 5-15 min cuestan 0,3-0,7 R en BTC.
  - Entre 30 y 60 min, la fuente da mejor Sharpe a 60 (0,40 frente a 0,21) y el coste sintético es menor.
- **Frecuencia:** 0,35-0,45 operaciones por día hábil, unas 90-110 al año.
- **Costes:**
  - 0,09-0,21 R, con un acierto mínimo del 36-40 % con objetivo 2R o del 27-30 % con 3R.
  - Entrar con orden maker en la vuelta al borde del rango lo bajaría a 0,05-0,1 R.
- **Diferencia con lo ya probado:** I14 usaba la vela fija de 13:00-14:00 UTC (en invierno, antes de la apertura), cuerpo > 0,5 ATR, stop de 1,5 ATR y objetivo de 1,5R, sin rango ni volumen. La zona de ruido de Zarattini usa bandas y VWAP.
- **Riesgos:**
  - la evidencia fuerte corresponde a la configuración que no podemos pagar, y la de 60 min es débil en la propia fuente;
  - el efecto de la apertura de EE. UU. se reforzó con los ETF en 2024, así que construcción (2020-2023) y validación/examen pueden comportarse distinto;
  - la ORB es muy conocida.

## Líneas investigadas sin evidencia operable

| Línea | Lo que hay | Por qué no |
|---|---|---|
| Datos macro a hora fija (IPC, empleo, Fed) | [Benigno y Rosa 2023](https://www.newyorkfed.org/research/staff_reports/sr1052) **[WP Fed NY]**: BTC no responde a sorpresas macro en 2017-2022. [Block Scholes 2026](https://www.blockscholes.com/institutional-research/is-bitcoin-showing-greater-sensitivity-to-us-cpi-releases-again) **[empresa]**: reacción al IPC en la primera hora (R² ≈ 80 % en los últimos 12 datos), sin deriva a 4-24 h; se desplomó a finales de 2024-2025. [Ben Omrane et al. 2023](https://ideas.repec.org/a/spr/annopr/v330y2023i1d10.1007_s10479-021-04353-0.html) **[revista]**: provocan saltos | No hay ninguna regla publicada. Sin el dato de sorpresa no hay dirección. Unos 30 eventos al año y necesita un calendario externo |
| Funding (00/08/16 UTC) y cierre diario/semanal UTC | [Hansen et al. 2024](https://quantpedia.com/periodicity-in-cryptocurrencies-recurrent-patterns-in-volatility-and-volume/): picos de volatilidad, no de dirección. Kim y Hansen 2026: los cuartos de hora de funding no son especiales | No hay efecto direccional documentado |
| Fin de semana y huecos de CME | Lo de que «el 95 % se rellena» no tiene horizonte temporal **[marketing]**. [CME opera 24/7 desde el 29-05-2026](https://theblock.co/post/390491/cme-group-launch-24-7-crypto-futures-options-trading-may-29) | El hueco ya no existe y «lunes de Asia» ([Concretum](https://concretumgroup.com/seasonality-in-bitcoin-intraday-trend-trading/)) ya se probó |
| Continuación en días de sobrerreacción | [Caporale y Plastun](https://www.brunel.ac.uk/economics-finance-and-accounting/research/pdf/1917-Oct-GMC-Momentum-effect-in-the-Cryptocurrency-Market-after-One-day-Abnormal-Returns.pdf) **[revista]**: 86-91 % de acierto en BTC | Sesgo de anticipación: clasifica el día con su propio cierre. La versión causal no está probada |
| Ratio largo/corto de los grandes traders | «Caídas el 71 % de las veces en 48 h» ([fuente](https://sites.google.com/view/decentralised-news/home/longshort-ratio-analysis)) **[marketing]** | Sin método y con horizonte de 48 h |
| Curvas intradía y microestructura | [Bouri et al. 2021](https://repository.essex.ac.uk/30487/) **[revista]**; [Easley et al. 2024](https://stoye.economics.cornell.edu/docs/Easley_ssrn-4814346.pdf) **[WP]** | En Bouri el Sharpe cambia de signo con un parámetro; Easley predice volatilidad, no dirección |
| 21-23 UTC y lunes de Asia | [Quantpedia](https://quantpedia.com/are-there-seasonal-intraday-or-overnight-anomalies-in-bitcoin/), Concretum | Ya probados (R ≤ 0) |

## Tabla resumen

| # | Candidata | Evidencia | Solidez para BTC | Operaciones | Coste | Encaja en 1R/2R | Veredicto |
|---|---|---|---|---|---|---|---|
| 1 | Momentum de la última media hora | BTC 2013-20, SPY, 60 futuros | Alta | ~0,5/día | Equilibrio 3-10 pb < 14 pb | No | No probar |
| 2 | Desequilibrio taker en el cuarto de hora | Binance 2021-24 | Media-alta | — | Efecto 5-17 pb | No | No replicable |
| 3 | Reversión de saltos ≥3σ en 2 h | Bitstamp 2015-18, sin costes | Media-baja | 0,13-0,17/día | 0,15-0,23 R | Adaptado | Probar |
| 4 | ORB de 60 min en la apertura cash de EE. UU. + RVOL | Acciones, crudo e índices; no cripto | Baja en BTC | 0,35-0,45/día hábil | 0,09-0,21 R | Sí | Probar |

## Top-3 recomendado (3 pruebas nuevas)

1. **ORB de 60 min en la apertura de EE. UU. + RVOL, objetivo 2R.** Es la única idea nueva con coste asumible (0,09-0,21 R), mecanismo documentado (pico de volumen y volatilidad en la apertura, reforzado por los ETF) y parámetros de las fuentes. La apertura de EE. UU. no se ha probado bien: I14 ignoraba el cambio de hora. Expectativa baja: en acciones esta versión da Sharpe 0,40.
2. **Reversión de saltos ≥3σ en barras de 2 h.** Es el único margen publicado para BTC que, en bruto, triplica nuestro coste, con stop amplio en el horizonte de 1-4 h (donde el proyecto ha visto lo mejor) y una sola variante. Riesgo principal: decaimiento desde 2018.
3. **La misma ORB con objetivo 3R.** Las fuentes y vuestros resultados favorecen objetivos largos o dejar correr, y 3R entra en lo que pide el dueño. No es una idea independiente: no hay una tercera con evidencia comparable, y no gastaría pruebas en datos macro, funding o fin de semana.

## Notas para el prerregistro

- **Horas de EE. UU.:** convertir con la zona America/New_York para que el cambio de hora se aplique solo.
- **Calendario:** usar el de festivos de la NYSE. En las medias sesiones, la salida es a las 13:00 NY.
- **σ y barras:** σ móvil sin incluir la barra actual, barras de 2 h alineadas a horas pares y una posición abierta por estrategia.
- **Qué registrar:** el acierto obtenido junto al acierto mínimo de la tabla de arriba. Esa comparación es la prueba honesta para el esquema 2R.
