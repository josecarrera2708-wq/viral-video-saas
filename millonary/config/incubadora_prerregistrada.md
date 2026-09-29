# Incubadora de traders · Prerregistro (v1) — fijado ANTES de ejecutar nada

Fecha: 2026-09-29. Inspirada en la incubadora de Conesa (traders-estrategia en simulado, capital por mérito), bajo el protocolo de Millonary.
No se cambia nada de este documento tras la primera ejecución; cualquier variante nueva es una prueba nueva en `reports/registro_pruebas.md`.

## Universo (N = 15 traders, parámetros FIJOS, sin optimizar; posición ∈ {−1, 0, +1} sobre BTCUSDT 4h)
S01 Parabolic SAR (0,02/0,2) + EMA200 · S02 Ichimoku (9/26/52) · S03 Bollinger(20,2)+RSI(14) reversión ·
S04 Keltner (EMA20 ± 2·ATR10) ruptura · S05 RSI(2)<10 sobre SMA200, largo · S06 cruce SMA 7-25 (largo/corto) ·
S07 cruce SMA 7-25 + filtro SMA200 (solo largo) · S08 canal de 20 velas por tercios · S09 Donchian 20/10 ·
S10 MACD(12,26,9)+EMA200 · S11 Supertrend(10,3) · S12 expansión de volatilidad (ATR14>SMA50 del ATR) + momentum 12 velas ·
S13 retroceso a EMA20 en tendencia (EMA50>EMA200) · S14 momentum 90 d (largo/corto) · S15 RSI14 (55/45) + EMA200.
Señal al cierre de la vela i → posición en la vela i+1. Tamaño 1× fijo (sin vol-target) para compararlos.
Costes 7 pb por unidad de rotación; funding real del perpetuo (los largos pagan, los cortos cobran) desde 2020.

## Periodos
Datos 2020-01-01 → 2025-06-30 (el ciego 2025-07+ está consumido y NO se usa para elegir).
Construcción (train): 2020-01-01 → 2023-12-31. **Examen sellado (exam): 2024-01-01 → 2025-06-30, se mira UNA vez.**
Hacia delante (forward): desde 2026-09-29 16:30 UTC, en sombra (misma fecha que la prueba de papel).

## Métricas y contraste
Retornos diarios. Regresión r = α + β_BTC·r_BTC + β_tend·F_tend + ε (errores HAC Newey-West, 5 retardos);
F_tend = signo del retorno a 60 d de BTC (hasta t−1) × r_BTC(t). α anualizado ×365, t-stat.
Corrección por comparaciones múltiples sobre los N=15: Holm (control FWER) y Benjamini-Hochberg sobre el p unilateral (α>0) del EXAMEN.
Deflated Sharpe con n_trials = 15 + 23 (registro previo) y PBO (CSCV) sobre las 15 series diarias.

## Puertas para pasar a "Mesa de estrategias minadas" (capital simulado)
P1 Sharpe en train > 0 · P2 Sharpe en exam > 0 · P3 p unilateral de α (exam) con Holm < 0,10 ·
P4 DSR (2020-2025.06) ≥ 0,80 · P5 ≥ 30 operaciones en total · P6 Sharpe en exam > 0 con costes ×2 · P7 PBO del conjunto < 0,5.
Pasar las 7 = "certificada en histórico". NO significa rentable: entra en sombra hacia delante ≥ 90 días (regla del laboratorio) antes de cualquier capital real.

## Reparto de capital simulado por mérito estadístico (no por el último resultado)
Solo entre certificadas: peso ∝ (1 − p_Holm) / σ_anual (paridad de riesgo ponderada por mérito), tope 25 % por trader, se
descuenta la correlación (peso × (1 − correlación media con el resto), renormalizado). El núcleo v1 es siempre el miembro base.
Si ninguna se certifica, el reparto es 100 % núcleo (resultado válido).

## Meta-etiquetado (regresión logística) con examen final sellado
Solo para traders con ≥ 40 operaciones en train. Características conocidas al abrir (percentil ATR, distancia a EMA200 en ATR, RSI14,
retorno 10 velas, hora). Entrenamiento en train; se decide el umbral (0,5 fijo, no optimizado). Examen: ejecución ÚNICA en exam;
gana solo si mejora el Sharpe del filtrado frente al no filtrado Y el p de la diferencia (bootstrap por operaciones) < 0,10. Cuenta como prueba nueva (por trader).
