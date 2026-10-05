# Búsqueda v2 · acción de precio a favor de la tendencia, 4 temporalidades (prerregistro)

Fecha: 2026-10-05. Petición del dueño: revisar desde cero, buscar estrategias de acción de precio que funcionen, y averiguar con datos de años anteriores dónde va el stop, dónde el TP y en qué temporalidad (15 min, 1 h, 4 h, diario; en temporalidades mayores, stops y TP más amplios buscando movimientos largos).
Este documento y el código (`src/busqueda/`) se confirman en git ANTES de ejecutar sobre datos reales. Pruebas 314-1081 del registro (768 variantes).

## Por qué este diseño
Diagnóstico de las mesas actuales (registro 2026-10-04): pierden sobre todo (1) operando contra la tendencia y (2) con stops estrechos donde las comisiones se comen ≈0,3-0,45 R por operación. Aquí TODO opera a favor de la tendencia (EMA200 y EMA50) y se prueban stops amplios y objetivos largos.

## Rejilla (fija, sin ajuste posterior)
- Temporalidades: 15 min (Deribit, 2022-07→), 1 h y 4 h (Binance perpetuo, 2020→), diario (de las velas de 1 h).
- Tendencia: alcista = cierre > EMA200 y EMA50 > EMA200 (bajista al revés). S6 solo exige cierre vs EMA200.
- 6 setups: S1 ruptura del máx./mín. de 20 velas; S2 retroceso a la EMA20 con vela de rechazo; S3 barra interior rota; S4 envolvente cerca de la EMA20; S5 pin bar cerca de la EMA20; S6 cruce EMA 9/21.
- Modo: ambos lados / solo largos.
- Stop: 1, 2 o 3 × ATR(14) desde la entrada, o estructural (mín./máx. de 10 velas ± 0,1 ATR, limitado a 0,5-4 ATR).
- Salida: TP 2R, 3R o 5R con salida por tiempo (15 min 96 velas = 1 día; 1 h 72 = 3 días; 4 h 42 = 7 días; diario 20 días), o «dejar correr» sin TP ni tiempo: sale al cerrar al otro lado de la EMA50.
- Motor y costes reales del proyecto (taker 0,05 %, maker 0,02 % en TP, deslizamiento 2 pb, funding real), riesgo 0,5 % por operación, 1.000 USDT.

## Periodos
- 1 h / 4 h / diario: construcción 2020-03→2024-01, validación 2024-01→2025-07, examen 2025-07→2026-09-28.
- 15 min: construcción 2022-07→2024-07, validación 2024-07→2025-07, examen 2025-07→2026-09-28.
- Aviso honesto: 2025-07→2026-09 ya se usó como examen de OTRAS reglas (mesas intradía/15 min/1 h). Para estas 768 reglas nuevas no se ha mirado nunca, pero no es un periodo de mercado «virgen».

## Selección (una sola ejecución)
1. Construcción y validación para las 768 variantes.
2. Elegibles: R media > 0 en construcción Y en validación, y ≥ 30 operaciones en validación.
3. Finalistas: las 20 elegibles con mayor t de R en validación. SOLO ellas se miran en el examen.

## Puertas (todas para certificar)
- G1 R media > 0 en el examen con ≥ 20 operaciones.
- G2 p unilateral de R en el examen, corregida por Holm entre las 20 finalistas, < 0,10.
- G3 R media > 0 en el examen con costes ×2.
- G4 caída máxima en el examen < 30 % y sin liquidación.
- G5 Deflated Sharpe ≥ 0,80 (retornos diarios de construcción+validación, n = 768 pruebas).

## Qué se hará con el resultado
- Certificada(s) → pasan a papel en una mesa nueva (no se tocan las mesas en marcha). Nada de dinero real sin aprobación EXPRESA del dueño.
- Ninguna certificada → se informa tal cual, con la tabla de marginales (qué stop, qué TP, qué temporalidad y qué setup rinden mejor de media), sin reajustar la rejilla con el examen ya visto.
