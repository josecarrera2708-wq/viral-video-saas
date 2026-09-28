# Kit 04 · Análisis de canales de YouTube

Le das **el enlace de un canal** y Claude Code te devuelve el análisis que hace un
consultor de YouTube: mira sus miniaturas una por una, lee sus títulos, sus
descripciones, sus hashtags y sus etiquetas, cuenta sus duraciones y sus fechas de
subida, encuentra los vídeos que reventaron y averigua qué tenían en común, lee el
gancho de los primeros segundos palabra por palabra, y te dice **en qué punto se le
cae la gente** y qué grabar a continuación.

Salida: un informe **HTML** de 14 secciones que se abre en cualquier navegador, más
un archivo con **el packaging reescrito** (títulos y miniaturas nuevos para sus
vídeos flojos y los 10 siguientes vídeos ya planificados).

- **Input**: un enlace de canal. Opcionalmente, 4 capturas de YouTube Studio.
- **Output**: `workspace/youtube-[canal].html` + `workspace/[canal]-packaging.md`
- **Tiempo**: 10-20 minutos por canal (según cuántos vídeos entren en la muestra).
- **Coste añadido**: cero. Ni claves de API, ni cuenta de Google, ni suscripciones.

---

## Cómo obtiene los datos (y por qué esto es raro)

Una página de canal de YouTube **no se puede leer** con un lector de webs normal:
devuelve un armazón vacío. Por eso casi ninguna herramienta conversacional puede
analizar un canal de verdad.

Este kit usa **`yt-dlp`**, el lector de datos públicos de YouTube más usado del
mundo. Es un programa único, gratuito y de código abierto que el wizard instala por
ti en un paso. Con él, del enlace salen:

| Dato | Se usa para |
|---|---|
| Títulos, duraciones, fechas de subida | Nicho, ritmo, formato, títulos |
| Visitas, me gusta, comentarios por vídeo | Outliers, comunidad, conversión |
| Suscriptores y visitas totales del canal | Cuántas visitas cuesta un suscriptor |
| Descripción completa, hashtags, etiquetas, categoría | Ficha técnica y buscabilidad |
| Capítulos | Estructura y navegación dentro del vídeo |
| **Miniaturas en imagen** | Claude las **ve**: legibilidad, texto, contraste, cara |
| **Momentos más vistos** (curva pública) | Dónde se cae la gente dentro del vídeo |
| **Transcripción automática** | El gancho de los primeros segundos, literal |
| Pestaña de Shorts | Si los Shorts ayudan al canal o le traen público que no vuelve |

**Lo que no está en el enlace** son las métricas privadas: CTR, impresiones,
retención media y fuentes de tráfico. Están solo en YouTube Studio, y solo las ve
el dueño. Si el canal es tuyo, 4 capturas (un minuto: el guion está en
`entrada/LEEME.md`) convierten el informe en un embudo medido con tus propios
números. Si no las hay, esas dimensiones quedan **"sin datos"** y se dice en el
informe. **Nunca se estiman.**

El kit **no descarga vídeos**: solo metadatos, subtítulos y miniaturas. No entra en
ninguna cuenta, no necesita contraseñas y no publica nada.

---

## Qué mide: 4 bloques, 16 dimensiones, 100 puntos

El embudo es el de YouTube de verdad. Es secuencial: un agujero arriba estropea
todo lo de abajo, así que el informe se ordena alrededor del primer agujero.

### Bloque 1 · ¿Te reparten? (25 puntos)
Si YouTube puede entender de qué va el canal y decidir a quién enseñárselo.
1. **Nicho y coherencia temática** — ¿se sabe de qué va el canal leyendo 12 títulos?
2. **Ritmo y constancia** — vídeos por mes, los huecos reales, si acelera o se apaga.
3. **Formato y duración** — largo frente a Shorts, duraciones y su coherencia.
4. **Buscabilidad y ficha técnica** — título, descripción, capítulos, hashtags,
   etiquetas, idioma y subtítulos.

### Bloque 2 · ¿Hacen clic? (25 puntos)
El bloque de más palanca de YouTube y el que casi nadie trabaja.
5. **Miniatura: legibilidad** — a tamaño de móvil: un foco, poco texto, contraste.
6. **Miniatura: sistema** — ¿se reconoce el canal sin leer el nombre?
7. **Títulos: promesa y curiosidad** — longitud, lo importante delante, concreción.
8. **La pareja título + miniatura** — si se repiten o se suman, y si cumplen.

