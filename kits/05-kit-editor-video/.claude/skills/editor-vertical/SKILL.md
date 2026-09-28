---
name: editor-vertical
description: "Convierte un vídeo en bruto en un vertical publicable de 1080x1920: transcribe con marca de tiempo por palabra, quita silencios, muletillas y tomas repetidas, recorta a vertical con el encuadre que elige el usuario, quema subtítulos karaoke palabra a palabra, añade rótulos y mockups animados, zooms sobre las frases importantes, efectos de sonido y volumen igualado a -14 LUFS. Todo local con ffmpeg y un modelo de voz en el propio ordenador. Usa esta skill cuando el usuario quiera editar un vídeo, hacerlo vertical, ponerle subtítulos, cortar los silencios, montar un TikTok, un Reel o un Short, retocar un vídeo ya editado o mejorar el ritmo de un clip. Triggers: 'edita este vídeo', 'hazme esto vertical', 'ponle subtítulos', 'córtame los silencios', 'móntame este TikTok', 'pásalo a formato Reel', 'quítale las pausas', 'métele zooms', 'ponme un rótulo', 'corta más', 'ha cortado de más', 'continúa el vídeo'."
---

# Editor de vídeo vertical

Entra un vídeo tal como salió de la cámara. Sale un vertical de 1080x1920 con
subtítulos quemados, sin pausas muertas y con ritmo. Nueve pasos, todos en el
ordenador del usuario.

**Regla fundamental: los subtítulos no se inventan.** Salen de la transcripción,
palabra por palabra, con su marca de tiempo. Si una palabra no se entiende, se
pregunta o se corrige a mano en `trabajo/correcciones.json` — nunca se completa con
"lo que tendría sentido". Poner en boca del usuario algo que no dijo es el peor fallo
posible de este kit.

**Segunda regla: el vídeo original no se toca.** Todo lo generado va a
`workspace/<nombre>/`.

**Tercera regla: narra, no calles.** Cada paso lleva su tiempo (la transcripción son
minutos). Di en una línea qué estás haciendo y qué va a tardar. El silencio largo se
interpreta como que se ha colgado.

En este documento los comandos se escriben con `python`. Usa el que diga el campo
`python` de `.claude/setup-completado.json` (`python3` en Mac, `python` o `py` en
Windows).

---

## Paso 0 — Antes de empezar

1. Si no existe `.claude/setup-completado.json`, el kit no está instalado: manda a
   `/setup` y para. No intentes editar; fallaría a mitad.
2. Localiza el vídeo. En `entrada/`, o donde diga el usuario. Si hay varios
   candidatos, lista los que hay con su duración y pregunta cuál.
3. Si el vídeo dura más de 4 minutos, avisa antes: va a tardar aproximadamente su
   propia duración en procesarse y va a ocupar disco. Ofrece editar solo un trozo si
   lo que quiere es un clip corto.

## Paso 1 — Abrir el proyecto

```
python scripts/nuevo.py "<ruta del vídeo>"
```

Con `--nombre <slug>` si quiere un nombre concreto. Devuelve la duración, el tamaño,
los fps y los avisos que importen. Relee los avisos y tradúcelos:

- **Sin pista de audio** → no hay transcripción, ni subtítulos, ni cortes por
  silencio. Pregunta si grabó el sonido aparte. Se puede seguir solo para pasarlo a
  vertical con rótulos, y hay que decirlo.
- **Ya es vertical** → perfecto, el paso del encuadre casi no quita nada.
- **Rotado** (vídeo de móvil) → el kit ya lo tiene en cuenta; solo confírmalo.
- **Muy corto** (menos de 5 s) → hay poco que cortar; el valor estará en los
  subtítulos.

Resume al usuario lo que has recibido en dos líneas. Sin jerga: "4 minutos y 12
segundos, horizontal, con sonido".

## Paso 2 — Transcribir

```
python scripts/transcribir.py "<proyecto>" --idioma es
```

Pon `--idioma es` cuando sepas que habla en español: la detección automática falla
con vídeos que empiezan con música o con un silencio.

**Avisa antes de lanzarlo**: la primera vez descarga el modelo de voz (unos 500 MB) y
son varios minutos sin señales de vida. Después, es aproximadamente medio minuto por
minuto de vídeo.

Cuando acabe, di cuántas palabras ha reconocido y **lee las primeras frases en voz
alta al usuario**. Es la comprobación más útil de todo el proceso: si la
transcripción está mal, todo lo que viene detrás sale mal, y aquí se ve gratis.

