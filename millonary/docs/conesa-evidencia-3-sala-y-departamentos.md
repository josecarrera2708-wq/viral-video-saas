# Evidencia 3 · Transcripción del vídeo de la sala y los departamentos (aportada por el dueño, 2026-09-29)

Fuente: audio de un vídeo de Vicente Conesa Santos mostrando la interfaz del fondo. **Marcada como MARKETING/AFIRMACIONES del
autor: no son resultados verificados.** Las imágenes de esa interfaz llegarán aparte; el dueño avisará cuando haya enviado todas.

## Lo que muestra / afirma
**Estructura física simulada (oficina):** despacho de dirección (el propio Conesa), sala de comité, gimnasio, zona zen,
infraestructura, zona de **minería de estrategias**, zona de **estrategias ya minadas** ("que ya sabemos que funcionan"),
**incubadora de traders**, coberturas, arbitraje, derivados (opciones "también las vamos a incluir").

**Incubadora de traders:** traders IA que prueban estrategias en simulación hasta encontrar las que funcionan; a las que
funcionan se les **asigna capital real**.

**Chat de agentes 24/7:** los agentes hablan entre ellos continuamente. Ejemplos: Riesgos informa de "posicionamiento en BNB",
"funding anual"; un analista dice a un trader "apunta esto como contexto"; Infraestructura crea clases; un trader "posición en
el oro, esperando el Ichimoku". El dueño puede seleccionar agentes e interactuar.

**Laboratorio:** revisa lo que hacen los traders y mejora las estrategias; ejemplo citado: "fuera de muestra el beneficio pasa de
11.200 a 20.000 dólares por cada 10.000; factor de beneficio 1,26 → 1,73". Los traders "se lo apuntan y operan con ello".

**Academia / Escuela:** los agentes reciben formación, se muestra qué estudian y su rango/nivel (p. ej. "gestión de riesgo nivel 4");
"mejoran con un sistema de machine learning y una red neuronal".

**Bienestar del equipo:** cada agente tiene energía, estrés, confianza y foco (ejemplo: Mei Nakamura, analista cuantitativo, 40
de energía, 20 de estrés); el dueño puede mandarlo a la zona zen o al gimnasio.

**Ranking diario de traders:** P&L por trader (una pérdida de 90-95 USD, un día de +174 USD), trades abiertos en vivo
(Rocío Ortega acaba de abrir uno).

**Departamentos listados:** dirección, riesgos, macroeconomía, **análisis de sesgo por activo** (para detectar posibles entradas),
gestión de cartera, escuela, laboratorio de mejoras, bienestar del equipo, academia, mesa de derivados, **mesa de arbitraje**
(retornos citados: 9 % y 11 % anual por agente), coberturas (proteger operaciones que no salen bien), opciones (futuro), equipo
cuantitativo, machine learning, infraestructura, mesa de trading.

**Noticias / calendario económico:** el fondo usa el calendario macro para sus análisis.
**Informe diario:** resumen de cómo va el día (beneficio/pérdida).
**Multi-activo:** BNB, oro (XAUUSD) y otros. (Nuestro proyecto: solo BTC por decisión del dueño.)

## Correspondencia con lo ya construido en Millonary
| Elemento de Conesa | En Millonary hoy |
|---|---|
| Comité, Dirección | ✔ `desk/committee.py` |
| Riesgos | ✔ capa determinista + informe |
| Macroeconomía + calendario | ✔ FOMC oficial + F&G/VIX/curva/dólar/funding (CPI/empleo: sin fuente) |
| Análisis de sesgo por activo | ◐ análisis técnico BTC (sin multi-activo) |
| Gestión de cartera | ✔ |
| Escuela / Academia | ◐ post-mortem por lote y marcador por contexto (sin "niveles" ni currículo) |
| Laboratorio de mejoras | ◐ 6 variantes en sombra + regla de promoción |
| Cuantitativo / ML | ◐ minero + embudo (sin ventaja probada del ranking) |
| **Incubadora de traders** | ✘ NO existe: traders de simulación por estrategia con asignación de capital por mérito |
| **Estrategias ya minadas (biblioteca)** | ◐ candidatas del minero sin certificar; biblioteca formal ✘ |
| **Chat de agentes entre sí 24/7** | ✘ (los informes son estructurados, no conversacionales) |
| **Ranking de traders del día** | ✘ (solo un trader: el núcleo) |
| **Bienestar (energía/estrés/confianza/foco)** | ✘ (equivalente posible: calidad medida de cada agente) |
| Mesa de arbitraje / coberturas / derivados / opciones | ◐ derivados en investigación; resto sin construir |
| Noticias en vivo | ✘ pendiente |
| Informe diario | ✔ briefing + informe de la prueba |
| Multi-activo | ✘ (solo BTC por decisión del dueño) |

## Notas críticas (para cuando se construya)
- "Red neuronal con cerebro casi como el de un humano" y las cifras de mejora del laboratorio son afirmaciones sin evidencia
  aportada; cualquier mejora debe medirse fuera de muestra y con corrección por comparaciones múltiples (protocolo de Millonary).
- La incubadora es la pieza más interesante y replicable: N traders-estrategia en simulación, cada uno con su propia evidencia,
  y **asignación de capital proporcional al mérito estadístico** (no al último resultado).
