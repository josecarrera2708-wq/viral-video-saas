# Sesión del comité · 2026-10-06 04:18 UTC

**Estado general:** 🟢 OK
**Decisión:** Mantener el objetivo del núcleo: 0.65× de exposición.
**Principio:** los agentes analizan y recomiendan; la operativa la fija el núcleo validado y solo Riesgos puede vetar.


## 🟢 Riesgos — Operativa permitida · exposición 0.59× · caída 0.0%
- Distancia a los frenos: caída 0.0% de 30%; pérdida diaria 0.0% de 7%.
- Exposición 0.59× (tope efectivo 2.0×; el 5× del exchange no se usa).
- Liquidación (margen cruzado): el precio tendría que moverse ≈ 168% en contra; con esta exposición un gap de -50% costaría -30% del capital.

## 🟢 Macroeconomía — Entorno NORMAL
- Fear & Greed 73 (codicia).
- VIX 15.3 (percentil 15% del último año).
- Curva 10a-2a: +0.45 pp; 10a 5.28%.
- Dólar (índice amplio) +0.6% en 50 días.
- Funding actual 0.0100% por 8h (percentil 96% del último año); media 30d anualizada 5.5%.
- Próximo evento: FOMC (alto) 2026-10-28 18:00 UTC, en 542 h.
- Regla histórica probada: recortar la exposición alrededor del FOMC EMPEORÓ el núcleo (Sharpe 0,78 → 0,74; rechazada). Solo se informa, no se actúa.

## 🟢 Análisis de mercados — Tendencia alcista (3/4 horizontes)
- Momentum por horizonte: 20d +10.7%, 60d +33.8%, 120d +42.1%, 250d -3.0% → 3/4 positivos.
- Ruptura Donchian-50 (4h): LARGO.
- Precio +20.9% sobre la SMA200 diaria; SMA50 > SMA200.
- Volatilidad (ATR 4h) 0.78% del precio, percentil 5% del último año.
- Estructura: último máximo confirmado 87,250 (+1.1 ATR), último mínimo 84,475 (-3.0 ATR).
- Patrones de velas recientes (informativo, sin ventaja probada): engulfing alcista, harami bajista, tweezers bajista.

## 🟢 Gestión de cartera — Objetivo 0.65× · actual 0.59×
- Señal = 0,5·A(0.75) + 0,5·B(1) = 0.875.
- Volatilidad anual (EWMA 45d) 34% → escala mín(2; 25%/σ) = 0.74.
- Exposición objetivo 0.65× frente a 0.59× actual (banda ±20%) → sin cambios necesarios.
- Coste de funding estimado a esta exposición: +3.24% anual del capital.
- Cuenta pequeña: el lote mínimo (86 USDT) es el 8% del capital; el objetivo se redondea a ese paso.

## 🟢 Mesa de trading — 1 órdenes · 1 lotes abiertos
- 1 órdenes ejecutadas (comisiones 0.29 USDT). Modelo de costes: 5 pb comisión + 2 pb deslizamiento por lado.
  2026-09-29 20:00 BUY 0.0070 BTC @ 83,579.1 (BANDA)
- Lotes abiertos: 1 (no realizado +19.62 USDT). Cuadre del diario: OK.

## 🟢 Derivados y arbitraje — Carry teórico +5.5% anual (investigación)
- Funding anualizado: 30d +5.5%, 1 año +3.3%.
- Carry teórico 'cash-and-carry' (largo spot + corto perpetuo): ≈ 5.5% anual bruto a 30d; el coste de montar y desmontar es ≈ 4 × 5 pb = 0,20 % y exige capital en spot y margen en el perpetuo.
- ESTADO: INVESTIGACIÓN. No se opera: requiere ejecución en dos mercados y gestión del riesgo de contraparte; se evaluará como pata aparte con su propio protocolo.

## 🟢 Laboratorio (cuantitativo / ML) — 6 variantes en sombra · 5 días de prueba
- Todas las variantes arrancan planas el 2026-09-29 16:30 UTC; 5 días hacia delante.
  solo pata A (momentum diario): retorno +1.8% · caída 1.3% · Sharpe n/d → sin evidencia (faltan días)
  solo pata B (Donchian 50): retorno +2.3% · caída 1.7% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 20 %: retorno +1.6% · caída 1.2% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 35 %: retorno +2.9% · caída 2.1% · Sharpe n/d → sin evidencia (faltan días)
  horizontes cortos (10/20/40/60d): retorno +2.5% · caída 1.6% · Sharpe n/d → sin evidencia (faltan días)
  horizontes largos (60/120/250/365d): retorno +1.8% · caída 1.3% · Sharpe n/d → sin evidencia (faltan días)
- Contexto histórico de cada variante (2017-2025-06, solo exploratorio) en reports/lab_historia.json; cada una cuenta como prueba en el registro.
- Regla de promoción: ≥ 90 días hacia delante, Sharpe ≥ núcleo + 0,3, caída ≤ 1,2× la del núcleo, embudo de robustez superado.

