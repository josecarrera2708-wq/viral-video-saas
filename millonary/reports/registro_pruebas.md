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
