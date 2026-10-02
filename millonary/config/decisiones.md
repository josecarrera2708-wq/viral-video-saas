# Millonary · Decisiones de diseño (2026-09-29)

Las decisiones marcadas **[YO]** las tomo yo con lo recopilado (el dueño me delegó esa autoridad);
las marcadas **[TÚ]** son del dueño.

| # | Decisión | Valor | Razón |
|---|---|---|---|
| 1 | Nombre / marca | **Millonary** | [TÚ] |
| 2 | Activo | Solo BTC | [TÚ] |
| 3 | Capital admitido | **100 a 10.000 USDT** | [TÚ] |
| 4 | Apalancamiento máximo | **5×** (tope duro) | [TÚ]. Objetivo efectivo ≤ 3×; 5× solo si la estrategia lo justifica en backtest |
| 5 | Stop-loss | **Según análisis**, nunca fijo: por estructura y/o ATR, lo elige el minero y lo valida el embudo | [TÚ]/[YO] |
| 6 | Instrumento | **Perpetuo USDT-M** (largos y cortos, funding modelado) | [YO]: es la serie sin huecos con funding; permite ir corto |
| 7 | Marcos temporales | Minar en **1h y 4h**; 1d como filtro de régimen | [YO]: Conesa muestra 1h; 15m se deja para refinar entradas más tarde |
| 8 | Serie de validación principal | Perpetuo desde 2020-01 (≈6,7 años, 0 huecos) | [YO] |
| 9 | Riesgo por operación | 0,5 % del capital (tramo alto); 1 % (tramo bajo) | [YO], ver nota de capital pequeño |
| 10 | Pérdida diaria máxima | 3 % → pausa hasta el día siguiente | [YO] |
| 11 | Drawdown desde máximos | 10 % → tamaño a la mitad; 15 % → parada total y revisión | [YO] |
| 12 | Criterios de aceptación | Los de la sección 6 de la ruta de trabajo | [YO] |
| 13 | Los agentes de IA no pueden saltarse la capa de riesgo | Regla fija | [YO] |

## Tramos de capital (importante)
Con BTC ≈ 83.500 USDT, el lote mínimo de 0,001 BTC vale ≈ 83,5 USDT de nocional. Consecuencias:

| Capital | Qué implica |
|---|---|
| **100–300 USDT** | No se puede dimensionar por riesgo con precisión: con un stop del 2 % el lote mínimo ya arriesga ≈ 1,7 USDT (≈ 1,7 % de 100). Regla: **se omite la operación si el riesgo del lote mínimo supera el 2 % del capital**. Funciona como "modo mínimo", con muchas menos operaciones posibles y más peso de las comisiones. |
| **300–1.000 USDT** | Dimensionado casi correcto. Riesgo objetivo 1 %. |
| **1.000–10.000 USDT** | Dimensionado normal. Riesgo objetivo 0,5 %. |

**Recomendación sincera:** empezar el paper trading con 1.000 USDT de referencia, y para dinero real
no bajar de ~300 USDT. Con 100 USDT las comisiones y el lote mínimo desvirtúan las estadísticas del
backtest.

## Nota sobre el apalancamiento 5×
A 5× una caída adversa de ~20 % liquida la posición (menos margen de mantenimiento). Como BTC hizo
velas de 1h de −18 % (mar-2020, oct-2025), el motor **modela la liquidación** y un stop siempre debe
estar mucho más cerca que ese nivel. El apalancamiento es un tope, no un objetivo.

## 2026-09-29 · Construcción tras la fase de evidencia (el dueño dio el «adelante»)
- Incubadora de traders (15 setups del estilo Conesa) con prerregistro previo, atribución α/β/tendencia, Holm/BH, DSR, PBO y examen sellado: **0/15 certificadas**. El reparto de capital simulado queda 100 % en el núcleo v1 (resultado válido).
- Meta-etiquetado logístico con examen sellado: 0 ganan. No se retoca el umbral (sería una prueba nueva).
- Mesa de opciones (Deribit público) añadida como departamento informativo; sin operar opciones ni activar protección de cola.
- Chat de agentes determinista (`src/desk/chat.py`): mensajes derivados de los informes reales; `ask` responde con cifras del informe, sin LLM ni decisiones.
- Bienestar de Conesa = cosmético (según su propia UI: «el ánimo no cambia ninguna operación»); aquí equivale a la salud de Infraestructura. No se construye.
- Pendiente: noticias en vivo (sin fuente fiable/gratuita), multi-activo (fuera de alcance: solo BTC), Hyperliquid/arbitraje real (requiere dos plataformas).

