# Registro de pruebas (para corregir por comparaciones múltiples)

Cada variante de PROCESO o regla evaluada cuenta, se apruebe o no. Última actualización: 2026-09-29.

| # | Prueba | Resultado |
|---|---|---|
| 1–3 | Minero v1, top 5/10/20 (walk-forward 2022-25) | Sharpe OOS 0,36 / 0,17 / 0,08 |
| 4–8 | 5 reglas canónicas de tendencia | Sharpe OOS 0,79 / 0,98 / 0,73 / 1,17 / 0,08 |
| 9–12 | Minero v2, top 5/10 × bruto/vol-target | Sharpe OOS 0,13–0,31 |
| 13–14 | Conjunto canónico 4h; momentum 20/60/120 d | Sharpe OOS 1,03 / 0,63 (0,75 con vol-target) |
| 15 | **Núcleo v1 prerregistrado** (2017-2025.06) | Sharpe 1,10; 6/6 criterios; ciego +0,9 % dentro de bandas |
| 16 | Variante F (filtro de funding p95) | Rechazada: no reduce la caída |
| 17 | Recorte ×0,5 alrededor del FOMC (2021-2025.06) | **Rechazada**: Sharpe 0,78 → 0,74; −0,85 %/año (IC90 −1,8 % a +0,1 %) |
| 18–23 | 6 variantes de sombra del Laboratorio (exploratorio, 2017-2025.06) | Sharpe 1,00–1,13; ninguna mejora al núcleo por ≥ 0,3 |
| 24–38 | Incubadora: 15 traders (SAR+EMA200, Ichimoku, Bollinger+RSI, Keltner, RSI(2), SMA 7-25 ×2, canal por tercios, Donchian, MACD, Supertrend, expansión de vol., retroceso EMA20, momentum 90 d, RSI14+EMA200); examen 2024-01→2025-06, ejecución única | **0/15 certificadas**; mejor Sharpe exam 1,19 (S07) vs buy&hold 1,47; α no significativo (Holm); PBO 0,31 |
| 39–53 | Meta-etiquetado logístico por trader, examen sellado (una ejecución) | **0 ganan**; el umbral 0,5 fijo veta casi todo (win rate < 50 %); artefacto anotado: la operación abierta antes del examen no se filtra |
| 54–128 | Ciclo de mejora: 5 operadores (filtro EMA200, solo largos, tamaño por volatilidad, stop 3×ATR, parte fuerte del canal) × 15 traders; construcción 2020-23 y validación 2024-25.06 (segunda mirada al examen, anotada) | 21 pasan a sombra hacia delante (sobre todo «solo largos» y «tamaño por volatilidad»); **0 significativas tras Holm** (mejor p_Holm 0,63). «Solo largos» refleja la deriva alcista de BTC 2020-25: exige confirmación hacia delante |
| 129–142 | Mesa intradía: 14 traders de 1 h con stop/TP/tiempo; construcción 2020-23, validación 2024-25.06, examen sellado 2025-07→2026-08 (ejecución única) | **0/14 certificadas**; expectativa en R negativa en el examen en los 14 (−0,05 a −0,23 R por operación); con costes ×2 empeora en todos. Frecuencia 0,3-1,6 ops/día. Causa: el coste de ida y vuelta (≈12 pb) es ≈0,2 R con stops de 1-2 ATR de 1 h |
| 143–212 | Mesa intradía, ciclo de mejora: 5 operadores (tendencia, stops ×2, sesión, stop mínimo, dejar correr) × 14 traders; solo construcción y validación (el examen ya estaba consumido) | 5 pasan a sombra hacia delante (mejoras pequeñas: R valid. +0,05 a +0,09); **0 significativas tras Holm** |

Estrategias únicas minadas (no usadas para elegir el núcleo): ≈ 66.000 (v1 32.304 + 8 ventanas WFO v1 ≈ 113.000 evaluaciones + v2 ≈ 119.000).
El periodo ciego (2025-07 → 2026-08) se abrió UNA vez y está consumido.

## Desviaciones anotadas (no corregidas: ni cambian resultados ni se retocan parámetros)
- La Pata A se decide al cierre diario (00:00 UTC) y se aplica desde la vela de las 04:00 del día siguiente (4 h de retraso extra
  frente a "desde la vela siguiente"). Es igual en backtest y en vivo (revisión Opus, hallazgo 8).
- El freno de pérdida diaria mide la caída intradía desde las 00:00 UTC (máx. histórica 5,8 %), no cierre a cierre (4,7 %).

