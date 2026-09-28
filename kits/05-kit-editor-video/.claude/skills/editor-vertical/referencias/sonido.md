# Sonido: nivel y efectos

Último paso. Iguala el volumen de la voz y mezcla los efectos. Es el paso que deja el
archivo final en `workspace/<nombre>/<nombre>-vertical.mp4`.

```
python scripts/sonido.py "<proyecto>" [--refrescar] [--sin-efectos] [--sin-nivelar]
```

## El nivel: -14 LUFS

TikTok, Instagram y YouTube normalizan a **-14 LUFS**. Un vídeo que sale más bajo se
oye más flojo que el resto del feed y la gente pasa de largo; uno que sale más alto lo
bajan ellos, y de paso lo aplastan. Así que se lleva ahí, con el pico máximo en
-1,5 dB para que no sature al recomprimir.

Se mide en **dos pasadas**: primero se analiza el audio entero, luego se corrige con la
medida ya conocida. En una sola pasada el filtro va corrigiendo a medida que avanza, y
las primeras palabras del vídeo quedan a otro volumen que el resto — se nota, y es un
fallo típico de las cadenas hechas con prisa.

El script imprime el nivel de partida ("la voz está en -23,4 LUFS; se lleva a -14").
Menciónaselo al usuario cuando pregunte si el sonido está bien: es un número, no una
opinión.

| Situación | Qué decir |
|---|---|
| Original muy bajo (-30 LUFS o menos) | Se sube, pero **sube también el ruido de fondo**. Mejora, no arregla |
| Original saturado (picos recortados) | La saturación ya está grabada. No se puede quitar. Dilo claro |
| `--sin-nivelar` | Solo si el usuario ya ha masterizado el audio por su cuenta |

Al final pasa por un limitador suave (`alimiter` a 0,95) para que ningún efecto se
sume a la voz y reviente el pico.

## Los efectos

Los efectos van en **`trabajo/sfx.json`**. Si el archivo no existe, el script escribe
una propuesta sobria y la usa:

```json
{"eventos": [
  {"sonido": "whoosh-short", "t": 4.82, "ganancia": 0.24, "nota": "salto de 1.3 s"}
]}
```

| Clave | Qué es |
|---|---|
| `sonido` | Nombre del catálogo (abajo) |
| `t` | Segundo **del vídeo montado** en que suena |
| `ganancia` | Volumen. 1.0 = el archivo original. Si no se pone, se usa la del catálogo |
| `alinear` | `"inicio"` o `"final"`. Si no se pone, la del catálogo |
| `nota` | Texto libre, solo para acordarse de por qué está ahí |

Se puede editar y volver a correr con `--refrescar`. Con `--sin-efectos` se monta solo
la voz.

### `alinear`: por dónde se cuadra el efecto

Un barrido que sube durante cinco segundos y revienta al final no se coloca por donde
empieza, se coloca **por donde revienta**. Con `"alinear": "final"`, `t` es el instante
del golpe y el efecto arranca antes solo. Es la diferencia entre un efecto que cuadra
y uno que suena tarde.

Si un efecto de 5 s alineado por el final se pone en `t: 2.0`, no hay carrerilla
suficiente: se avisa y entra recortado.

### La propuesta automática

Un barrido corto (`whoosh-short`, ganancia 0,24) en cada salto de más de **0,70 s** de
silencio quitado, máximo **12**, y se queda con los saltos más largos, que son los que
más se notan.

Un efecto en cada corte cansa y suena a plantilla; en los saltos largos ayuda a
entender que ahí faltaba algo. Es deliberadamente poco. Límite duro: 60 efectos en un
vídeo — más que eso es ruido, no edición.

## El catálogo

19 efectos en `assets/sfx/`, con **licencia Pixabay Content License**: uso comercial
permitido, sin atribución obligatoria. La ficha de cada uno está en
`assets/sfx/sonidos.json` con su duración, su volumen recomendado y para qué sirve.

