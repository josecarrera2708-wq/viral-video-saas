# Contexto común para los agentes (léelo entero)

Proyecto **Millonary**: fondo de trading en PAPEL, solo BTC (perpetuo BTCUSDT). Repo: /home/user/viral-video-saas/millonary.
- Para ti el repo es de SOLO LECTURA: no modifiques ni crees archivos dentro, no hagas commits ni push.
- Nada de dinero real.
- Todo se prerregistra en git ANTES de evaluar. Por eso NO hagas backtests ni mires resultados de estrategias con nuestros datos de BTC: eso lo hará el coordinador después del prerregistro. Sí puedes: buscar en la web (WebSearch/WebFetch), leer código del repo, y hacer cálculos o simulaciones con datos SINTÉTICOS.

## Lo que pide el dueño
Estrategias intradía de BTC con operaciones de 15 min a 3-4 h, con relación beneficio/riesgo 2:1 o 3:1 (stop = 1R, objetivo = 2R o 3R),
que ganen dinero de verdad tras costes, idealmente con más operaciones ganadas que perdidas. Tiene poco capital y quiere hacerlo crecer.

## Datos disponibles (no propongas nada que necesite otros datos)
- Velas del perpetuo BTCUSDT de Binance de 5 min, 15 min, 1 h y 4 h desde 2020-01: OHLC, volumen, nº de operaciones, volumen comprador agresor (taker buy).
- Contado BTCUSDT 15m/1h/4h/1d desde 2017.
- Funding cada 8 h (00, 08, 16 UTC) desde 2019; índice de prima (premium index) 1 h.
- Métricas cada 5 min desde 2020-09: open interest, ratio largo/corto de top traders y de cuentas, ratio de volumen taker comprador/vendedor.
- Diario: Fear & Greed, FRED (tipos, VIX, dólar).
- NO hay libro de órdenes, ni ticks, ni liquidaciones, ni datos de CME, ni noticias históricas.

## Motor y costes
- Señal al cierre de la vela; entrada en la apertura de la siguiente. Stop en precio; objetivo en múltiplos de R; salida por tiempo.
- Costes: taker 0,05 % por lado, maker 0,02 %, deslizamiento 2 pb por lado → ida y vuelta a mercado ≈ 0,14 %.
- Con stops intradía de 0,3-0,5 % eso son 0,3-0,45 R por operación. El proyecto ya comprobó que en 15 min casi todo muere por costes
  (R media −0,3 en 13 setups; en 1 h −0,05 a −0,23 R). Cualquier propuesta debe explicar cómo sobrevive a esto
  (stop más ancho, entrada/salida con orden límite maker, menos operaciones pero mejores…).

## Protocolo de evaluación
- Construcción 2020-03→2024-01, validación 2024-01→2025-07, examen 2025-07→2026-09.
- Puertas: R>0 con ≥20 ops, Holm p<0,10, R>0 con costes ×2, caída <30 %, DSR ≥0,80.

## YA PROBADO (no repetir tal cual; si propones algo parecido, explica qué cambia y por qué)
ruptura del rango asiático, Donchian 24 h, Bollinger+RSI, VWAP z-score a la media, cruce EMA 9/21 + EMA200, RSI(2) Connors, squeeze Bollinger/Keltner,
IBS, envolvente en S/R, pin bar en techo/suelo, barrido de liquidez (rompe máx/mín de 96 velas y cierra dentro), reentrada a FVG, barra interior,
estrella de la mañana/tarde, doble/triple techo-suelo, HCH, triángulos, cuñas, banderas, tazas, zona de ruido de Zarattini (ORB intradía),
estacionalidades horarias (lunes Asia, noche de Wall Street, 21-23 UTC), MAX/MIN de n días, CTA/tendencia, Weinstein, momentum de series temporales,
expansión de volatilidad, filtros de tendencia/volumen/funding/horario/RSI, y meta-etiquetado logístico simple con umbral 0,5.
Lo que mejor salió: patrones en 1 h/4 h con stop amplio y «dejar correr» (acierto 21-36 %, +0,3 a +1,1 R por operación en el examen); ninguno certificado.
2.044 pruebas acumuladas.

## Entrega
Informe en ESPAÑOL, en markdown, de no más de ~2.500 palabras. Guárdalo en el archivo que te indique tu tarea y devuélvelo también como respuesta final.
Cita fuentes con URL. Distingue claramente evidencia publicada con números de opinión o marketing de traders.