- Mesa intradía: el test de causalidad detectó que el stop de I01 usaba el rango asiático completo en velas anteriores al cierre de esa sesión (sin efecto en entradas: comprobado que entradas y stops de entrada son idénticos antes y después de la corrección).

## Mesa de 15 min (2026-10-01/02) — pruebas 213-251 (39 variantes: 13 traders base + 26 aprendices A/C)
- Prerregistro `config/mesa15_prerregistrada.md` y código `src/desk15/` confirmados en git ANTES de ejecutar validación y examen. Única enmienda previa: la regla de veto de los aprendices pasó de absoluta (R media < 0) a relativa (peor que la media global), tras una prueba de tubería SOLO sobre construcción que mostró que la absoluta vetaba casi todo.
- Examen sellado 2025-10-01→2026-09-29 ejecutado UNA vez (`reports/mesa15_resultados.md`): **0/13 certificadas**; los 13 con R media negativa en construcción, validación y examen (costes ≈ −0,3 R por operación con stops de ≈ 0,4 %); 20 de 26 aprendices reducen la pérdida de su base en validación y examen con ≥ 30 operaciones, pero siguen negativos (aprender a evitar los peores contextos no crea ventaja donde no la hay).
- Tests: `tests/test_desk15.py` (causalidad de los 13 setups por truncamiento, veto causal del aprendiz, paginación de datos, funding por vela).
- Hacia delante: inicio 2026-10-02 00:00 UTC, rutina horaria compartida con la mesa de 1 h.

## 2026-10-02 · Mesa de 1 h (13 traders ÷4) y anchura del stop
- Stop ×1,5 / ×2,0 (mesa 15 min, validación): R media −0,31 → −0,19 / −0,14; mesa 1 h: −0,16 → −0,09 / −0,07. Mejor en 12-13 de 13 traders, pero todo sigue negativo; el examen confirma (segunda mirada en 15 min). Informe: reports/mesa15_stops.md, mesa1h_stops.md. Nada adoptado.
- Mesa 1 h: 0/13 certificadas (examen R −0,27 … 0,00; mejor Q01 R 0,00, P07 −0,03); 5 aprendices mejoran a su base (P01·C, P02·A, P03·C, P04·A, P04·C), hipótesis. reports/mesa1h_resultados.md.

## 2026-10-02 · Mesa de fondos (estrategias célebres) — pruebas 252-261
- Prerregistro `config/fondos_prerregistrada.md` + código `src/fondos/` en git (b366d91) ANTES de ejecutar sobre datos reales. Parámetros de sus autores, sin ajuste.
- **Corrección de un error de datos tras la 1.ª ejecución (anotada, sin tocar reglas ni umbrales):** el empalme de feb-2018 copiado del núcleo reescalaba el contado ×0,89 desde 2018-02-11. Para el carry (contado frente a perpetuo) eso creaba una beta oculta de −0,11 (corr. −0,74 con el núcleo, imposible en una estrategia neutral), y en la rutina habría metido un salto falso del 12 % al empalmar datos nuevos. Ahora se usan precios reales con el hueco relleno plano. F01-F05 y F07-F09 salen iguales; cambian F06 y F10. Resultados de la 1.ª ejecución guardados en el historial de git del informe.
- Resultado (`reports/fondos_resultados.md`, 2018-09→2026-10): **1/10 certificada: F06 carry de funding** (Sharpe 7,0; +10,9 %/año; caída 3 %; corr. con el núcleo −0,02; mezcla 50/50 en riesgo con el núcleo: Sharpe 4,6 vs 1,0). Por años: 2020 +17 %, 2021 +34 %, 2022 +1 %, 2023 +7 %, 2024 +12 %, 2025 +5 %, 2026 +0,1 % (el funding se ha comprimido). Riesgos fuera del dato: quiebra del exchange (FTX 2022), desapalancamiento automático, margen del corto en subidas bruscas.
- Las 9 restantes no certifican: Tortugas S1 0,42 / S2 0,18, momentum 12 m 0,37, media 200 d 0,72 (caída 68 %), Williams 0,69 (cae a 0,07 con costes ×2), Moreira-Muir 0,52 (caída 95 %), Turtle Soup −1,32, NR7 0,59 (0,09 con costes ×2), multiestrategia 0,24. Ninguna supera al núcleo v1 (1,04, caída 25 %): el núcleo ya es la versión diversificada de la tendencia (Tortugas + momentum + volatilidad objetivo).