| Sonido | Dur. | Gan. | Alinear | Para qué |
|---|---|---|---|---|
| `whoosh-short` | 0,57 | 0,28 | inicio | **El de los cortes.** Movimiento rápido, transición ágil |
| `whoosh` | 0,57 | 0,35 | inicio | Barrido con pegada: un revelado rápido, un corte duro que se quiere marcar |
| `whoosh-cinematic` | 5,54 | 0,30 | **final** | Transición de escena grande. Revienta justo en el corte |
| `riser` | 10,03 | 0,30 | **final** | Subida que estalla en el momento fuerte. Solo si el vídeo da para diez segundos |
| `impact-bass-1` | 2,12 | 0,45 | inicio | Golpe de graves. Un titular que entra de golpe, un logotipo |
| `impact-bass-2` | 2,59 | 0,45 | **final** | Golpe con crescendo previo: cae en el revelado |
| `glitch-1` | 2,64 | 0,40 | inicio | Interferencia con pegada. Corte seco o aparición repentina |
| `glitch-2` | 3,50 | 0,35 | inicio | Interferencia larga y agresiva. Con cuentagotas: cansa enseguida |
| `glitch-3` | 3,10 | 0,30 | inicio | Textura digital discreta, por debajo de la voz |
| `click` | 0,37 | 0,35 | inicio | Se pulsa un botón. En el fotograma exacto |
| `click-soft` | 0,37 | 0,30 | inicio | Clic discreto: un toque en pantalla, una opción que se marca |
| `key-press` | 0,40 | 0,35 | inicio | Una sola tecla, un intro |
| `typing` | 1,50 | 0,30 | inicio | Ráfaga de teclado. Va con el mockup de terminal |
| `pop` | 0,72 | 0,30 | inicio | Algo que aparece, una etiqueta que entra |
| `ping` | 1,32 | 0,35 | inicio | Subraya un dato o una cifra en pantalla |
| `chime` | 2,50 | 0,35 | inicio | Algo sale bien, una confirmación |
| `notification` | 2,46 | 0,35 | inicio | Entra un mensaje, aparece un cartelito |
| `sparkle` | 1,80 | 0,30 | inicio | Brillo o destello, algo que reluce |
| `error` | 1,62 | 0,35 | inicio | Algo ha ido mal, un «no», una interrupción brusca |

Un nombre que no esté en el catálogo se avisa y se salta: el vídeo se monta igual.

## Cómo elegir

Los volúmenes del catálogo están pensados para ir **por debajo de la voz**. Si un
efecto tapa lo que se dice, el problema es la ganancia, no el efecto: bájala a la
mitad antes de cambiar de sonido.

| El usuario dice | Haz |
|---|---|
| "no me gustan los sonidos" | `--sin-efectos --refrescar`. Un vídeo sin efectos está bien |
| "se oyen muy fuerte" | Baja las ganancias a la mitad y `--refrescar` |
| "ponle un golpe cuando sale el rótulo" | `impact-bass-1` en el `inicio` de ese visual |
| "algo cuando escribo en la terminal" | `typing` cuando empieza a escribirse |
| "un sonido de transición largo" | `whoosh-cinematic` con `"alinear": "final"` en el instante del corte |
| "ponle música" | Este kit no pone música: lo que puedas publicar depende de la licencia de esa canción, y esa decisión es suya. Ofrécele que la añada él en la app donde publique |
| "sale muy bajito" | Ya está a -14 LUFS. Enséñale el nivel de partida que imprimió el script y explica qué se puede y qué no |

Emparejar cada efecto con lo que pasa en pantalla es lo que separa un vídeo editado de
un vídeo con sonidos encima. Si no hay nada que subrayar, mejor silencio: los efectos
puestos por rellenar suenan a plantilla y se notan más que su ausencia.

## Vídeo sin voz

Si el vídeo no tiene pista de audio, se monta un silencio de base y se mezclan los
efectos encima (el mezclador necesita algo sobre lo que mezclar). El vídeo sale con
sonido; solo que el sonido son los efectos.
