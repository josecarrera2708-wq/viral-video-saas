# Millonary · Réplica BTC del modelo "fondo gestionado por IA" de Conesa

Estado: **PLAN, sin código todavía.** Fecha: 2026-09-29.
Alcance: **solo Bitcoin.** Técnico + fundamental. Paper trading antes de dinero real.

---

## 0. Cómo leer este documento

- **[EVIDENCIA]** = lo vimos u oímos en el material de Conesa.
- **[SUPUESTO]** = lo deduzco, hay que comprobarlo.
- **[BLOQUEO]** = algo que hoy impide avanzar y requiere acción tuya.
- Cada fase tiene **entregables** y una **puerta de salida**: no se pasa a la siguiente sin cumplirla.

**Sobre "rentable":** nadie puede garantizarlo, y yo tampoco. Lo que sí puedo hacer es
construir el proceso que Conesa describe (generar muchas estrategias y quedarse solo con las
que aguantan pruebas duras) y **fijar por adelantado qué números significan "sirve"**
(sección 6). Si ninguna estrategia pasa, la respuesta honesta será "no operar", y eso también es
un resultado válido.

---

## 1. Qué es lo que hay que replicar (evidencia)

| Elemento de Conesa | Evidencia | Qué construimos |
|---|---|---|
| Sala de trading con agentes de IA por departamentos (dirección, riesgos, macro, análisis, mesa, cartera, derivados, arbitraje, coberturas, opciones, cuantitativo, ML, infraestructura, escuela, laboratorio) | Audio + vídeo | Un **comité de agentes** con pocos roles útiles (sección F8). No 15 departamentos. |
| Comité que comparte análisis | Audio | Ronda de análisis estructurada antes de cada decisión |
| Ranking de traders/estrategias | Audio | Tabla de rendimiento por estrategia, con métricas netas de costes |
| **Minero de estrategias 24/7 + filtro de robustez (Monte Carlo, walk-forward, criterio, post-mortem)** | Audio + capturas de "AlgoMaker" | **El corazón del proyecto** (F4 + F5) |
| Bancos del embudo, generaciones, "1092 evaluadas · 0 candidatas" | Captura | Registro de cada candidata y de cuántas se probaron (necesario para el DSR) |
| Régimen RISK-ON/OFF con BTC vs SMA50/200, volatilidad, Fear & Greed, funding | Vídeo | Módulo de régimen (F7) |
| Límites: exposición bruta, neta por activo, pérdida diaria, kill switch | Vídeo (borroso) | Capa de riesgo dura en código (F6) |
| Paper trading contra Bybit ("PAPEL realista") | Vídeo | Paper trading (F9) |
| Escuela/academia: los agentes "estudian" | Audio | Re-entrenamiento periódico con walk-forward (F12). **No** es que la IA "aprenda sola" mientras opera |

**Lo que NO sabemos de Conesa** y que no voy a inventar: las reglas concretas de entrada y
salida, los parámetros de las estrategias minadas, el tamaño de posición real, los umbrales
exactos de robustez. Las tiene su programa, no las dice en el material. Nuestro sistema
descubrirá las suyas con nuestros datos.

---

## 2. Estado del entorno (lo que pude comprobar hoy)

### 2.1 [BLOQUEO] Red: casi todo lo que necesito está denegado

Desde este contenedor, la política de red devuelve 403 a:

`api.binance.com`, `fapi.binance.com`, `data.binance.vision`, `api.bybit.com`,
`api.exchange.coinbase.com`, `api.kraken.com`, `api.coingecko.com`, `api.alternative.me`,
`query1.finance.yahoo.com`, `fred.stlouisfed.org`, `www.federalreserve.gov`,
`www.investing.com`, `truthsocial.com`, `nitter.net`, `www.coindesk.com`, `cointelegraph.com`,
`nfs.faireconomy.media`, y `huggingface.co` (transcripción de audio).