## 2026-10-03 · Gestor de cartera (Fase 1) — pruebas 262-265
- Prerregistro `config/cartera_prerregistrada.md` + código `src/cartera/` en git (1fbdc58) ANTES de ejecutar. Bolsillos: núcleo v1 + F01-F09.
- Resultado (`reports/cartera_resultados.md`, 2020-01→2026-10): **1/4 aprobada: K4 HRP de los 10 bolsillos + control de caída** (Sharpe 4,5; +6,7 %/año; caída 2 %). K1 paridad núcleo+carry (Sharpe 2,5; +11 %/año; caída 9 %) y K2 HRP (2,7; +10,9 %; 5 %) fallan solo G1 (p Holm 0,14). K3 50/50 + control: 1,31, peor que sin control (1,50).
- Lo que dicen: cualquier reparto por riesgo pone ~92-99 % en el carry → más estable pero MENOS rentable que el núcleo solo (+18 %/año, caída 25 %). El 50/50 en capital que corre en papel (+14,8 %/año, caída 11 %, Sharpe 1,5) es el mejor equilibrio rentabilidad/riesgo; no es una prueba (referencia).
- Anotado: la fórmula prerregistrada del control (⌊(1 − DD/20 %)/0,25⌋·0,25) baja a 0,75 con CUALQUIER caída > 0 (no solo desde el 5 %): actúa como un desapalancamiento casi permanente (K3 reducido el 94 % de los días, K4 el 59 %). No se corrige: cambiarlo sería una prueba nueva.
- PBO (CSCV): familia {N, K1-K4} 0,34; F01-F09 sin carry 0,76 (elegir la «mejor» estrategia célebre por su historial es casi siempre sobreajuste).
- K4 en papel desde 2026-10-03 con 1.000 USDT (`src/cartera/forward.py`, rutina diaria).

## 2026-10-03 · Fase 2, lote 1: primas de riesgo — pruebas 266-269
- Prerregistro `config/primas_prerregistrada.md` + código `src/primas/` en git (f991bd0) ANTES de ejecutar. Datos nuevos: 25 trimestrales BTCUSDT USDT-M (Binance Vision 1 h, 2021-02→hoy) y DVOL de Deribit (2021-03→hoy).
- Resultado (`reports/primas_resultados.md`): **0/4 certificadas**. B01 basis hasta vencimiento (Sharpe 1,28; +6,8 %/año; caída 7 %; 21/21 vencimientos con ganancia), B02 con salida anticipada (1,32; +7,0 %) y V01 venta de varianza (1,58; +9,4 %; caída 8 %; peor día −4,7 %; 2026 −5,4 %) pasan 4/5 y fallan SOLO el Deflated Sharpe (0,59 / 0,62 / 0,74 < 0,80 con n = 269). V02 (filtro IV > RV) 1/5: el filtro empeora (Sharpe 0,63; negativa con costes ×2).
- Diagnóstico: correlación con el carry de funding ≈ 0 y con el núcleo −0,1 a −0,4; como tercer bolsillo suben la paridad núcleo+carry (B01 4,95 → 5,49; V01 2,51 → 5,06).
- B01, B02 y V01 se siguen hacia delante EN SOMBRA (`src/primas/forward.py`, rutina diaria, inicio 2026-10-03): solo evidencia; no entran en la cartera.

## 2026-10-03 · Fase 2, lote 2: entrada maker (orden límite) — pruebas 270-309
- Prerregistro `config/maker_prerregistrada.md` + código `src/maker/` (copia del motor; el original intacto, con test) en git (d2c5038) ANTES de ejecutar.
- Resultado (`reports/maker_resultados.md`): **0/40 certificadas**. Llenado 94 %; el maker mejora la R en validación y examen en 32/40, pero solo ≈ +0,04 R por operación (examen: −0,207 → −0,168 de media). Traders con R > 0 en el examen: 1 → 2 (mesa1h P07 +0,003 y Q01 +0,016, no significativas). Con costes ×2 todas negativas.
- Conclusión: la comisión explica ≈ 20 % del problema; el resto es falta de ventaja en las señales de corto plazo. Nada pasa a papel.

## 2026-10-03 · Acumulación de BTC (decisión del dueño) — pruebas 310-313 (exploratorias)
- Petición del dueño: reunir el máximo de BTC. Mezclas de BTC con núcleo y carry vistas ANTES del prerregistro, sin prerregistrar: ⅓ cada uno, 50 % BTC/50 % carry, 25/25/50 y 50/25/25 → pruebas 310-313, para que cuenten en el n. Medido en BTC (2020→hoy, por cada BTC inicial): 100 % BTC 1,00; 50/50 0,60; 50/25/25 0,59; ⅓ 0,47; 25/25/50 0,39.
- Prerregistro `config/acumulacion_prerregistrada.md` + código `src/acumulacion/` en git ANTES del inicio en papel (compra al cierre del 2026-10-03). A1 100 % BTC APLICADA; A2 50/25/25 en sombra. No certifica nada (sin puertas).
- Añadida A3 (núcleo + carry 50/50 que convierte en BTC sus ganancias ≥ 10 USDT a fin de mes; copia aparte) antes del inicio, por petición del dueño. Sin puertas.

