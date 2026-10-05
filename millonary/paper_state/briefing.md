# Sesión del comité · 2026-10-05 04:17 UTC

**Estado general:** 🟢 OK
**Decisión:** Mantener el objetivo del núcleo: 0.64× de exposición.
**Principio:** los agentes analizan y recomiendan; la operativa la fija el núcleo validado y solo Riesgos puede vetar.


## 🟢 Riesgos — Operativa permitida · exposición 0.59× · caída 1.2%
- Distancia a los frenos: caída 1.2% de 30%; pérdida diaria 0.0% de 7%.
- Exposición 0.59× (tope efectivo 2.0×; el 5× del exchange no se usa).
- Liquidación (margen cruzado): el precio tendría que moverse ≈ 169% en contra; con esta exposición un gap de -50% costaría -29% del capital.

## 🟢 Macroeconomía — Entorno NORMAL
- Fear & Greed 70 (codicia).
- VIX 16.4 (percentil 35% del último año).
- Curva 10a-2a: +0.46 pp; 10a 5.24%.
- Dólar (índice amplio) -0.2% en 50 días.
- Funding actual 0.0100% por 8h (percentil 96% del último año); media 30d anualizada 5.3%.
- Próximo evento: FOMC (alto) 2026-10-28 18:00 UTC, en 566 h.
- Regla histórica probada: recortar la exposición alrededor del FOMC EMPEORÓ el núcleo (Sharpe 0,78 → 0,74; rechazada). Solo se informa, no se actúa.

## 🟢 Análisis de mercados — Tendencia alcista (3/4 horizontes)
- Momentum por horizonte: 20d +10.3%, 60d +32.2%, 120d +38.8%, 250d -4.1% → 3/4 positivos.
- Ruptura Donchian-50 (4h): LARGO.
- Precio +18.6% sobre la SMA200 diaria; SMA50 > SMA200.
- Volatilidad (ATR 4h) 0.87% del precio, percentil 9% del último año.
- Estructura: último máximo confirmado 87,250 (+3.4 ATR), último mínimo 83,842 (-1.2 ATR).
- Patrones de velas recientes (informativo, sin ventaja probada): harami bajista, tweezers bajista.

## 🟢 Gestión de cartera — Objetivo 0.64× · actual 0.59×
- Señal = 0,5·A(0.75) + 0,5·B(1) = 0.875.
- Volatilidad anual (EWMA 45d) 34% → escala mín(2; 25%/σ) = 0.73.
- Exposición objetivo 0.64× frente a 0.59× actual (banda ±20%) → sin cambios necesarios.
- Coste de funding estimado a esta exposición: +3.14% anual del capital.
- Cuenta pequeña: el lote mínimo (85 USDT) es el 8% del capital; el objetivo se redondea a ese paso.

## 🟢 Mesa de trading — 1 órdenes · 1 lotes abiertos
- 1 órdenes ejecutadas (comisiones 0.29 USDT). Modelo de costes: 5 pb comisión + 2 pb deslizamiento por lado.
  2026-09-29 20:00 BUY 0.0070 BTC @ 83,579.1 (BANDA)
- Lotes abiertos: 1 (no realizado +7.30 USDT). Cuadre del diario: OK.

## 🟢 Derivados y arbitraje — Carry teórico +5.3% anual (investigación)
- Funding anualizado: 30d +5.3%, 1 año +3.3%.
- Carry teórico 'cash-and-carry' (largo spot + corto perpetuo): ≈ 5.3% anual bruto a 30d; el coste de montar y desmontar es ≈ 4 × 5 pb = 0,20 % y exige capital en spot y margen en el perpetuo.
- ESTADO: INVESTIGACIÓN. No se opera: requiere ejecución en dos mercados y gestión del riesgo de contraparte; se evaluará como pata aparte con su propio protocolo.