### Bloque 3 · ¿Se quedan? (25 puntos)
9. **El gancho** — los primeros 5-15 segundos, leídos de la transcripción real.
10. **Estructura y ritmo** — capítulos, forma de la curva, relleno, dónde se cae.
11. **Se cumple la promesa** — si el vídeo da lo que el título prometía, y cuándo.
12. **Producción que afecta a que se queden** — audio, subtítulos, texto en pantalla.

### Bloque 4 · ¿Vuelven y te compran? (25 puntos)
13. **Conversión a suscriptor** — cuántas visitas le cuesta un suscriptor.
14. **Sesión y catálogo** — listas, series, secciones, tráiler, enlaces entre vídeos.
15. **Comunidad** — comentarios y me gusta por mil visitas, si responde.
16. **Negocio y activo propio** — qué vende, si se ve, y si tiene algo suyo o toda
    su audiencia está alquilada a YouTube.

**Cada dimensión se puntúa de 0 a 100** con anclajes fijos (0-20 no existe · 21-40
mal o abandonado · 41-60 lo mínimo · 61-80 bien con fallos concretos · 81-100
referencia de su nicho). La nota del bloque es la media de sus cuatro dimensiones
llevada a 25, con la operación a la vista. La global es la suma:

**0-39 crítico · 40-59 flojo · 60-74 aceptable · 75-89 bueno · 90-100 referencia**

Un canal pequeño que no crece suele estar entre 25 y 50. Un 80 es un canal que ya
vive de esto.

### El titular no es la nota: es **la fuga**

La fuga es el eslabón donde se le cae la mayoría de la gente:

```
impresiones  →  clics (CTR)  →  retención  →  suscriptores / negocio
```

Con las capturas de Studio se localiza contando dónde se pierde más gente en
números absolutos. Sin ellas, es el primer bloque que baja de 15/25. Y hay una
regla que evita el error clásico de estos informes: **el dato medido manda sobre el
juicio del mecanismo.** Si sus impresiones son altas, el bloque 1 no es la fuga
aunque su ficha técnica esté mal — ahí es margen de mejora, no la causa.

### El análisis de outliers

La parte más accionable. Se calcula la **mediana** de visitas del canal (solo
vídeos de entre 28 días y 18 meses, para que la edad no falsee la comparación) y se
mide cada vídeo contra ella: **≥3× fuerte · 1,5-3× por encima · 0,5-1,5× normal ·
<0,5× por debajo**. Y después lo que de verdad vale: **qué tienen en común los de
arriba** (tema, tipo de título, tipo de miniatura, duración) y por qué no lo ha
vuelto a repetir. Casi nadie repite lo que le funcionó.

---

## Qué te llevas

Todo va a `workspace/`:

| Archivo | Qué es |
|---|---|
| `youtube-[canal].html` | **El informe.** 14 secciones, autocontenido, imprimible en PDF, con la galería de miniaturas comentada y el embudo dibujado |
| `[canal]-packaging.md` | **Lo que se paga**: 5 títulos y miniaturas suyos reescritos (antes/después), los **próximos 10 vídeos** con título + miniatura descrita + gancho de 10 segundos + duración objetivo, y la plantilla de descripción con capítulos y hashtags |
| `[canal]-hallazgos.md` | El cuaderno del análisis, dimensión a dimensión. Si la sesión se corta, con "continúa el análisis" se retoma sin repetir nada |
| `miniaturas-[canal]/` | Las miniaturas descargadas. El informe las muestra desde ahí |
| `datos/` | Los datos crudos, para profundizar después sin volver a descargar |

Las 14 secciones del informe: cabecera · titulares con la nota y la fuga · la prueba
de la portada (lo que ve alguien que llega por primera vez) · resumen ejecutivo · el
embudo dibujado · la tabla de vídeos con su multiplicador · los outliers y qué
tienen en común · las 16 dimensiones con su evidencia · **la galería de miniaturas
comentada** · títulos antes y después · los ganchos palabra por palabra · los
próximos 10 vídeos · **lo que NO debe cambiar** · nota metodológica.

---

## Cómo se usa

```
/setup                                        (la primera vez, en este ordenador)
analiza este canal: https://youtube.com/@handle
analiza el canal de ejemplo                   (práctica, sin internet)
```

Y después, en lenguaje normal:

```
continúa el análisis
profundiza en las miniaturas
dame 10 ideas más de vídeo
reescríbeme estos 5 títulos
compara este canal con estos dos: [enlace] [enlace]
analiza 30 vídeos en vez de 12
```

**La muestra**: por defecto se analizan a fondo los **12 vídeos largos más
recientes**, los **3 más vistos de la historia** del canal y **6 Shorts**, y el
listado completo de títulos y fechas para el ritmo. Se puede ampliar pidiéndolo; cada vídeo extra
son un par de segundos más de extracción.

