# Subtítulos: estilo y agrupación

Los subtítulos se dibujan con Pillow como imágenes PNG con fondo transparente, y se
pegan encima del vídeo. **No se usa el filtro de texto de ffmpeg ni archivos `.ass`**,
y es una decisión deliberada: así el resultado es idéntico en Mac y en Windows y no
depende de cómo esté compilado el ffmpeg de cada uno. La mitad de los problemas con
subtítulos quemados vienen de ahí.

```
python scripts/subtitulos.py "<proyecto>" [--refrescar]
```

## Cómo se agrupan las palabras

Un grupo se cierra cuando pasa cualquiera de estas cosas:

| Regla | Valor |
|---|---|
| Máximo de palabras por grupo | 4 |
| Máximo de caracteres por grupo | 18 |
| Hueco entre palabras que abre grupo nuevo | 0,55 s |
| Fin de frase (`.` `?` `!` `…`) | siempre corta |
| Salto entre dos trozos cortados | siempre corta |

18 caracteres es poco a propósito: en vertical, con el tamaño necesario para que se
lea en un móvil a pulso, no cabe más de una línea corta. Grupos largos obligan a
bajar el tamaño y entonces no se leen, que es el error clásico.

Cada grupo aparece 0,08 s antes de su primera palabra y se queda 0,12 s después de la
última. Si dos grupos van muy pegados (menos de 0,25 s), el cambio es seco, sin
fundido: un fundido en ese hueco parpadea.

## Cambiar el estilo

Los cambios van en `proyecto.json`, en la clave `subs`. Solo lo que se quiera cambiar;
el resto se queda como está:

```json
{
  "subs": {
    "tamano": 88,
    "y": 1240,
    "color_activo": "#FFD400"
  }
}
```

Y luego `python scripts/subtitulos.py "<proyecto>" --refrescar` y volver a componer.

| Clave | Por defecto | Qué es |
|---|---|---|
| `tamano` | 78 | Alto de la letra en píxeles, sobre un lienzo de 1080x1920 |
| `color_texto` | `#FFFFFF` | Las palabras que no se están diciendo |
| `color_activo` | `#FF7A00` | La palabra que suena en ese instante |
| `y` | 1300 | Altura de la tira dentro del vídeo, desde arriba |
| `margen` | 56 | Aire a izquierda y derecha |
| `borde` | 8 | Grosor del contorno negro que hace legible el texto sobre cualquier fondo |
| `sombra` | 0.45 | Opacidad de la sombra bajo el texto (0 = sin sombra) |

### Sobre la altura (`y`)

1300 no es un número arbitrario. Por debajo de ~1400 los subtítulos chocan con lo que
TikTok e Instagram pintan encima del vídeo: el nombre de la cuenta, el texto del pie,
los botones de la derecha. Y por encima de ~1100 tapan la cara.

| Situación | Valor |
|---|---|
| Por defecto, seguro en las tres redes | 1300 |
| El usuario aparece muy abajo en el encuadre | 1150-1200 |
| Vídeo para YouTube Shorts solamente | Hasta 1450 |
| Modo marco (franjas arriba y abajo) | 1360, sobre la franja negra |

### Traducciones para el usuario

No hables de píxeles ni de claves JSON. Traduce:

| Dice | Cambia |
|---|---|
| "más grandes" | `tamano` +12 |
| "más pequeños" | `tamano` -10 |
| "más arriba" / "tapan mucho" | `y` -100 |
| "más abajo" | `y` +80, y avisa si pasa de 1400 (los tapa la app) |
| "en amarillo" | `color_activo`: `#FFD400` |
| "sin naranja", "que no cambie de color" | `color_activo` igual que `color_texto` |
| "de dos en dos palabras" | Hay que tocar `MAX_PALABRAS` en `scripts/subtitulos.py` (arriba, con `MAX_CARACTERES`). Es un cambio en el motor: hazlo si lo pide, y dile que afecta a todos los vídeos |
| "no se leen sobre el fondo claro" | `borde` 10 y `sombra` 0.6 |

## Palabras mal transcritas

No se arreglan aquí: se arreglan en `trabajo/correcciones.json` (ver
`referencias/cortes.md`) y se rehace este paso. Nunca cambies el texto de un subtítulo
para que "quede mejor": el subtítulo tiene que decir lo que dijo el usuario.

## Vídeo sin voz

Si la transcripción no encontró palabras, este paso lo dice y se salta solo. El vídeo
se termina sin subtítulos. Avisa al usuario: probablemente es que el audio no se
entiende, no que el kit falle.