## 2026-09-29 · Panel, informe semanal y ciclo de mejora continua
- Ciclo de mejora prerregistrado (`config/mejoras_prerregistrada.md`): las estrategias solo «se perfeccionan» pasando etapas (construcción → validación → sombra hacia delante → adopción con ≥ 90 días, ΔSharpe ≥ +0,3, caída ≤ 1,2×, p < 0,10 con Holm). Nada toca capital sin aprobación del dueño.
- Hallazgo: «tamaño por volatilidad» mejora casi todos los traders (caída del examen 46-58 % → 17-32 %), coherente con el diseño del núcleo; «solo largos» mejora mucho pero se explica por la deriva alcista 2020-25 (los cortos no aportaron). Ambos siguen en sombra hasta tener datos hacia delante.
- La rutina diaria genera `paper_state/panel.html` (pestañas Sala/Ranking/Equipos/Informe) y `paper_state/semanal/` (informe .md, operaciones .csv, diario .xlsx) y actualiza `reports/mejoras_registro.json`; ninguno de esos pasos puede detener la actualización de la cuenta.

## 2026-09-29 · Mesa intradía (petición del dueño: 1-2 operaciones/día)
- El núcleo v1 y su prueba NO se tocan (cambiarlos invalidaría la evidencia). La mesa intradía es un sistema aparte: 14 traders de 1 h con stop, TP y tiempo, con contabilidad propia.
- Histórico (examen sellado, una sola ejecución): 0/14 certificadas; expectativa negativa en los 14. Causa estructural: el coste de ida y vuelta (≈12 pb) equivale a ≈0,2 R con stops de 1-2 ATR de 1 h. Con 1-2 operaciones al día el edge bruto tendría que superar ese coste.
- Aun así los 14 operan en papel hacia delante con datos de Deribit (único proveedor accesible), actualización horaria, para medir en semanas lo que el núcleo tardaría años en mostrar.
- Skills instalados: ninguno de trading; el catálogo de la organización solo tiene plugins de contabilidad. Referencias comunitarias de GitHub (solo Markdown) usadas como lista de comprobaciones: prueba de truncamiento, estrés de costes ×1,5/2/3, remuestreo Monte Carlo, control de deriva. No se instala código de terceros.

## 2026-10-02 · Mesa de 15 min en paralelo + aprendices
Petición del dueño: acelerar con velas de 15 min sin tocar la mesa de 1 h, añadir acción de precio (techos/suelos, ineficiencias, patrones de velas) y fórmulas cuantitativas, y que los agentes aprendan sin esperar 90 días.
Decisión: sistema aparte (`src/desk15`, `paper_state/mesa15`), 13 traders prerregistrados, y aprendices A (individual) y C (colectivo) que vetan contextos donde la evidencia ya cerrada es peor que la media del trader; se evalúan contra su base. Nada toca dinero real.
Honestidad: el histórico dio 0/13 certificadas y R media ≈ −0,3 por operación (costes); el aprendizaje reduce pérdidas pero no crea ventaja.

## 2026-10-02 · Mesa de 1 h con los 13 traders (petición del dueño) y prueba de stops
Se añade `paper_state/mesa1h` (papel, inicio 2026-10-02 00:00 UTC, rutina horaria). Stops más anchos: solo informe, sin cambios en mesas en marcha.

## 2026-10-02 · Revisión completa + mesa de fondos (petición del dueño)
- Fallos corregidos: (1) el funding sintético del mes en curso nunca se sustituía por el real (causa de G1 en NO desde el día 1; libro funding_ledger con corrección automática); (2) la réplica de G1 recibía solo 2 días de funding (habría fallado con el paso de las semanas); (3) la mesa intradía no paginaba Deribit (límite 744 tasas / 5.000 velas: desde ~30-oct habría reescrito en silencio el funding de operaciones cerradas).
- Mesa de fondos en papel desde 2026-10-03 (10 estrategias, rutina horaria, pestaña «Fondos»). La única certificada es el carry de funding (neutral al precio, no correlacionado con el núcleo): es la candidata natural para complementar el núcleo, pero NO se activa con dinero: requiere ≥ 90 días en papel, revisar el riesgo de contraparte y aprobación EXPRESA del dueño.