---

## El canal de práctica

`ejemplos/canal-de-practica/` contiene **Huerto en Casa**, un canal de huerto urbano
ficticio (41.300 suscriptores, 214 vídeos) con **16 errores metidos a propósito**:
nicho difuso, ritmo roto con un hueco de siete semanas, títulos sin promesa, una
miniatura con once palabras de texto, un gancho de 22 segundos de presentación, la misma
descripción copiada en todos los vídeos con 19 hashtags (más de 15: YouTube los
ignora todos), cero capítulos en vídeos de 20 minutos, Shorts de temas que el canal
no trata, ninguna lista de reproducción y **un vídeo con 487.000 visitas frente a
una mediana de 8.900 que no ha vuelto a repetir**.

Se analiza **sin internet** (todo el material está transcrito en archivos), gasta
una fracción de un análisis real y sirve para ver el sistema completo antes de
usarlo con un canal de verdad. Incluye las estadísticas de Studio, así que también
se ve cómo se localiza la fuga con datos medidos.

---

## Lo que este kit no hace

- **No juzga a la persona.** Analiza el canal: packaging, contenido, ritmo, negocio.
  Nada sobre su aspecto, su cuerpo, su voz, su acento ni su vida privada, ni aunque
  se lo pidas. De su cara en la miniatura solo dice si cumple su función.
- **No inventa nada.** Ni visitas, ni CTR, ni retención, ni RPM. Los datos de
  referencia del sector van con su fuente y su fecha, y nunca disfrazados de datos
  del canal analizado. Lo que no se pudo comprobar sale como "sin datos".
- **No confunde la curva pública con la retención.** Los "momentos más vistos" son
  una curva relativa y el informe lo dice cada vez que la usa.
- **No toca el canal.** No publica, no responde comentarios, no cambia miniaturas.
  No necesita ninguna cuenta ni contraseña.
- **No descarga vídeos.** Solo metadatos, subtítulos y miniaturas.

---

## Qué cuesta usarlo

**Nada más allá de tu Claude Code.** No hay API de pago, no hay clave de YouTube, no
hay cuenta de Google, no hay suscripción a herramientas de terceros. `yt-dlp` es
gratuito y de código abierto.

Lo único que consume es tu propio uso de Claude: un análisis completo es del orden
de un rato largo de conversación. El de práctica gasta bastante menos porque no
descarga nada.

---

## Y cobrarlo

Rangos de mercado 2026, orientativos — la decisión es tuya:

- **Análisis de canal**: 300-700 € para un canal pequeño o mediano; 900-1.800 € con
  presentación en directo y plan de contenidos.
- **Packaging por vídeo** (título + miniatura + gancho): 60-150 €/vídeo, o
  400-900 €/mes por paquete de 4-8 vídeos.
- **Gestión de canal** (estrategia + packaging + calendario): 800-2.500 €/mes.

Para presentarlo: el HTML se enseña en pantalla compartida o se manda en PDF (en el
navegador, imprimir → guardar como PDF). El orden que funciona: la prueba de la
portada → la galería de miniaturas comentada → dónde está la fuga → los títulos
reescritos → los próximos 10 vídeos. La galería es lo que más impresiona, porque se
ve el trabajo hecho sobre sus propias imágenes.

Dentro del informe no van tus tarifas: el informe se le puede enseñar al dueño del
canal.

---

## Estructura del kit

```
04-kit-analisis-youtube/
├── EMPIEZA-AQUI.md        ← 3 pasos para arrancar
├── README.md              ← este archivo
├── CLAUDE.md              ← el cerebro: cómo se comporta Claude en este kit
├── .claude/
│   ├── commands/setup.md  ← el wizard (/setup)
│   ├── commands/canal.md  ← el comando estrella (/canal)
│   └── skills/analisis-canal-youtube/SKILL.md   ← el sistema completo
├── entrada/LEEME.md       ← el guion de las 4 capturas opcionales de Studio
├── ejemplos/canal-de-practica/   ← el canal ficticio con 16 errores
└── workspace/             ← aquí aparecen tus informes
```

## Si algo falla

Cuéntaselo a Claude pegando el error **literal**: el kit trae una tabla de errores
conocidos con su solución (herramienta desactualizada, 403, 429, vídeos sin curva
pública, canales sin Shorts…) y sabe resolverlos. Si tras dos intentos sigue
atascado, pregunta en la comunidad donde conseguiste el kit pegando el error tal
cual.