## 2026-10-04 · Revisión a petición del dueño (sin pruebas nuevas)
- Fallo encontrado en el post-mortem de la mesa intradía: la EMA de 800 h necesita 800 velas y el papel solo carga 420 de calentamiento, así que la tendencia salía vacía y TODAS las operaciones se marcaban «contra la tendencia de fondo». Corregido: ahora queda vacío (sin lección) mientras no haya datos. No cambia ninguna entrada, stop, TP ni resultado; solo las lecciones.
- Pérdidas en papel coherentes con los históricos ya registrados (0/14, 0/13, 0/13 certificadas, R esperada negativa). En papel: mesa 15 min R −0,44/op (costes ≈ 0,45 R/op con stops del 0,22 %); 1 h −0,47; intradía +0,03.

## 2026-10-05 · Búsqueda v2: acción de precio a favor de tendencia en 15 min/1 h/4 h/diario — pruebas 314-1081 (768 variantes)
- Prerregistro `config/busqueda_v2_prerregistrada.md` + código `src/busqueda/` (test de causalidad por truncamiento y tubería sintética) confirmados en git (4b3dca6) ANTES de ejecutar sobre datos reales.
- Resultado (`reports/busqueda_v2_resultados.md`, ejecución única): **0/768 certificadas**. 176 elegibles; 20 finalistas al examen (19 de 4 h, 1 de 1 h): 7 con R > 0 en el examen, 3 sobreviven a costes ×2 (4 h barra interior solo largos con stop 2-3 ATR y TP 3-5R: +0,24 a +0,33 R), pero solo 0,05-0,07 ops/día (≈ 23 en el examen) → p Holm 1,00 y DSR 0,00 con 768 pruebas.
- Marginales (R construcción / validación): 15 min −0,34/−0,23 · 1 h −0,03/+0,02 · 4 h +0,20/+0,12 · diario +1,05/+0,15; solo largos +0,33/+0,03 frente a ambos +0,11/−0,00; stop 2-3 ATR mejor que 1 ATR en validación; TP2 −0,04/−0,05 · TP5 +0,07/+0,03 · «dejar correr» +0,84/+0,10. Lectura: cuanto más alta la temporalidad, más amplio el stop y más largo el objetivo, mejor; en 15 min ninguna combinación funciona. Nada pasa a papel sin decisión del dueño.

## 2026-10-05 · Búsqueda v3: fondos, investigadores y traders conocidos — pruebas 1082-1109 (28 variantes)
Prerregistro: `config/busqueda_v3_prerregistrada.md` (commit fa079ef, ANTES de ejecutar). Resultados: `reports/busqueda_v3_resultados.md`.
- Variantes: 28. Elegibles: 4. Certificadas: **0**.
- Estrategias publicadas que NO aguantan costes en BTC 2024-2026:
  - Estacionalidades (lunes de Asia, noche de Wall Street, 21-23 UTC), con R ≤ 0 en validación.
  - Zona de ruido de Zarattini, con −0,09 R en el examen.
  - RSI(2) de Connors e IBS.
- Lo mejor del examen:
  - Conjunto de tendencias CTA 4 h: +0,09 R, 42 ops, +2,5 %.
  - MAX(20) diario: +0,035 R.
  - Ninguno es significativo (p Holm 1,0; DSR ≈ 0).
- Weinstein, máximos anuales y CTA diario tienen R alto pero muy pocas operaciones (5-9 en validación). No se pueden certificar.
- Total acumulado del proyecto: 1.109 pruebas.
- Mesa nueva (X01-X09) creada por la regla prerregistrada. Arranca en papel el 2026-10-06 00:00 UTC.

## 2026-10-05 · Búsqueda v4: patrones chartistas, velas japonesas e ineficiencias — pruebas 1110-1517 (408 variantes)
Prerregistro: `config/busqueda_v4_prerregistrada.md` (commit c78a456, ANTES de ejecutar). Resultados: `reports/busqueda_v4_resultados.md`.
- Variantes: 408. Elegibles: 31. Al examen: 20. Certificadas: **0**.
- Aun así es la mejor tanda del proyecto: 12 de las 20 finalistas ganan en el examen, también con costes ×2.
- Mejores del examen:

