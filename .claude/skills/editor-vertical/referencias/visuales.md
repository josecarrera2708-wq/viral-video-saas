# Rótulos, mockups, zooms e imágenes

Todo lo de este archivo es **opcional**. Si Playwright o su Chrome no están, este
paso se salta y el vídeo se termina igual, con subtítulos y sin rótulos. Dilo y sigue;
no bloquees un vídeo por un rótulo.

## Cómo se generan (y por qué así)

No se graba la pantalla. Cada plantilla es una página HTML que expone una función
`fotograma(t)`: se le pide el instante 0,4 s y coloca todo exactamente como estaría en
0,4 s. Playwright pide fotograma a fotograma y guarda PNG con transparencia. Por eso
el resultado es idéntico siempre, aunque el ordenador vaya lento o esté haciendo otra
cosa — que es justo lo que falla cuando se graba la pantalla.

```
python scripts/capturar.py "<proyecto>" [--previa] [--solo <nombre>] [--limpiar]
```

| Opción | Para qué |
|---|---|
| `--previa` | Una sola imagen de cada visual, del centro de su animación. Rápido: úsalo para que el usuario apruebe el diseño antes de generar cientos de PNG |
| `--solo <nombre>` | Regenerar un único visual sin tocar los demás |
| `--limpiar` | Borrar las imágenes anteriores antes de generar |
| `--fps N` | Por defecto 30 (el montaje lo sube a 60). A 60 tarda el doble y casi no se nota |

Los visuales se declaran en **`trabajo/visuales.json`**. Si no existe, el script lo
crea vacío con la lista de plantillas disponibles.

```json
{"visuales": [
  {"nombre": "intro", "plantilla": "titulo", "inicio": 0.4,
   "datos": {"lineas": ["Esto no es", "*un editor* normal"], "visible": 2.0}},
  {"nombre": "paso1", "plantilla": "rotulo", "inicio": 12.6,
   "datos": {"texto": "Paso 1", "sub": "Instalar el kit", "visible": 2.4}}
]}
```

| Clave | Qué es |
|---|---|
| `nombre` | Identificador libre. Da nombre a los archivos y permite `--solo` |
| `plantilla` | Una de las seis (abajo) |
| `inicio` | Segundo en que entra, **del vídeo ya cortado** |
| `datos` | Lo que cambia según la plantilla |
| `x`, `y` | Opcionales: mueven el visual. Cada plantilla ya tiene su sitio |

**Los tiempos son del vídeo cortado, no del original.** Para saber en qué segundo se
dice cada cosa, abre `trabajo/subs.json`: lleva el texto de cada grupo con su instante
en el vídeo final. Poner el `inicio` a ojo es el error más habitual aquí.

En cualquier texto, `*lo que sea*` sale resaltado en color. Es el único marcado.

## Las seis plantillas

`visible` es siempre **cuánto tiempo se queda quieto en pantalla**, sin contar la
entrada ni la salida. La duración total la calcula la plantilla sola.

### `rotulo` — el de todos los días

Cae abajo (y=980), justo encima de los subtítulos. Es el 80 % de los casos.

```json
{"texto": "Paso 1", "sub": "Instalar el kit", "visible": 2.4}
```

| Dato | Por defecto |
|---|---|
| `texto` | `"Rótulo"` |
| `sub` | vacío (si está vacío, no se pinta la segunda línea) |
| `visible` | 2.4 s (mínimo 0.6) |

### `titulo` — el titular a pantalla completa

Va arriba (y=300). Las líneas entran en cascada, una detrás de otra.

```json
{"lineas": ["Esto no es", "*un editor* normal"], "ante": "KIT 05",
 "visible": 2.2, "centrado": false}
```

| Dato | Por defecto |
|---|---|
| `lineas` | Una lista. **Una frase por línea, cortada donde tú quieras** que se rompa |
| `ante` | Pastilla pequeña encima del titular (vacío = no se pinta) |
| `visible` | 2.2 s |
| `centrado` | `false` (alineado a la izquierda, que se lee mejor en vertical) |
| `tamano` | 0 = automático. La plantilla baja el tamaño sola si hay líneas largas o 4+ líneas |

Con más de 4 líneas el texto se queda pequeño. Si hace falta más, son dos títulos
seguidos, no uno con ocho líneas.

### `mockup-movil` — una conversación de chat

Va casi arriba (y=190). Máximo 8 mensajes; los que sobran se ignoran.

```json
{"quien": "Claude", "visible": 1.8, "mensajes": [
  {"de": "yo", "texto": "Hazme el vídeo vertical"},
  {"de": "otro", "escribiendo": true},
  {"de": "otro", "texto": "Hecho: 1080x1920 con subtítulos"}
]}
```

| Dato | Qué es |
|---|---|
| `quien` | Nombre en la cabecera. Su inicial hace de avatar |
| `mensajes` | Hasta 8. `"de": "yo"` sale a la derecha; cualquier otra cosa, a la izquierda |
| `escribiendo: true` | Pinta los tres puntitos en vez de texto. Un mensaje así, antes de la respuesta, es lo que hace que parezca real |
| `visible` | 1.8 s **después** del último mensaje |

Las burbujas entran una a una: cuatro mensajes ya son varios segundos. Cuenta con eso
al elegir el `inicio`.