## 🟢 Incubadora de traders — 15 traders en sombra · 0 certificadas · 6 días
- Histórico (examen 2024-01→2025-06, 15 traders): certificadas 0/15 · PBO del conjunto 0.31. Mejor Sharpe en examen ≈ 1.19 (buy&hold 1.47); menor p (Holm) del α = 1.00.
- Reparto de capital simulado por mérito: núcleo v1 100%.
- Mesa de estrategias minadas: vacía (ninguna certificada; el capital sigue 100 % en el núcleo).
- Ranking hacia delante (6 días, sombra; sin capital, sin valor estadístico hasta ≥ 90 días):
  S14 Momentum 90 d: +3.35% · caída 2.4% · 1 ops · posición +1
  S07 SMA 7-25 + filtro 200 (largo): +2.99% · caída 2.4% · 1 ops · posición +1
  S06 Cruce SMA 7-25: +2.47% · caída 2.4% · 2 ops · posición +1
  S13 Retroceso a EMA20: +2.21% · caída 2.4% · 2 ops · posición +1
  S15 RSI14 + EMA200: +2.08% · caída 2.4% · 1 ops · posición +1

## 🟢 Mesa de opciones — IV 34% vs RV 31% · put 10 % OTM 0.60%
- Vencimiento a 24.2 días: volatilidad implícita ATM 33.6% · realizada 30 d 30.8% · prima +2.8 pts.
- Sesgo 25Δ (puts − calls): +0.7 pts. Put 10 % por debajo (K≈77,000): cuesta 0.60% del nocional.
- Prima de volatilidad normal.
- ESTADO: solo informa. La protección de cola no se activa: no se puede validar con histórico (sin datos históricos de opciones).

## 🟢 Mesa intradía — 72 operaciones · 4 abiertas
- 14 traders en papel · 72 operaciones cerradas (11.6 al día entre todos) · 4 posiciones abiertas.
- Datos: Deribit BTC-PERPETUAL 1 h (velas cerradas), última vela cerrada 2026-10-05 21:00 UTC.
  I13 Parabolic SAR + EMA200: +1.19% · 5 ops · R total +3.12
  I02 Ruptura Donchian 24 h: +1.10% · 6 ops · R total +2.71
  I07 Ruptura tras squeeze: +0.93% · 3 ops · R total +2.56
- El histórico 2020-2026 da expectativa negativa tras costes en los 14 (0/14 certificadas): esta prueba mide si se confirma hacia delante.

## 🟢 Escuela — 0 lotes cerrados analizados · 0 categorías débiles
- Sin lotes cerrados
- Aún no hay lotes cerrados con contexto suficiente para clasificar.
- Con muestras < 20 estas cifras son ANECDÓTICAS: se muestran para acumular evidencia, no para cambiar reglas.

## 🟢 Infraestructura — Sano · datos hace 28.3 h
- Última vela cerrada a las 2026-10-05 00:00 UTC (hace 28.3 h) · fuente: Binance Vision.
- Base de datos: ok.
- Incidencias en 7 días: 0.
- Disco libre 29.0 GB.

## Organigrama (estado real frente a la idea original)

| Departamento | Estado | Qué hace realmente |
|---|---|---|
| Dirección (comité) | ACTIVO | Reúne los informes y redacta la sesión. No decide la operativa. |
| Riesgos | ACTIVO · con VETO | Capa determinista: exposición máx., pérdida diaria, caída máx., kill switch, datos no fiables. |
| Macroeconomía | ACTIVO (informa) | Fear&Greed, VIX, curva, dólar, funding y calendario FOMC. CPI/empleo: falta fuente (BLS bloquea el acceso automático). |
| Vigilancia de noticias (Fed, Trump, cuentas clave) | PENDIENTE | Requiere un proceso 24/7 y fuentes: los RSS de la Fed son accesibles; X/Truth Social exigen API de pago. Entrará en modo sombra. |
| Análisis de mercados | ACTIVO (informa) | Tendencia por horizonte, estructura, volatilidad, patrones de velas (sin ventaja probada). |
| Mesa de trading | ACTIVO en papel | Ejecución simulada con costes, diario de lotes y posiciones. Dinero real: solo tras el protocolo. |
| Gestión de cartera | ACTIVO | Volatility targeting, banda de rebalanceo, coste de funding. |
| Derivados y arbitraje | INVESTIGACIÓN | Carry teórico cash-and-carry. No se opera. |
| Coberturas | NO APLICA por ahora | El sistema se 'cubre' saliendo a efectivo; las estrategias con cortos no mejoraron fuera de muestra. |
| Mesa intradía (papel) | ACTIVO en papel | 14 traders con stop/TP/tiempo sobre velas de 1 h (Deribit), 1.000 USDT virtuales cada uno; actualización horaria. Histórico: 0/14 certificadas. |
| Opciones | ACTIVO (solo informa) | Deribit público: IV vs RV, sesgo 25Δ y coste de un put 10 % OTM. No se opera con opciones; protección de cola desactivada (sin histórico). |
| Incubadora de traders / Estrategias minadas | ACTIVO en sombra | 15 traders-estrategia con atribución alfa/beta, corrección por comparaciones múltiples y examen sellado; capital simulado solo por mérito. 0/15 certificadas en el examen. |
| Cuantitativo / Machine learning | ACTIVO en sombra (Laboratorio) | Minero + embudo de robustez; 7 variantes hacia delante. Sin ventaja probada del ranking del minero. |
| Escuela / Academia | ACTIVO | Post-mortem de cada lote y marcador por contexto; no cambia parámetros. |
| Laboratorio de mejoras | ACTIVO en sombra | Regla de promoción: ≥ 90 días, Sharpe ≥ núcleo+0,3, caída ≤ 1,2×, embudo superado. |
| Infraestructura | ACTIVO | Frescura de datos, integridad de la base de datos, incidencias, disco. |
| Bienestar del equipo (salud del sistema) | ACTIVO | Se traduce en salud operativa (Infraestructura) y en la calidad medida de cada agente (Laboratorio y Escuela). |