Solo funciona PyPI (instalar librerías). **Sin datos de precios no se puede hacer nada.**

**Acción tuya:** en el entorno de la sesión, *Network access → Edit*, elegir un nivel más
amplio o añadir estos dominios. Lista mínima para arrancar:
`data.binance.vision`, `api.binance.com`, `fapi.binance.com`, `api.bybit.com`,
`api-testnet.bybit.com`, `api.alternative.me`, `fred.stlouisfed.org`,
`www.federalreserve.gov`, `nfs.faireconomy.media`, `huggingface.co`.
Para la fase de noticias añadiremos más (sección F7).

Alternativa si no se puede abrir la red: **tú descargas los CSV** de BTC en tu PC (Binance
Vision es público) y los subes al chat o al repo. Sirve para F1 a F6, pero no para
noticias en vivo ni para paper trading.

### 2.2 Librerías
Instaladas: `numpy`, `pillow`, `pymupdf`, `python-docx`, `faster-whisper`. Faltan (se instalan
por PyPI sin problema): `pandas`, `pyarrow`, `numba`, `scipy`, `scikit-learn`, `statsmodels`,
`ccxt`, `pybit`, `deap`, `optuna`, `matplotlib`, `plotly`, `feedparser`, `httpx`, `fastapi`.

### 2.3 Cosas que no puedo hacer aquí
- Ejecutar 24/7: el contenedor es efímero. Para paper trading continuo hace falta un **VPS**
  (o tu PC encendido). Ver F9.
- Guardar claves de API de forma segura: usar variables de entorno / secretos del entorno,
  **nunca** en el repo.

---

## 2b. Investigación hecha y hallazgos que cambian el plan

1. **Sobreajuste al minar.** Probar miles de estrategias hace que varias salgan buenas por
   azar. El *Deflated Sharpe Ratio* (Bailey y López de Prado) ajusta el Sharpe por el número
   de pruebas y por la forma de la distribución. **Por eso el registro de "cuántas probamos" es
   obligatorio** y el DSR forma parte del embudo. Fuente:
   [SSRN 2460551](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551).