## 🟢 Laboratorio (cuantitativo / ML) — 6 variantes en sombra · 4 días de prueba
- Todas las variantes arrancan planas el 2026-09-29 16:30 UTC; 4 días hacia delante.
  solo pata A (momentum diario): retorno +0.7% · caída 1.3% · Sharpe n/d → sin evidencia (faltan días)
  solo pata B (Donchian 50): retorno +0.9% · caída 1.7% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 20 %: retorno +0.6% · caída 1.2% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 35 %: retorno +1.1% · caída 2.1% · Sharpe n/d → sin evidencia (faltan días)
  horizontes cortos (10/20/40/60d): retorno +0.9% · caída 1.6% · Sharpe n/d → sin evidencia (faltan días)
  horizontes largos (60/120/250/365d): retorno +0.7% · caída 1.3% · Sharpe n/d → sin evidencia (faltan días)
- Contexto histórico de cada variante (2017-2025-06, solo exploratorio) en reports/lab_historia.json; cada una cuenta como prueba en el registro.
- Regla de promoción: ≥ 90 días hacia delante, Sharpe ≥ núcleo + 0,3, caída ≤ 1,2× la del núcleo, embudo de robustez superado.

## 🟢 Incubadora de traders — 15 traders en sombra · 0 certificadas · 5 días
- Histórico (examen 2024-01→2025-06, 15 traders): certificadas 0/15 · PBO del conjunto 0.31. Mejor Sharpe en examen ≈ 1.19 (buy&hold 1.47); menor p (Holm) del α = 1.00.
- Reparto de capital simulado por mérito: núcleo v1 100%.
- Mesa de estrategias minadas: vacía (ninguna certificada; el capital sigue 100 % en el núcleo).
- Ranking hacia delante (5 días, sombra; sin capital, sin valor estadístico hasta ≥ 90 días):
  S03 Bollinger + RSI (reversión): +1.87% · caída 0.7% · 1 ops · posición -1
  S14 Momentum 90 d: +1.25% · caída 2.4% · 1 ops · posición +1
  S07 SMA 7-25 + filtro 200 (largo): +0.89% · caída 2.4% · 1 ops · posición +1
  S10 MACD + EMA200: +0.56% · caída 2.4% · 1 ops · posición +0
  S06 Cruce SMA 7-25: +0.38% · caída 2.4% · 2 ops · posición +1

## 🟢 Mesa de opciones — IV 34% vs RV 32% · put 10 % OTM 0.77%
- Vencimiento a 25.2 días: volatilidad implícita ATM 34.0% · realizada 30 d 31.7% · prima +2.3 pts.
- Sesgo 25Δ (puts − calls): +0.4 pts. Put 10 % por debajo (K≈78,000): cuesta 0.77% del nocional.
- Prima de volatilidad normal.
- ESTADO: solo informa. La protección de cola no se activa: no se puede validar con histórico (sin datos históricos de opciones).

## 🟢 Mesa intradía — 62 operaciones · 3 abiertas
- 14 traders en papel · 62 operaciones cerradas (11.3 al día entre todos) · 3 posiciones abiertas.
- Datos: Deribit BTC-PERPETUAL 1 h (velas cerradas), última vela cerrada 2026-10-05 04:00 UTC.
  I13 Parabolic SAR + EMA200: +1.65% · 3 ops · R total +1.55
  I02 Ruptura Donchian 24 h: +1.22% · 5 ops · R total +3.91
  I01 Rango asiático → Londres/NY: +0.96% · 3 ops · R total +2.42
- El histórico 2020-2026 da expectativa negativa tras costes en los 14 (0/14 certificadas): esta prueba mide si se confirma hacia delante.

## 🟢 Escuela — 0 lotes cerrados analizados · 0 categorías débiles
- Sin lotes cerrados
- Aún no hay lotes cerrados con contexto suficiente para clasificar.
- Con muestras < 20 estas cifras son ANECDÓTICAS: se muestran para acumular evidencia, no para cambiar reglas.

## 🟢 Infraestructura — Sano · datos hace 28.3 h
- Última vela cerrada a las 2026-10-04 00:00 UTC (hace 28.3 h) · fuente: Binance Vision.
- Base de datos: ok.
- Incidencias en 7 días: 0.
- Disco libre 29.1 GB.

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