Si el resultado es malo:

| Síntoma | Qué hacer |
|---|---|
| Palabras sueltas, texto inconexo | `--modelo medium --refrescar` (más lento, bastante mejor) |
| Transcribe en otro idioma | `--idioma es --refrescar` |
| Nombres técnicos mal escritos ("cloud" por "Claude") | El kit ya corrige los habituales; añade los tuyos a `trabajo/correcciones.json` |
| Casi nada reconocido | El audio es el problema. Dilo con franqueza antes de seguir |

Opciones y criterios completos: `referencias/cortes.md`.

## Paso 3 — Decidir los cortes

```
python scripts/plan_cortes.py "<proyecto>"
```

Imprime el plan: qué se quita y por qué. **Cuéntaselo antes de aplicar nada**, en
lenguaje normal y con los números:

> "De 4:12 se queda en 2:48. Le quito 23 silencios, 6 muletillas y 2 veces que
> repetiste la misma frase (me quedo con la última). Las pausas de menos de medio
> segundo las acorto, no las quito: si no, suena atropellado."

Y pregunta si quiere ajustar algo antes de cortar. Ajustes:

| Quiere | Comando |
|---|---|
| Más ritmo | `--umbral 0.40` |
| Menos agresivo | `--umbral 0.75` |
| Dejar las muletillas | `--sin-muletillas` |
| Dejar las tomas repetidas | `--sin-tomas` |
| No tocar las pausas cortas | `--sin-micropausas` |

Los criterios de cada señal, en `referencias/cortes.md`.

## Paso 4 — El encuadre (aquí decide el usuario)

**Este paso no se salta y no se adivina.** Un vídeo horizontal no cabe en vertical:
se tira más de la mitad de la imagen. Elegir mal significa un vídeo entero con la
cara cortada.

```
python scripts/encuadre.py "<proyecto>"
```

Deja tres fotogramas en `trabajo/encuadre/` con una regla del 0 al 100 % y el
rectángulo de recorte dibujado. Ábrelos para el usuario (`open` en Mac, `start` en
Windows) y **míralos tú también**: puedes leer imágenes, así que propón un valor en
vez de preguntar en abstracto.

> "Estás en la mitad izquierda del encuadre, sobre el 35 %. Propongo centrar ahí y
> se te ve entero. ¿Lo dejo así?"

Cuando esté decidido:

```
python scripts/encuadre.py "<proyecto>" --centro 0.35
```

Si la acción se mueve por todo el plano (una pantalla compartida, dos personas), el
recorte no vale. Entonces:

```
python scripts/encuadre.py "<proyecto>" --modo marco
```

Mete el vídeo entero dentro del vertical, con su propio fondo desenfocado detrás. Se
ve todo, a cambio de que la imagen sea más pequeña. Explícale el intercambio así, con
esas palabras.

## Paso 5 — Cortar y pasar a vertical

```
python scripts/cortar.py "<proyecto>"
```

Una sola pasada de ffmpeg: recorta los trozos, los pega, pasa a vertical y deja 60
fps. Sale `trabajo/master.mp4`. Con `--calidad 14` para más calidad (archivo más
grande), `--calidad 20` para menos.

Es el paso más lento después de transcribir. Avisa: aproximadamente medio minuto por
minuto de vídeo.

Si ya existe y hay que rehacerlo (se cambió el encuadre o el plan), `--refrescar`.

## Paso 6 — Subtítulos

```
python scripts/subtitulos.py "<proyecto>"
```

Karaoke: grupos de hasta 4 palabras, y la palabra que se está diciendo se enciende en
naranja. Se dibujan como imágenes PNG con transparencia, no con el filtro de texto de
ffmpeg — por eso salen igual en Mac y en Windows.

Los cambios de estilo (tamaño, colores, altura, palabras por grupo) van en
`proyecto.json`, en la clave `subs`, y luego `--refrescar`. Los valores y qué
significa cada uno: `referencias/estilo.md`.

## Paso 7 — Rótulos, mockups y zooms (opcional)

Este paso es el que convierte un vídeo correcto en un vídeo que parece producido. Es
opcional: si Playwright o Chrome no están, se salta y el vídeo se termina igual.

**Rótulos y mockups.** Escribe `trabajo/visuales.json`:

```json
{"visuales": [
  {"nombre": "intro", "plantilla": "titulo", "inicio": 0.4,
   "datos": {"lineas": ["Esto no es", "*un editor* normal"], "visible": 2.0}},
  {"nombre": "paso1", "plantilla": "rotulo", "inicio": 12.6,
   "datos": {"texto": "Paso 1", "sub": "Instalar el kit", "visible": 2.4}}
]}
```