2. **Las herramientas comerciales hacen esto mismo**: StrategyQuant X (genético + Monte Carlo +
   walk-forward + OOS) y Build Alpha (robustez primero: OOS, Monte Carlo, ruido, "vs aleatorio",
   walk-forward). Lo de Conesa es ese patrón. Ver
   [Build Alpha, guía de robustez](https://www.buildalpha.com/robustness-testing-guide/).
   No encontré ningún producto llamado "AlgoMaker"; en las capturas corre en `127.0.0.1`, junto
   al "Trading Floor" [SUPUESTO: es una herramienta propia o a medida].
3. **Trump y la Fed sí mueven BTC**, con eventos documentados: −12,4 % en dos horas tras el
   anuncio de aranceles del 10-oct-2025; +7 % con la pausa de aranceles de abril de 2025; +8 %
   con el anuncio de la reserva estratégica. Es decir, el riesgo de evento es real y grande.
   Fuente: [CoinDesk](https://www.coindesk.com/markets/2026/04/20/five-times-president-trump-made-a-statement-that-moved-bitcoin-and-why-it-might-happen-again-this-week),
   [CNBC](https://www.cnbc.com/2025/04/09/bitcoin-surges-more-than-7percent-in-broad-market-relief-rally-as-trump-pauses-some-tariffs.html).
   **Implicación:** el módulo fundamental se usa primero como **protección** (reducir o cerrar
   antes/durante eventos) y solo después, si los datos lo justifican, como señal.
4. **Sistemas multiagente LLM (TradingAgents, FinMem):** existen y publican buenos backtests,
   pero son **no deterministas** (dos ejecuciones pueden dar decisiones distintas) y los
   resultados de papers en ventanas cortas no garantizan nada.
   Fuente: [TradingAgents (arXiv)](https://arxiv.org/abs/2412.20138),
   [repo](https://github.com/TauricResearch/TradingAgents).
   **Implicación:** la IA generativa **no decide sola** el dinero. Decide el sistema validado;
   los agentes analizan, explican y pueden **vetar**, nunca saltarse los límites.
5. **Bybit tiene testnet oficial** y librería `pybit`; `ccxt` también soporta sandbox y
   funding rate. Sirve para paper trading realista (F9). Fuente:
   [pybit](https://github.com/bybit-exchange/pybit),
   [API funding rate](https://bybit-exchange.github.io/docs/v5/market/history-fund-rate).
6. **Fuentes gratuitas de datos:** Binance Vision (velas históricas mensuales/diarias),
   Bybit/Binance API (funding, open interest), alternative.me (Fear & Greed), FRED (tipos, CPI,
   etc.), RSS de la Fed. **Investing.com no ofrece API pública**; automatizarlo es scraping y
   puede ir contra sus términos. Uso calendarios alternativos (FRED + calendario de
   ForexFactory en JSON + fechas oficiales FOMC/BLS). Twitter/X exige API de pago; Truth
   Social no tiene API oficial (existen RSS/espejos no oficiales, fiabilidad variable).

**Pendiente de investigar** (lo hago al arrancar F1/F7, con la red abierta): coste real de
comisiones/funding en Bybit para tu país y tipo de cuenta; disponibilidad legal de derivados
donde resides; qué espejo de Truth Social/X es fiable; latencia real de cada fuente.

---

## 3. Arquitectura objetivo (resumen)

```
 DATOS (F1) ──► MOTOR BACKTEST (F2) ──► SEÑALES (F3) ──► MINERO (F4) ──► EMBUDO ROBUSTEZ (F5)
                                                                              │
                                                                   BANCO DE ESTRATEGIAS
                                                                              │
 RÉGIMEN + FUNDAMENTAL (F7) ─────────────► COMITÉ DE AGENTES (F8) ◄───────────┘
                                                   │
                              CAPA DE RIESGO DURA (F6, veto final, kill switch)
                                                   │
                                   PAPER TRADING (F9) ──► DASHBOARD (F10) ──► GO/NO-GO (F11)
```

Regla de oro: **la capa de riesgo (F6) es código determinista y está por encima de los
agentes.** Un agente no puede subir una posición por encima del límite ni desactivar el kill
switch.

---

## 4. Fases, en orden

### F0. Preparación (bloqueos y decisiones)  · duración: 1 sesión
- Abrir la red (sección 2.1) o decidir la vía de "tú descargas los CSV".
- Decidir los parámetros de la sección 8.
- Instalar librerías. Crear `trading-btc/` con la estructura de la sección 9.
- **Puerta:** puedo descargar 1 mes de velas de BTC y 1 valor de Fear & Greed.

### F1. Datos  · 1–2 sesiones
Descargar y guardar en Parquet, con control de calidad:
- **Velas BTCUSDT** en 1m (para simular entradas exactas), 5m, 15m, 1h, 4h, 1d. Desde 2017
  (spot) y desde 2020 (perpetuo). Con volumen, número de trades y volumen del taker.
- **Funding rate** histórico (perpetuo), **open interest**, **basis** si está disponible.
- **Fear & Greed** diario (alternative.me).
- **Macro:** FFR/DFF, CPI, desempleo, DXY/índices si hay fuente (FRED), y **fechas** de FOMC,
  CPI, NFP, PCE.
- Control de calidad: huecos, duplicados, velas erróneas, zonas horarias (todo en UTC),
  cortes de exchange.
- **Puerta:** informe de calidad sin huecos > 1 h sin explicar y datos reproducibles con un
  solo comando.

### F2. Motor de backtest propio  · 2 sesiones
Vectorizado con `numpy`/`numba`, **sin mirar el futuro** (señal en la vela *t* se ejecuta en
*t+1*), con:
- Comisiones maker/taker, **slippage** configurable, **coste de funding**, apalancamiento y
  liquidación, tamaño de contrato mínimo.
- Métricas: rentabilidad, CAGR, Sharpe/Sortino, factor de beneficio, drawdown, ratio
  retorno/DD, esperanza matemática, nº de trades, duración media, curva de capital, R-múltiplos.
- **Pruebas unitarias** que demuestran ausencia de look-ahead (test canario: una estrategia
  que "adivina" el cierre siguiente debe fallar el test).
- Se valida contra un cálculo manual y contra `backtesting.py`/`vectorbt` en 2–3 estrategias
  sencillas (cruce de medias) para comprobar que da lo mismo.
- **Puerta:** los tests de no-look-ahead y de paridad pasan.

### F3. Biblioteca de señales  · 2 sesiones
Todo lo que sale de los PDFs y de Conesa, como bloques combinables:
- **Tendencia:** SMA/EMA 7, 25, 50, 100, 200, cruces, pendiente, precio vs media, triple cruce.
- **Momentum/volumen:** RSI, MFI, MACD, Bollinger, volumen relativo.
- **Volatilidad:** ATR, percentil de volatilidad, rango.
- **Velas (los PDFs):** martillo, martillo invertido, estrella fugaz, hombre colgado,
  envolvente alcista/bajista, harami, pinzas, doji, marubozu, estrella de la mañana/noche,
  tres soldados/cuervos, pin bar. **Corrijo el error del documento** (marubozu con colores
  invertidos) al codificarlas.
- **Estructura:** soportes/resistencias, máximos/mínimos, rupturas, líneas de tendencia,
  patrones de gráfico (banderas, triángulos, cuñas, doble techo/suelo, HCH) de forma
  aproximada y medible.
- **Derivados:** funding, open interest, basis.
- **Contexto:** filtro de marco temporal superior (top-down).
- **Puerta:** cada señal tiene test con un ejemplo dibujado a mano.

### F4. Minero de estrategias  · 2–3 sesiones
- Gramática de estrategias = *filtro de régimen + condición de entrada + salida + gestión*.
- Búsqueda **genética** (`deap`) y/o Optuna, con objetivos múltiples (retorno/DD, Sharpe,
  nº de trades mínimo, simplicidad).
- **Registra el nº total de candidatas probadas** (para el DSR) y guarda todas, no solo las
  buenas.
- Separación de datos **antes** de minar: entrenamiento / validación / **test ciego** que
  no se toca hasta el final (ver F5).
- Penalización por complejidad (menos parámetros = mejor).
- **Puerta:** el minero es reproducible (semilla fija) y genera un banco de candidatas con su
  historial completo.

### F5. Embudo de robustez  · 2–3 sesiones
Una candidata solo entra al banco si pasa **todas**:
1. **Mínimos:** ≥ N trades, esperanza > 0 **neta de costes**, drawdown máximo razonable.
2. **Fuera de muestra (OOS)** con embargo (purga) entre entrenamiento y test.
3. **Walk-forward** (ventanas móviles) y "walk-forward matrix".
4. **Monte Carlo:** reordenar trades (remuestreo), omitir trades al azar, variar costes ×1,5 y
   ×2, ver el peor caso de drawdown al 95 %.
5. **Sensibilidad de parámetros:** mover cada parámetro ±10–20 %; si el resultado se derrumba,
   fuera ("parámetro afilado").
6. **Ruido y datos perturbados** (ligeros cambios de precio/orden de velas).
7. **Diferentes regímenes:** funciona en alcista, bajista y lateral, o al menos no revienta
   en ninguno.
8. **Comparación con aleatorio** (entradas al azar con la misma salida).
9. **Deflated Sharpe Ratio y PBO** (probabilidad de sobreajuste) ajustados por el nº de
   pruebas del minero.
10. **Test ciego final** (una sola vez, se anota el resultado, no se vuelve a ajustar).
- **Correlación entre estrategias** para no comprar 10 copias de lo mismo.
- **Puerta:** documento por estrategia ("ficha") con todas las pruebas y por qué pasa. Es
  aceptable y esperable que **pasen muy pocas o ninguna** (Conesa: 0 de 1092 en pantalla).

### F6. Capa de riesgo dura  · 1–2 sesiones
Código determinista, independiente de la IA. Punto de partida inspirado en lo que se ve en el
Trading Floor (**los valores exactos están por confirmar, los míos son propuestas**):
- Riesgo por operación (p. ej. 0,25–0,5 % del capital) y dimensionamiento por volatilidad
  (ATR) o Kelly fraccional (1/4 o 1/2 Kelly máximo).
- Apalancamiento máximo (propuesta: 2×–3× efectivo en BTC).
- Pérdida diaria máxima (propuesta: 2–3 %) → parar el día.
- Drawdown desde máximos (propuesta: 8–10 % → reducir tamaño a la mitad; 15 % → parar y
  revisar).
- **Kill switch** manual y automático (datos caídos, latencia, orden rechazada, funding
  extremo, spread anómalo).
- Riesgo de ruina calculado (el docx "Medias móviles y RoR" trae la fórmula) para cada
  estrategia antes de activarla.
- Nunca mover el stop en contra; sí a break-even si la estrategia lo demuestra en backtest.
- **Puerta:** tests que simulan un flash-crash y comprueban que los límites se respetan.

### F7. Régimen y análisis fundamental  · 3 sesiones
**7a. Régimen de mercado** (como el RISK-ON/OFF del vídeo): BTC vs SMA50/200, volatilidad,
funding, Fear & Greed, amplitud si aplica. Salida: etiqueta + intensidad. Se valida con
backtest: ¿las estrategias rinden distinto por régimen? Si no, no se usa.

**7b. Calendario y eventos programados:** FOMC (y discursos del presidente de la Fed), CPI,
PCE, NFP, subastas, vencimientos de opciones. Regla inicial: reducir tamaño/cerrar X minutos
antes y no abrir hasta X minutos después. Los X se calibran con el histórico (F1).

**7c. Vigilancia de noticias y figuras clave "minuto a minuto"** (polling cada 1–2 min, no
es tiempo real puro):
- RSS oficiales: Fed, BLS, Tesoro, Casa Blanca; medios cripto y macro.
- Trump/Truth Social, otras figuras: **según lo que sea accesible** (API de pago de X, RSS no
  oficial de Truth Social). **Riesgo:** fuentes no oficiales caen o llegan tarde.
- Un clasificador (LLM) puntúa cada titular: relevancia para BTC, dirección probable, urgencia y
  **confianza**. Se guarda todo con marca de tiempo para medir después si acertó.
- **Uso inicial: solo protección** (bajar riesgo, bloquear nuevas entradas, alertar). No abre
  operaciones por sí solo hasta que el histórico de aciertos lo respalde.
- **Puerta:** medición retrospectiva de los 30–50 eventos más grandes de BTC: ¿el sistema
  habría detectado y reaccionado antes del pico de volatilidad? ¿Con qué retraso?

### F8. Comité de agentes  · 2–3 sesiones
Con la API de Claude, pocos roles bien definidos (más roles no significa mejor):
- **Macro/Fundamental:** resume noticias, calendario, régimen.
- **Técnico:** lee el estado de las estrategias validadas y su señal.
- **Riesgo (con veto):** aplica F6 y puede bloquear.
- **Director:** consolida, pide justificación, registra la decisión.
- **Analista post-mortem:** cada operación cerrada, ¿por qué ganó o perdió? (la "escuela").
- Cada decisión queda registrada con sus razones. **Determinismo:** temperatura baja,
  salida estructurada (JSON), y el sistema **funciona igual sin agentes** (los agentes
  añaden filtro y explicación, no son un punto único de fallo).
- Control de costes (tokens) y de latencia.
- **Puerta:** en backtest histórico con noticias/eventos reproducidos, el comité mejora o al
  menos no empeora los resultados del sistema sin comité. **Si no mejora, se queda como
  informador**, no como decisor.

### F9. Paper trading  · 8–12 semanas de calendario
- Bybit **testnet** o simulador propio con precios en vivo (con slippage realista).
- Requiere un **VPS** (~5–10 €/mes) o ejecución continua; el contenedor de esta sesión no
  sirve.
- Registro de cada señal, orden, fill simulado, coste, y comparación con lo que el backtest
  habría hecho en las mismas velas ("tracking error").
- Reportes diarios y semanales automáticos.
- **Puerta:** ≥ 8 semanas, ≥ 50 operaciones; métricas dentro de la banda esperada por Monte
  Carlo; sin fallos de infraestructura.

### F10. Panel de control  · 2 sesiones
- Web local (FastAPI + página simple): estado del fondo, régimen, estrategias activas,
  ranking, riesgo en tiempo real, log de eventos, botones **Pausar** y **Kill switch**.
- Opcional al final, por estética: la "sala de trading" isométrica animada. Es vistosa pero no
  aporta rentabilidad; va la última.

### F11. Decisión go / no-go y dinero real  · decisión tuya
- Solo si F5 y F9 cumplen la sección 6.
- **Capital inicial pequeño** (una cantidad cuya pérdida total puedas asumir), escalado por
  tramos, con las mismas reglas de riesgo. Apalancamiento bajo.
- Órdenes vía API con permisos **solo de trading, nunca de retirada**, IP restringida.
- Revisión legal/fiscal en tu país.

### F12. Operación y mejora continua
- Re-minado y re-validación periódica (mensual/trimestral) con walk-forward.
- Detector de "decaimiento" de cada estrategia (si se sale de su banda, se pausa).
- Documentación de cada cambio (nada de retocar parámetros tras ver resultados en vivo).

---

## 5. Orden de ejecución (resumen)

`F0 → F1 → F2 → F3 → F4 → F5 → F6` (motor y validación: **aquí se decide si hay algo**)
`→ F7 → F8` (fundamental y agentes)
`→ F9 → F10 → F11 → F12` (paper, panel, dinero real, mejora)

F6 puede empezar en paralelo a F4. F7 puede empezar en paralelo a F4/F5 (independiente del
minero). Todo lo demás es secuencial.

**Punto de decisión temprano (tras F5):** si no sobrevive ninguna estrategia, no seguimos
hacia paper/dinero real. Paramos, ampliamos el espacio de búsqueda (otros marcos
temporales, otras señales, funding/OI) o cambiamos el enfoque.

---

## 6. Criterios de éxito fijados de antemano (propuesta a confirmar)

Los fijo **antes de ver resultados** para no poder engañarnos después.

Para que una estrategia entre al banco (F5):
- Esperanza > 0 **neta de comisiones, slippage y funding**, incluso con costes ×1,5.
- ≥ 200 trades en total (menos, no es estadísticamente fiable) y ≥ 30 en OOS.
- Sharpe OOS ≥ 1,0 (anualizado) y **Deflated Sharpe Ratio ≥ 0,95**.
- PBO (prob. de sobreajuste) ≤ 0,3.
- Drawdown máximo OOS ≤ 20 % y peor drawdown Monte Carlo (p95) ≤ 30 %.
- Estabilidad: ±20 % en parámetros no la rompe.
- Riesgo de ruina < 1 %.

Para pasar de paper a dinero real (F11):
- ≥ 8 semanas y ≥ 50 operaciones en paper.
- Rendimiento y drawdown dentro de la banda del Monte Carlo.
- Diferencia backtest–paper explicada (< 25 % en métricas clave).
- Cero incidencias de riesgo sin resolver.

Si tú prefieres otros umbrales, lo cambiamos **ahora**.

---

## 7. Riesgos principales (y qué hago con ellos)

| Riesgo | Mitigación |
|---|---|
| Sobreajuste (lo más probable) | Registro de pruebas + DSR/PBO + test ciego + Monte Carlo (F5) |
| Look-ahead / errores del backtest | Tests canarios, paridad con librerías (F2) |
| Costes subestimados | Comisiones, slippage y funding explícitos; prueba con costes ×2 |
| Evento de cola (Trump, Fed, hack de exchange) | Capa de riesgo dura, kill switch, ventanas de bloqueo (F6/F7) |
| LLM no determinista / alucina | Agentes solo informan y vetan; JSON estructurado; el sistema funciona sin ellos |
| Fuentes de noticias que fallan o llegan tarde | Redundancia, marca de tiempo, "sin datos = riesgo reducido" |
| Cambio de régimen (la estrategia deja de funcionar) | Detector de decaimiento + re-validación periódica (F12) |
| Riesgo operativo (claves, permisos, caídas) | Claves solo-trading, IP restringida, monitorización, VPS |
| Riesgo de mi propia lectura de Conesa | Todo lo no confirmado está marcado [SUPUESTO]; no se usa como regla |
| Expectativas | Un día de +0,078 % en paper (lo que enseña Conesa) no demuestra nada. Nosotros exigimos meses. |

---

## 8. Decisiones que necesito de ti (bloquean F0/F1/F6)

1. **Red:** ¿puedes ampliar el acceso de red del entorno (2.1)? Si no, ¿descargas tú los CSV?
2. **Instrumento:** ¿spot BTC/USDT o **perpetuo con apalancamiento** (Bybit)? Recomiendo empezar
   con perpetuo a 1–3× por funding y por poder ir corto, pero solo si es legal en tu país.
3. **Marco temporal principal:** Conesa mostraba **1h**. Propongo minar en 1h y 4h y usar 1d
   como filtro. ¿De acuerdo?
4. **Capital de referencia** para simular (Conesa: 100.000 $ en paper; tú, ¿cuánto vas a poner
   de verdad?). El tamaño mínimo de contrato y las comisiones dependen de esto.
5. **País / broker:** para revisar disponibilidad de Bybit y fiscalidad.
6. **Presupuesto de IA:** clave de la API de Claude para los agentes (F8) y un tope mensual.
7. **VPS para 24/7** (F9): ¿lo contratas tú o probamos primero en tu PC?
8. **Umbrales de la sección 6:** ¿los aceptas o los cambiamos?
9. **Audio pendiente de Conesa:** lo que aún no me pasaste (nombre del programa, reglas,
   límites exactos). Cada dato nuevo se incorpora a F6/F7.
10. **Datos que aporten más:** si tienes acceso de pago a algo (TradingView, Glassnode, X API),
    dímelo; mejora F7.

---

## 9. Estructura de carpetas propuesta

```
trading-btc/
  RUTA-DE-TRABAJO.md      ← este documento
  README.md
  config/                 ← parámetros y límites de riesgo (sin secretos)
  data/                   ← parquet (no se sube a git)
  src/
    data/                 ← F1
    backtest/             ← F2
    signals/              ← F3
    miner/                ← F4
    robustness/           ← F5
    risk/                 ← F6
    regime_news/          ← F7
    agents/               ← F8
    execution/            ← F9/F11
    dashboard/            ← F10
  tests/
  reports/                ← fichas de estrategia, informes de calidad, paper trading
  docs/
    conesa-evidencia.md   ← transcripciones y capturas, con etiquetas de confianza
    material-pdf.md       ← resumen del material de estudio
```

---

## 10. Qué haré nada más tengas resuelto lo de la sección 8

1. Abro F0/F1: descarga de datos y control de calidad.
2. Te enseño un **primer informe de datos** (cobertura, huecos, gráficos) antes de tocar
   estrategias.
3. Sigo por F2 (motor) con las pruebas de paridad, y te reporto al cerrar cada fase con su
   puerta de salida cumplida o no.
