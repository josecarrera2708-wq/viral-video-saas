# Sesión del comité · 2026-09-29 16:47 UTC

**Estado general:** 🟡 AVISO
**Decisión:** Mantener el objetivo del núcleo: 0.62× de exposición.
**Principio:** los agentes analizan y recomiendan; la operativa la fija el núcleo validado y solo Riesgos puede vetar.

**Avisos:** Gestión de cartera

## 🟢 Riesgos — Sin cuenta todavía
- No hay operaciones ni equity registradas.

## 🟢 Macroeconomía — Entorno NORMAL
- Fear & Greed 73 (codicia).
- VIX 14.2 (percentil 2% del último año).
- Curva 10a-2a: +0.36 pp; 10a 5.17%.
- Dólar (índice amplio) -0.2% en 50 días.
- Funding actual 0.0100% por 8h (percentil 92% del último año); media 30d anualizada 10.9%.
- Próximo evento: FOMC (alto) 2026-10-28 18:00 UTC, en 697 h.
- Regla histórica probada: recortar la exposición alrededor del FOMC EMPEORÓ el núcleo (Sharpe 0,78 → 0,74; rechazada). Solo se informa, no se actúa.

## 🟢 Análisis de mercados — Tendencia alcista (3/4 horizontes)
- Momentum por horizonte: 20d +6.4%, 60d +28.9%, 120d +13.3%, 250d -6.7% → 3/4 positivos.
- Ruptura Donchian-50 (4h): LARGO.
- Precio +17.3% sobre la SMA200 diaria; SMA50 > SMA200.
- Volatilidad (ATR 4h) 0.99% del precio, percentil 23% del último año.
- Estructura: último máximo confirmado 85,146 (+2.0 ATR), último mínimo 83,778 (+0.4 ATR).
- Patrones de velas recientes (informativo, sin ventaja probada): pin_bar bajista.

## 🟡 Gestión de cartera — Objetivo 0.62× · actual 0.00×
- Señal = 0,5·A(0.75) + 0,5·B(1) = 0.875.
- Volatilidad anual (EWMA 45d) 35% → escala mín(2; 25%/σ) = 0.71.
- Exposición objetivo 0.62× frente a 0.00× actual (banda ±20%) → REBALANCEO pendiente.
- Coste de funding estimado a esta exposición: +0.00% anual del capital.

## 🟢 Mesa de trading — Sin órdenes todavía
- La mesa ejecutará cuando el núcleo pida cambiar la exposición.

## 🟢 Derivados y arbitraje — Carry teórico +10.9% anual (investigación)
- Funding anualizado: 30d +10.9%, 1 año +3.8%.
- Carry teórico 'cash-and-carry' (largo spot + corto perpetuo): ≈ 10.9% anual bruto a 30d; el coste de montar y desmontar es ≈ 4 × 5 pb = 0,20 % y exige capital en spot y margen en el perpetuo.
- ESTADO: INVESTIGACIÓN. No se opera: requiere ejecución en dos mercados y gestión del riesgo de contraparte; se evaluará como pata aparte con su propio protocolo.

## 🟢 Laboratorio (cuantitativo / ML) — 6 variantes en sombra · 0 días de prueba
- Todas las variantes arrancan planas el 2026-09-29 16:30 UTC; 0 días hacia delante.
  solo pata A (momentum diario): retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
  solo pata B (Donchian 50): retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 20 %: retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
  vol. objetivo 35 %: retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
  horizontes cortos (10/20/40/60d): retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
  horizontes largos (60/120/250/365d): retorno +0.0% · caída 0.0% · Sharpe n/d → sin evidencia (faltan días)
- Contexto histórico de cada variante (2017-2025-06, solo exploratorio) en reports/lab_historia.json; cada una cuenta como prueba en el registro.
- Regla de promoción: ≥ 90 días hacia delante, Sharpe ≥ núcleo + 0,3, caída ≤ 1,2× la del núcleo, embudo de robustez superado.

## 🟢 Escuela — Sin operaciones que analizar todavía
- La Escuela empieza a aprender cuando haya lotes cerrados: clasifica cada uno por contexto y mide dónde falla el sistema.

## 🟢 Infraestructura — Sano · datos hace 16.8 h
- Última vela cerrada a las 2026-09-29 00:00 UTC (hace 16.8 h) · fuente: Binance Vision.
- Base de datos: ok.
- Disco libre 29.5 GB.

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
| Opciones | FUTURO | Requiere otro mercado (p. ej. Deribit) y otro marco de riesgo. |
| Cuantitativo / Machine learning | ACTIVO en sombra (Laboratorio) | Minero + embudo de robustez; 7 variantes hacia delante. Sin ventaja probada del ranking del minero. |
| Escuela / Academia | ACTIVO | Post-mortem de cada lote y marcador por contexto; no cambia parámetros. |
| Laboratorio de mejoras | ACTIVO en sombra | Regla de promoción: ≥ 90 días, Sharpe ≥ núcleo+0,3, caída ≤ 1,2×, embudo superado. |
| Infraestructura | ACTIVO | Frescura de datos, integridad de la base de datos, incidencias, disco. |
| Bienestar del equipo (salud del sistema) | ACTIVO | Se traduce en salud operativa (Infraestructura) y en la calidad medida de cada agente (Laboratorio y Escuela). |