### `mockup-terminal` — comandos escribiéndose

Va a media altura (y=400). Máximo 12 líneas.

```json
{"nombre": "Terminal", "visible": 1.8, "lineas": [
  {"tipo": "comando", "texto": "claude"},
  {"tipo": "salida",  "texto": "Cargando el kit…"},
  {"tipo": "ok",      "texto": "Listo"}
]}
```

| `tipo` | Se pinta con | Cómo aparece |
|---|---|---|
| `comando` | `$` | Se escribe letra a letra, con cursor |
| `salida` | espacio | Aparece de golpe |
| `ok` | `✓` verde | Aparece de golpe |
| `error` | `✗` rojo | Aparece de golpe |

Un tipo desconocido se trata como `salida`. Los comandos tardan en escribirse: tres
comandos largos son varios segundos.

### `recap` — la lista de puntos

Va a media altura (y=360). Máximo 6 puntos, que entran en cascada.

```json
{"titulo": "Lo que hace", "marca": "check", "visible": 1.6,
 "puntos": ["Corta los silencios", "Pone subtítulos", "Lo hace vertical"]}
```

| Dato | Por defecto |
|---|---|
| `titulo` | vacío (sin título, la lista empieza arriba) |
| `puntos` | Hasta 6, frases cortas |
| `marca` | `"numero"` (1, 2, 3) o `"check"` (✓) |
| `visible` | 1.6 s |

Para el resumen del final o para enumerar mientras se habla. Los puntos aparecen al
ritmo de la cascada, no todos de golpe: si el usuario los va diciendo, cuadra.

### `cta` — la llamada a la acción del final

Va en el centro-bajo (y=540).

```json
{"frase": "El kit es *gratis*", "boton": "Link en la bio",
 "nota": "Solo esta semana", "visible": 2.4}
```

| Dato | Por defecto |
|---|---|
| `frase` | vacío |
| `boton` | `"Link en la bio"` |
| `nota` | vacío |
| `visible` | 2.4 s |

## Dónde cae cada plantilla

Nada de esto choca con los subtítulos (que van sobre y=1300) ni con la interfaz de la
red social:

| Plantilla | y |
|---|---|
| `mockup-movil` | 190 |
| `titulo` | 300 |
| `recap` | 360 |
| `mockup-terminal` | 400 |
| `cta` | 540 |
| `rotulo` | 980 |

Si dos visuales coinciden en el tiempo y en la altura, se pisan. Míralo antes: o los
separas en el tiempo, o le pones `y` a mano a uno de los dos.

## Zooms

No hay script: se escriben a mano en **`trabajo/timeline.json`**, clave `zooms`. Es un
archivo que `capturar.py` respeta — regenerar los rótulos no borra los zooms.

```json
{"zooms": [
  {"inicio": 8.2, "fin": 11.0, "z": 1.18, "modo": "resorte"}
]}
```

| Clave | Por defecto | Qué es |
|---|---|---|
| `inicio`, `fin` | — | Segundos del vídeo cortado |
| `z` | 1.15 | Cuánto amplía. 1.10 se nota poco, 1.30 ya es mucho |
| `modo` | `"resorte"` | `resorte` entra con un rebote pequeño; `suave` arranca y frena despacio |

Detalles que importan: el zoom se hace sobre una ampliación al doble de tamaño, así no
da saltos; lleva un temblor mínimo de cámara en mano, porque sin eso parece una
diapositiva; y el encuadre se va un poco hacia el tercio alto, que es donde está la
cara.

**Dos o tres zooms en un vídeo de un minuto sobran.** Sirven para subrayar la frase
importante. Puestos en todas partes marean y el vídeo parece nervioso, no dinámico.
Si el usuario pide "zooms por todas partes", ponle tres en las frases fuertes y
enséñaselo antes de llenar el vídeo.

## Imágenes o clips a pantalla completa

También en `timeline.json`, clave `fijas`. Una captura de pantalla, una foto, un clip
de apoyo:

```json
{"fijas": [
  {"archivo": "entrada/captura.png", "inicio": 14.0, "fin": 17.0}
]}
```

La ruta puede ser absoluta o relativa a la carpeta del kit. La imagen se recorta para
llenar el vertical entero y entra y sale con un fundido corto (0,18 s). Si el archivo
no está, se avisa y se salta esa capa: el vídeo se monta igual.

Esto es también la respuesta a *"tápame esto de la pantalla"*: una imagen encima de la
zona, en el tramo que haga falta.

## El orden de las capas

De abajo a arriba: vídeo cortado → zooms → rótulos y mockups → imágenes fijas →
**subtítulos, siempre encima de todo**. Ningún efecto puede tapar un subtítulo.

## Si los visuales no se pueden generar

`playwright`, `chromium`, `Executable doesn't exist`: falta el Chrome sin ventana.

```
python -m pip install playwright
python -m playwright install chromium
```

Son unos 150 MB y un par de minutos, una vez. Si no se puede instalar (disco, red,
un ordenador restringido), dilo con franqueza y **sigue sin rótulos**: el vídeo con
subtítulos ya está bien. Lo que no se hace nunca es dejar el vídeo sin terminar por
esto.