| Variante | Ops | Acierto | R examen | Retorno | p Holm |
|---|---|---|---|---|---|
| Bandera 4 h, TP 2R | 23 | 65 % | +0,80 | +9,1 % | 0,12 |
| Bandera 4 h, TP 3R | 22 | 64 % | +0,73 | +8,4 % | 0,44 |
| Cuatro velas seguidas 4 h, TP 2R | 76 | — | +0,38 | +13,9 % | 0,14 |
| Triple suelo/techo 1 h, dejar correr | 82 | — | +0,48 | +16,7 % | — |
| Doble suelo 1 h a favor de tendencia | — | — | +0,28 | — | — |

- Ninguna pasa Holm ni DSR (n_trials = 408).
- Un «acierto» alto con TP 1R (≈50-70 %) NO da beneficio por sí solo. La mejor salida media fue «dejar correr»: +0,55 / +0,14 R, con un acierto del 30 %.
- Malos en BTC:
  - Triángulo descendente.
  - HCH.
  - Estrella de la mañana/tarde en 1 h.
  - Velas en 1 h en general (−0,08 R de media).
- Mesa de patrones (Y01-Y07) creada por la regla prerregistrada. Empieza el 2026-10-06 00:00 UTC.
- Repetición con datos de Deribit desde 2025-07: coincide con el examen de Binance. Y04 bandera +0,74 R; Y01 doble suelo +0,26 R.
- Total acumulado del proyecto: 1.517 pruebas.

## 2026-10-05 · Búsqueda v5: patrones ligados a una confirmación + cuñas — pruebas 1518-1685 (168 variantes)
Prerregistro: `config/busqueda_v5_prerregistrada.md` (commit 134d411, ANTES de ejecutar). Resultados: `reports/busqueda_v5_resultados.md`.
- Variantes: 168. Elegibles: 21. Certificadas: **0**.
- Media en validación de cada confirmación, frente a +0,024 R sin confirmación:

| Confirmación | R en validación |
|---|---|
| Barrido de liquidez | +0,104 |
| FVG | +0,042 |
| Volumen | +0,032 |
| Tendencia superior | +0,029 |
| Divergencia RSI | −0,038 |
| Compresión | −0,075 |

- En el examen, el triple suelo/techo 1 h dejar correr ganó con varias confirmaciones:

| Confirmación | Ops | R examen | Retorno |
|---|---|---|---|
| Compresión | 40 | +0,87 | +14,7 % |
| Volumen | 59 | +0,59 | +14,9 % |
| Tendencia superior | 43 | +0,57 | +10,2 % |

- Doble suelo + barrido de liquidez: +0,35 R. Doble techo: flojo con cualquier confirmación. Cuña: sin ventaja.
- Mesa de trading: entran Z01 (doble suelo + tendencia superior, +0,15 R en el examen) y Z02 (triple + tendencia superior, +0,57 R). Z de doble techo + tendencia superior: fuera (−0,09 R en el examen).
- Total acumulado del proyecto: 1.685 pruebas.

## 2026-10-05 · Búsqueda v6: más combinaciones de patrones — pruebas 1686-1797 (112 variantes)
Prerregistro: `config/busqueda_v6_prerregistrada.md` (commit 1581163, ANTES de ejecutar). Resultados: `reports/busqueda_v6_resultados.md`.
- Variantes: 112. Elegibles: 24. Certificadas: **0**.
- **18 de 20 finalistas ganan en el examen**, todas también con costes ×2 menos dos.
- Mejores combinaciones en validación:

| Combinación | R en validación |
|---|---|
| Tendencia + funding | +0,27 |
| Funding a contrapié | +0,17 |
| Tendencia + volumen | +0,07 |
| Compresión doble | −0,10 / −0,14 |

- Mejores del examen:

| Variante | Ops | R examen | Retorno |
|---|---|---|---|
| Bandera 1 h + funding a contrapié | 41 | +1,04 | +17,4 % |
| Triple + volumen + compresión | 30 | +1,02 | +13,3 % |
| Triple + tendencia + volumen | 32 | +0,75 | +10,5 % |
| Triple con entrada en retesteo | 58 | +0,52 | +12,7 % |

- Ninguna pasa Holm ni DSR.
- Mesa de trading: entran W01-W04 por la regla prerregistrada. En la repetición con datos de Deribit desde 2025-07 ganan los cuatro, pero W01 (+0,08 R) y W03 (+0,22 R) ganan menos que con Binance: el funding y el volumen difieren entre bolsas.
- Total acumulado del proyecto: 1.797 pruebas.
