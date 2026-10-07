# Cazador de flujo y derivados: estrategias intradía con OI, ratios, flujo taker, prima y funding

## 0. Resumen

- La evidencia publicada confirma lo que ya vio el proyecto: el flujo agresor predice, pero vela a vela el efecto es diminuto. La reversión a 15 min existe todos los años de 2021 a 2026, pero deja como mucho 1,3 pb brutos por operación ([Kitron y Wengrowicz 2026](https://arxiv.org/abs/2608.21888)). Los factores de microestructura dan Sharpe neto muy negativo ([Pindza 2026](https://www.frontiersin.org/journals/blockchain/articles/10.3389/fbloc.2026.1811716/full)), y en una búsqueda auditada sobre el perpetuo BTC ninguna de 460 combinaciones de costes dio Sharpe positivo ([Zeng et al. 2026](https://arxiv.org/abs/2608.25348)). **Solo quedan eventos extremos y poco frecuentes, con R amplio.**
- Propongo 6 estrategias. Solo recomiendo prerregistrar las tres primeras (E1–E3), porque cada prueba nueva sube el listón del DSR (ya hay 2.044 pruebas).
- Aviso de datos: el sello temporal de las métricas **cambió de significado el 2024-03-04**. Además, los ratios de top traders faltan casi todo 2022 (detalles en §1).

## 1. Datos: formato, huecos y causalidad

Esto sale de leer solo el formato, la cobertura y los huecos del archivo `perp_BTCUSDT_metrics_5m.parquet`. No he calculado ningún rendimiento.

- **Cobertura**: 638.438 filas entre 2020-09-01 00:00 y 2026-09-28 23:55. Los sellos caen exactos cada 5 min.
  - Faltan 634 ventanas. Hay 10 huecos de 1 h o más; el mayor dura 10,5 h (2024-02-16/17).
- **Agujeros en las columnas**:
  - Ratios de top traders (las dos columnas): vacíos del 2021-12-30 al 2022-12-14, unas 92.000 filas.
  - Ratio taker: vacío del 2021-12-30 al 2022-05-09.
  - Ratio de cuentas: vacío del 2021-12-30 al 2022-01-19.
  - OI igual a 0 en 485 filas; el tramo más largo va del 2022-03-07 15:30 al 2022-03-08 01:05.
  - Valores congelados: 2021-04-27 de 06:50 a 11:05, del 2021-05-21 11:45 al 2021-05-22 04:20 y 2021-11-02 de 05:25 a 07:10.
- **Cambio de convención el 2024-03-04 00:00 UTC.** Lo comprobé cruzando con las velas, no con precios:
  - **Antes de esa fecha**, el registro con `create_time` t resume la ventana [t−5, t). Su ratio taker coincide con el de la vela de 5 min que abre en t−5 (correlación 0,998–0,999), y la |ΔOI| se alinea con el volumen de esa misma vela.
  - **Desde esa fecha**, el registro resume la ventana [t, t+5). Su ratio coincide con la vela que abre en t (correlación 0,998).
  - El OI y los ratios de cuentas cambian igual. Las velas de 5 min, 15 min y 1 h siguen siendo coherentes entre sí, así que el cambio no viene de las velas.
  - El apéndice A de [Garcia Seuma 2026b](https://arxiv.org/abs/2608.03616) da por hecho el sello de «fin de intervalo». En nuestros datos eso solo es cierto hasta el 2024-03-03. Quien use esa convención mira 5 min al futuro durante toda la validación y el examen.
  - [Zeng et al.](https://arxiv.org/abs/2608.25348) excluyeron el OI porque su hora de publicación no está verificada.
- **Regla de disponibilidad propuesta**: un registro con `create_time` t solo se usa desde **t + 10 min** (cubre las dos convenciones más 5 min de publicación). Probar +15 y +20 min como robustez, no para elegir.
- **Papel en vivo**: la API REST solo guarda 30 días y documenta el sello como «end time of the period» ([docs de Binance](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Long-Short-Ratio)). Hay que registrar la hora real de llegada.
- **El ratio taker de las métricas es redundante** con taker_buy/(volumen − taker_buy) de la vela. Mejor las velas: están completas, sin el agujero de 2022 (entre 2025-08 y 2026-03 difieren ~1 % de mediana).
- **OI en BTC, no en USDT** (`sum_open_interest`): el valor en USDT cae con el precio aunque nadie cierre. El OI de Binance cuadra razonablemente con su volumen; el de Bybit y OKX, no ([Giagkiozis y Said 2024](https://arxiv.org/abs/2310.14973)).
- **Funding y prima terminan el 2026-08-31**: E2 y E3 pierden septiembre de 2026 en el examen.
- **Aviso sobre el repo**: `src/data/extra_features.py` toma la foto con `create_time` ≤ apertura de la vela. Desde 2024-03 esa foto cubre los primeros 5 min de la vela: seguro al cierre de velas de 15 min o más; en velas de 5 min equivale a usar la propia vela.

**Notación común, todo causal:**
- Velas del perpetuo con etiqueta en la apertura; se conocen al cierre.
- **ΔOI_k**: ln OI(τ) − ln OI(τ−k), donde τ es el último `create_time` que sea ≤ T − 10 min.
- **σ_1h**: desviación típica de los rendimientos logarítmicos de las 720 velas de 1 h anteriores.
- **pX**: percentil X de la misma variable en los 30 días previos (o 90 días donde se indique), sin incluir el valor actual.
- **TI**: 2·taker_buy_base/volumen − 1.
- **ATR**: ATR(14) del marco de la señal.
- No hay señal si la ventana tiene menos del 80 % de los datos, si el OI vale 0 o si hay 3 o más valores idénticos seguidos.
- Enfriamiento de 4 h tras cada señal.
- Ejecución con el motor actual: entrada a mercado en la apertura siguiente, objetivo con orden límite (maker), stop y salida por tiempo a mercado.

**Umbral de rentabilidad con costes**: con R ≥ 1 ATR de 1 h, el coste ronda 0,07–0,15 R. Hacen falta aciertos de al menos 36–38 % con objetivo 2R y de al menos 28–29 % con objetivo 3R.

## 2. Estrategias, ordenadas por solidez de la evidencia

### E1 · Rebote tras una cascada de liquidaciones inferida (velas de 1 h, ambos lados). Evidencia: media

**Fuentes**
- **[Publicada]** [De Nicola 2021, *Ledger*](https://ledgerjournal.org/ojs/ledger/article/download/213/212/1232), con datos de Bitstamp 2015–2018:
  - Tras movimientos de 1 h de 4σ o más, la correlación con la hora siguiente es −0,148. En velas de 2 h es −0,231.
  - Apostar en contra rindió por operación, en bruto: en 1 h, 0,34 % con 4σ, 0,49 % con 5σ y 0,58 % con 6σ; en 2 h, 0,74 %, 1,18 % y 1,81 %.
  - El autor lo atribuye a la sobrerreacción y a las «cascading liquidations». Son datos antiguos y de contado; el mercado se ha vuelto más eficiente (Hurst de 0,42 a 0,49, [Tang et al.](https://arxiv.org/abs/2402.11930)).
- **[Publicada]** [Kitron y Wengrowicz 2026](https://arxiv.org/abs/2608.21888), con 183 pares de Binance:
  - La reversión aparece en 24 de 24 años por moneda entre 2021 y 2026.
  - Se concentra tras velas empujadas por el flujo taker y crece con su intensidad: la diferencia en la tasa de giro es +0,021 (IC 0,015–0,026).
  - Desaparece hacia las 4 h.
- **[Publicada]** [Scaillet et al. 2020](https://arxiv.org/abs/1704.08175): en general, los saltos dejan un cambio de precio persistente. Por eso hace falta el filtro de OI, para separar los movimientos forzados (transitorios) de los informativos (persistentes).
- **[Publicada]** Garcia Seuma 2026 ([a](https://arxiv.org/abs/2607.27070), [b](https://arxiv.org/abs/2608.03616)):
  - En octubre de 2025 (registro de Hyperliquid) el 88 % de las ventas forzadas ocurrió en los primeros 30 min, y el 96,5 % en la primera hora (b).
  - El OI se vacía entre un 25 % y un 70 % en siete cascadas (b); en BTC de Binance cayó un 24,6 % dentro del día (a).
  - Conclusión: la cascada cabe en una vela de 1 h, y se entra después de ella.
- **[Proveedor]** K33:
  - Los feeds de liquidaciones están recortados (una liquidación por segundo), así que el OI es mejor indicador ([Forklog](https://forklog.com/en/k33-research-unveils-underreported-liquidation-volumes-on-major-cexs/amp)).
  - Tras el 5 % de las mayores liquidaciones, BTC rinde a 30 días un +0,78 % de media (frente al 5,9 % habitual), con mediana −1,1 % ([The Block](https://www.theblock.co/post/372115/whats-next-after-cryptos-fourth-largest-long-liquidation-event-of-2025)). Por eso conviene recoger 2R y salir pronto, no «dejar correr».

**Reglas.** Largo al cierre de la vela de 1 h T si se cumplen las cuatro condiciones:
1. r_1h ≤ −4σ_1h.
2. ΔOI_60m ≤ p5.
3. Volumen de la vela ≥ p95.
4. TI_1h < 0.

Corto, en espejo: r_1h ≥ +4σ_1h, ΔOI_60m ≤ p5, volumen ≥ p95 y TI > 0.

**Parámetros.** El umbral de 4σ viene de la rejilla de la fuente. p5 y p95 son umbrales naturales.

**Salidas.**
- Stop a una distancia de clip((C − L) + 0,25·ATR; 1·ATR; 3·ATR). En cortos, (H − C) + 0,25·ATR.
- Objetivo 2R.
- Salida por tiempo a las 4 velas (4 h): la reversión es de primer orden y se apaga hacia las 4 h.

**Frecuencia.** Simulé un GARCH-t sintético con parámetros típicos (no con BTC): sale 27–37 episodios de −4σ al año por lado. Tras los filtros, estimo **2–4 al mes sumando los dos lados**.

**Costes.** Tras un shock de 4σ, el ATR de 1 h suele estar por encima del 1 %, así que el coste baja a ≈0,1 R. Si el efecto de 2015–2018 siguiera vivo, rendiría unos +0,25 a +0,35 R brutos; si se ha reducido a la mitad, queda en tablas. El margen es estrecho.
- **Riesgo de ejecución**: en la cascada de octubre de 2025 el spread medio se multiplicó por 30 y la profundidad cayó un 98 % ([Amberdata](https://blog.amberdata.io/how-3.21b-vanished-in-60-seconds-october-2025-crypto-crash-explained-through-7-charts)). Hay que exigir que aguante costes ×2 y probarla con el estrés de deslizamiento del stop (`stress_range_frac`).

**Qué cambia frente a lo ya probado.** No usa niveles, como el barrido de 96 velas, ni osciladores, como RSI(2). Condiciona en el desapalancamiento forzado medido por el OI, que es la causa propuesta de la reversión.

**Diagnósticos (no sirven para elegir).** Resultado por lado, y versión sin filtro de OI.

### E2 · Exceso del perpetuo con prima extrema (1 h, ambos lados). Evidencia: media-baja

**Fuentes.** **[Publicada]** [He, Manela, Ross y von Wachter](https://arxiv.org/abs/2212.06888):
- La brecha entre perpetuo y contado en BTC tiene una vida media de **1,68 h** (VECM con datos horarios).
- Tras subidas del contado, el perpetuo cotiza caro por la demanda apalancada que extrapola.
- Cuando está caro, el flujo taker se gira a vender perpetuo (coeficiente −0,0106, t = −13,3): corrige la pata del perpetuo.
- Desde 2022 las desviaciones han caído mucho (media anualizada de 0,69 a 0,17).
- Ojo: el paper no prueba la operación direccional. Esa parte es inferencia mía.

**Reglas.** Corto al cierre de T si se cumplen las tres:
- Prima de 1 h (cierre oficial del índice) ≥ p99 de las 720 horas previas.
- r_1h ≥ +2σ_1h.
- TI_1h > 0.

Largo, en espejo: prima ≤ p1, r_1h ≤ −2σ_1h y TI < 0.

**Salidas.**
- Stop a clip((H − C) + 0,25·ATR; 1; 3·ATR).
- Objetivo 2R.
- Salida a las 4 h, unas 2,4 vidas medias.

**Frecuencia.** Estimo 1–3 al mes sumando los dos lados.

**Costes.** La propia brecha (unos 0,05–0,2 %) es menor que el coste. Lo que se paga es la reversión del exceso de precio en horas de 2σ o más, donde R ≥ 1 ATR. Se solapa con E1 en los desplomes.

### E3 · Squeeze contra el lado abarrotado (ruptura de 1 h, objetivo 3R). Evidencia: baja

**Fuentes.**
- **[Proveedor]** Informe de Glassnode y Bybit, recogido por [Decrypt](https://decrypt.co/378686/bitcoin-sharpest-rally-two-years-short-liquidations): en agosto de 2026 BTC subió un +24,6 % en 5 días mientras el OI en monedas caía un 12,6 %; el 89 % de lo liquidado eran cortos. Los squeezes pueden durar.
- **[Proveedor]** K33, vía [The Block](https://www.theblock.co/post/397531/bitcoin-breakout-odds-rise-negative-funding-streak-mirrors-bottoming-regimes-k33): los regímenes de funding negativo con OI al alza aparecieron cerca de suelos. Son 3 episodios y no da estadísticas.
- **[Interna]** El filtro «funding a contrapié» fue de los mejores (+0,17 R). Pero salió de una búsqueda con muchas pruebas, así que no es evidencia independiente.

**Reglas.** Largo si se cumplen las tres:
- prem8 (media de las 8 últimas primas horarias, lo que impulsa el próximo funding) ≤ p5 de 90 días: los cortos están abarrotados.
- ΔOI_24h ≥ p80 de 90 días: se están abriendo posiciones.
- C_T > máximo de las 24 h previas.

Corto, en espejo: prem8 ≥ p95, ΔOI_24h ≥ p80 y C_T < mínimo de las 24 h previas.

**Salidas.**
- Stop a clip((C − L) + 0,25·ATR; 1; 3·ATR).
- Objetivo **3R**, porque es una operación de continuación.
- Salida a las 4 h.

**Qué cambia.** El Donchian de 24 h ya se probó, pero sin la prima ni la acumulación de OI.

**Frecuencia.** Estimo 0,5–1,5 al mes. Hay riesgo de no llegar a 20 operaciones en el examen.

**Costes.** Las velas de ruptura son anchas, y con 3R el acierto necesario baja a ~29 %.

### E4 · Ruptura sin posiciones nuevas: divergencia entre precio y OI (1 h). Evidencia: baja y contradictoria

**Reglas.**
- Corto si C_T > máximo de las 24 h previas y ΔOI_4h ≤ p20 de 90 días: el precio rompe mientras el OI cae, es decir, cierre de cortos sin largos nuevos.
- Largo, en espejo: C_T < mínimo de las 24 h previas y ΔOI_4h ≤ p20 (liquidación de largos).
- Stop a clip((H − C) + 0,25·ATR; 1; 3·ATR), objetivo 2R, salida a las 4 h.

**Fuentes.** Solo hay **[opinión]** de traders («si sube con OI cayendo, es cierre de cortos y es frágil»). Lo contradice el rally de agosto de 2026 citado en E3. No encontré estadísticas publicadas.

**Frecuencia.** Estimo 3–6 al mes. Su espejo («ruptura con OI subiendo, continuación») sirve como diagnóstico; no hay que registrar las dos.

### E5 · Minoristas frente a top traders (1 h). Evidencia: muy baja

**Datos.** `count_long_short_ratio` (todas las cuentas, como aproximación al minorista) frente a `sum_toptrader_long_short_ratio` (posiciones del 20 % con más margen, según la [definición de Binance](https://developers.binance.com/docs/derivatives/usds-margined-futures/market-data/rest-api/Top-Trader-Long-Short-Ratio)).

**Fuentes.**
- No hay estudios con números. Coinglass, Hyblock y CryptoQuant solo ofrecen descripciones.
- **[Publicada]** [CFTC, Ferko, Mixon y Onur 2024](https://www.cftc.gov/sites/default/files/2024-11/Retail_Traders_Futures_V2_new_ada.pdf): el minorista de futuros es contrarian y compra las caídas. Por eso un extremo de minoristas largos suele llegar tras una bajada, y ir contra ellos es en parte momentum.

**Reglas.**
- Corto si el ratio de cuentas ≥ p95, la posición de top traders ≤ p50 y C_T < mínimo de las 4 h previas.
- Largo, en espejo.
- Stop en el extremo opuesto de las 4 h + 0,25·ATR, recortado a [1; 3]·ATR. Objetivo 2R, salida a las 4 h.

**Frecuencia.** Estimo 2–4 al mes, pero el agujero de 2022 deja unos 2,3 años de construcción.

**Diagnóstico.** Compararla con la ruptura de 4 h sola.

### E6 · Absorción del flujo agresor (15 min). Evidencia: en contra

**Reglas.**
- Largo si TI_15 ≤ p1, el volumen ≥ p95 y la vela cierra en su mitad superior: (C − L)/(H − L) ≥ 0,5.
- Corto, en espejo.
- Stop a clip((C − L) + 0,25·ATR15; 1,5; 4·ATR15), objetivo 2R, salida a las 16 velas (4 h).

**Fuentes.**
- **[Publicada]** Kitron y Wengrowicz: tras velas en las que el flujo va contra el precio, la vela siguiente es una moneda al aire. Doce retardos de desequilibrio no añaden nada a la trayectoria del precio.
- [El efecto del cuarto de hora](https://arxiv.org/abs/2607.09426): el desequilibrio predice continuación a 4–12 h, pero solo unos **0,5 pb** por señal.

**Frecuencia.** 8–15 al mes. Con R de 0,4–0,7 % el coste es de 0,15–0,35 R, el perfil que ya murió en las mesas de 15 min. La incluyo solo porque la tarea la pide.

### Líneas descartadas

- **Cobro de funding**: no encontré ningún estudio con efectos de precio en BTC. En el paper del cuarto de hora, quitar los cuartos de hora del cobro no cambia nada. En el tercer trimestre de 2025 el funding estuvo en el 0,01 % el 78 % del tiempo en BitMEX, y Binance usa la misma banda ([Coincub](https://coincub.com/blog/perpetual-futures-funding-rates-78-of-a-quarter-at-0-01/)). El movimiento esperado es de pocos pb en ~1 h, frente a un coste de 0,14 %. Como mucho, sirve de filtro de ejecución.
- **CVD como continuación**: 0,5 pb por señal y Sharpe neto negativo (ver §0).
- Kaiko, Glassnode, CryptoQuant, Coinglass y Binance Research no publican estadísticas de estas señales intradía. Lo que hay son paneles, crónicas de eventos u opinión.

## 3. Tabla resumen

| # | Estrategia | Marco | Lados | Evidencia | Ops/mes (estimadas) | Objetivo / tiempo | Riesgo principal |
|---|---|---|---|---|---|---|---|
| E1 | Rebote tras cascada (4σ + caída del OI) | 1 h | ambos | media (De Nicola; Kitron; Garcia Seuma) | 2–4 | 2R / 4 h | efecto viejo y menguante; deslizamiento en cascadas |
| E2 | Prima extrema + salto de 2σ | 1 h | ambos | media-baja (He et al.) | 1–3 | 2R / 4 h | la brecha es menor que el coste; se solapa con E1 |
| E3 | Squeeze contra el lado abarrotado | 1 h | ambos | baja (anécdotas de proveedores) | 0,5–1,5 | 3R / 4 h | pocas operaciones |
| E4 | Ruptura con el OI cayendo, en contra | 1 h | ambos | baja y contradictoria | 3–6 | 2R / 4 h | los squeezes continúan |
| E5 | Minoristas frente a top traders | 1 h | ambos | muy baja | 2–4 | 2R / 4 h | agujero de 2022; es momentum disfrazado |
| E6 | Absorción | 15 min | ambos | en contra | 8–15 | 2R / 4 h | costes |

## 4. Top-3 y recomendación

1. **E1**: es la única con números publicados de reversión tras shocks y un mecanismo medible (desapalancamiento forzado) que no está en lo ya probado.
2. **E2**: el mecanismo está bien documentado (vida media de 1,68 h y flujo de arbitraje), aunque la parte direccional es una inferencia.
3. **E3**: es la pareja lógica de E1 (entrar al principio del squeeze, no al final) y va con objetivo 3R, en línea con lo que mejor ha funcionado («dejar correr»).

**Recomendaciones**
- Prerregistrar solo E1–E3, con la regla «create_time + 10 min».
- Añadir antes un test de causalidad: truncar las métricas en T y comprobar que no cambia ninguna señal anterior a T.
- Informar como diagnóstico, no para elegir: resultado por lado, versión sin filtro de OI y sensibilidad a +15/+20 min.
- Lo honesto es esperar que, como mucho, una de las tres pase las puertas.