Y genera:

```
python scripts/capturar.py "<proyecto>"
```

Las seis plantillas con sus datos exactos, en `referencias/visuales.md`. Los tiempos
(`inicio`) van en segundos **del vídeo ya cortado**, no del original: mira
`trabajo/subs.json` para saber en qué segundo se dice cada cosa.

**Zooms.** Se escriben a mano en `trabajo/timeline.json`, en la clave `zooms`. Con
2 o 3 en un vídeo de un minuto sobra: sirven para subrayar la frase importante, y
puestos en todas partes marean. También en `referencias/visuales.md`.

## Paso 8 — Montar

```
python scripts/componer.py "<proyecto>"
```

Apila en una sola pasada: el vídeo cortado, los zooms, las capas de rótulos, las
imágenes fijas y, encima de todo, los subtítulos. Sale `trabajo/montaje.mp4`.

## Paso 9 — Cerrar el sonido

```
python scripts/sonido.py "<proyecto>"
```

Iguala la voz a **-14 LUFS** (el nivel de TikTok, Instagram y YouTube) y mezcla los
efectos. Si no existe `trabajo/sfx.json`, escribe una propuesta sobria y la usa: un
barrido corto en los saltos largos. Se puede retocar y volver a correr con
`--refrescar`. El catálogo y los criterios, en `referencias/sonido.md`.

Deja el vídeo terminado en **`workspace/<nombre>/<nombre>-vertical.mp4`**.

## Cierre

1. Abre el vídeo para que lo vea (`open` / `start`).
2. Di en dos líneas qué ha pasado, con números: de cuánto a cuánto, cuántos cortes,
   cuántos subtítulos.
3. Ofrece los retoques más pedidos, que son siempre los mismos: más cortes, otro
   encuadre, subtítulos más grandes, un rótulo al principio.
4. Recuérdale que los intermedios de `trabajo/` se pueden borrar cuando esté
   contento: ocupan bastante.

---

## Retocar un vídeo ya hecho

No se rehace todo. Se vuelve al paso mínimo y se avanza desde ahí:

| Cambio | Se rehace desde |
|---|---|
| Más o menos cortes | Paso 3, luego 5 → 9 (con `--refrescar` en `cortar.py`) |
| Otro encuadre | Paso 4, luego 5 → 9 |
| Subtítulos (estilo, tamaño, posición) | Paso 6 con `--refrescar`, luego 8 → 9 |
| Corregir una palabra mal transcrita | `trabajo/correcciones.json`, paso 6 `--refrescar`, luego 8 → 9 |
| Añadir o quitar un rótulo | Paso 7, luego 8 → 9 |
| Añadir zooms | `timeline.json`, luego 8 → 9 |
| Efectos de sonido o volumen | Paso 9 con `--refrescar` |

Transcribir es lo caro: **no se repite nunca** salvo que la transcripción sea el
problema.

## Continuar un vídeo cortado

`proyecto.json` guarda en `pasos` qué está hecho. Lee ese archivo, di por dónde iba
en una línea ("ya estaba transcrito y cortado, faltaban los subtítulos") y sigue por
el primero que falte. Nada de empezar de cero: transcribir otra vez son minutos
tirados.

## Cuando algo no se puede comprobar

Si un paso no se puede hacer en este ordenador (no hay Chrome para los rótulos, no
hay audio para transcribir), la regla es: **seguir con lo que sí se puede y decirlo
claro**. Un vídeo vertical con subtítulos y sin rótulos es un buen vídeo. Un vídeo
que no se ha hecho porque faltaba un rótulo no es nada.

Lo que **nunca** se hace: rellenar un hueco inventando. Ni una palabra en un
subtítulo, ni un tiempo, ni un dato sobre lo que dice el vídeo.

## Referencias

| Archivo | Cuándo abrirlo |
|---|---|
| `referencias/cortes.md` | Ajustar qué se quita: umbrales, muletillas, tomas repetidas, transcripción |
| `referencias/estilo.md` | Cambiar los subtítulos: tamaño, colores, posición, agrupación |
| `referencias/visuales.md` | Rótulos, mockups, zooms e imágenes fijas: las seis plantillas y sus datos |
| `referencias/sonido.md` | Efectos de sonido, catálogo, volumen y niveles |
| `referencias/errores.md` | Cuando algo falla y no está en la tabla de `CLAUDE.md` |
