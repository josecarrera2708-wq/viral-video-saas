# Kit 05 · Editor de Vídeo Vertical — para Claude Code

Le das el vídeo tal como salió de la cámara. Te devuelve el vídeo publicable.

| | |
|---|---|
| **Entra** | Un vídeo en bruto: horizontal, con silencios, con muletillas, sin subtítulos |
| **Sale** | Vertical 1080x1920 a 60 fps, subtítulos quemados palabra a palabra, silencios fuera, volumen igualado y efectos |
| **Dónde** | En tu ordenador. Nada se sube a ningún servidor |
| **Coste** | Cero. Sin claves, sin suscripciones de vídeo, sin marcas de agua |
| **Tiempo** | Alrededor de 1 minuto de proceso por minuto de vídeo |

Funciona igual en Mac y en Windows. No consume tu plan de Claude editando: el vídeo
lo trabaja tu máquina; el modelo solo dirige.

## Empezar

Lee `EMPIEZA-AQUI.md` (4 pasos, 15 minutos) y escribe `/setup`. El wizard instala lo
que falta y **se comprueba a sí mismo editando un vídeo de prueba**, así que sabes
que funciona antes de gastar tu primer vídeo de verdad.

Después, todo se pide hablando:

```
edita este vídeo
corta más, quedan pausas
la cara está más a la izquierda
ponme un rótulo que diga "Paso 1" en el segundo 12
```

## Los nueve pasos

Cada paso deja su resultado en disco. Si algo se corta —se cierra el portátil, se va
la luz, se acaba tu límite de Claude— se retoma por donde iba sin repetir nada.

**1 · Se abre el proyecto.** Se lee el vídeo y se avisa de lo que puede dar guerra:
que no tenga audio, que ya sea vertical, que venga rotado desde el móvil.

**2 · Se transcribe con marca de tiempo en cada palabra.** No basta saber qué se
dice: hay que saber en qué milisegundo empieza cada palabra, porque de ahí salen los
subtítulos que se encienden solos y la detección de silencios. Lo hace un modelo de
voz que corre en tu ordenador (faster-whisper), gratis y sin internet.

**3 · Se decide qué se quita.** Cuatro señales, combinadas:

- **Silencios de verdad**, medidos en el audio (no solo huecos entre palabras).
- **Pausas largas** entre palabras, que se acortan a un tiempo natural en vez de
  eliminarse: quitarlas del todo suena atropellado.
- **Muletillas** ("eeeh", "mmm", "o sea" repetido) cuando están sueltas.
- **Tomas repetidas**: si dices "el primero es… el primero es que…", se queda con la
  segunda. Esto es lo que más tiempo ahorra y es lo que nadie hace a mano.

Antes de cortar, se te cuenta qué se va a quitar y cuánto va a durar el resultado.

**4 · Eliges el encuadre.** Aquí decides tú, y es el único paso donde hace falta.
Un vídeo horizontal no cabe en vertical: hay que tirar la mitad de la imagen. El kit
te saca tres fotogramas con una regla encima y le dices dónde estás: *"un poco a la
izquierda"*. También puede meter el vídeo entero dentro de un marco, con su propio
fondo desenfocado detrás, si la acción se mueve por todo el plano.

**5 · Se corta y se pasa a vertical**, todo en una sola recompresión. Una sola
importa: cada vez que se recomprime un vídeo se pierde calidad, y las cadenas de
herramientas mal hechas recomprimen cinco veces.

**6 · Se dibujan los subtítulos.** Estilo karaoke: la palabra que se está diciendo se
enciende. Se dibujan como imágenes con transparencia, no con el filtro de texto de
ffmpeg ni con archivos `.ass`. Es una decisión importante: así el resultado es
idéntico en Mac y en Windows y no depende de cómo esté compilado el ffmpeg de cada
uno, que es de donde vienen la mitad de los problemas con los subtítulos quemados.

**7 · Rótulos y mockups** (opcional). Seis plantillas animadas —rótulo, titular,
móvil con un chat, terminal, recapitulación, llamada a la acción— que se generan
fotograma a fotograma en un Chrome sin ventana. No se graba la pantalla: se le pide
el fotograma 12 y se guarda el fotograma 12, así que el resultado es idéntico
siempre, aunque el ordenador vaya lento. Si esta parte no se puede instalar, el kit
edita igual y solo te quedas sin rótulos.

**8 · Se monta todo en una pasada**: los zooms sobre las frases importantes, las
capas de rótulos, las imágenes que quieras meter a pantalla completa y, encima de
todo, los subtítulos.

**9 · Se cierra el sonido.** El volumen se iguala a **-14 LUFS**, que es el nivel al
que suenan TikTok, Instagram y YouTube. Si no se hace, tu vídeo se oye más bajo que
el resto del feed y la gente pasa de largo. Y se mezclan los efectos: un barrido
corto en los saltos, un golpe en los rótulos.

## Qué hay en el kit

| Carpeta | Qué es |
|---|---|
| `entrada/` | Donde sueltas los vídeos en bruto |
| `workspace/` | Un proyecto por vídeo, con el resultado y todos los intermedios |
| `scripts/` | El motor: 13 programas de Python — uno por paso, más los de instalación y prueba |
| `plantillas/` | Las seis plantillas de rótulos y mockups, en HTML |
| `assets/fuentes/` | Tres tipografías variables con licencia libre (OFL) |
| `assets/sfx/` | 19 efectos de sonido con licencia de uso libre (Pixabay) |
| `ejemplos/` | El guion para grabar tu clip de prueba de 20 segundos |
| `bin/` | Aparece al instalar: aquí vive el ffmpeg del kit |

## Lo que se puede cambiar (sin tocar nada, hablando)

| Quieres | Dices algo como |
|---|---|
| Más ritmo | "corta más" — se baja el umbral de silencio |
| Menos agresivo | "ha cortado de más, se come palabras" |
| Dejar las muletillas | "no me quites los 'eeeh'" |
| Otro encuadre | "la cara está más a la derecha" / "que se vea el vídeo entero" |
| Otros subtítulos | "más grandes", "más abajo", "de tres en tres palabras", "en amarillo" |
| Un rótulo | "un rótulo que diga 'Paso 1' cuando empiezo a explicar" |
| Zooms | "métele zoom donde digo lo importante" |
| Sin efectos | "quítale los sonidos" |

## Lo que este kit NO hace

Se dice antes para que no haya sorpresas:

- **No genera vídeo ni voz.** Edita lo que tú has grabado. No hay avatares, no hay
  voz sintética, no hay imágenes creadas.
- **No escribe tu guion.** Eso es otro kit.
- **No arregla un audio malo.** Iguala el volumen y quita silencios, pero si grabaste
  con viento y el micro tapado, se notará. Mejora, no resucita.
- **No pone música.** Efectos cortos sí; una canción de fondo no, porque lo que
  puedes publicar depende de la licencia de esa canción y eso es decisión tuya.
- **No sube nada a ninguna red.** El vídeo terminado se queda en tu carpeta; lo
  publicas tú.
- **No hace vídeos largos cómodamente.** Está pensado para clips de hasta 3-4
  minutos. Con una hora de grabación funcionaría, pero tardaría una hora y ocuparía
  mucho disco: para eso, primero corta el trozo que te interesa.

## Privacidad

Todo pasa en tu ordenador. La transcripción usa un modelo local: **tu audio no sale
de la máquina**, ni siquiera para transcribir, y una vez instalado funciona en avión.

Hay un motor de transcripción opcional (AssemblyAI) que es algo más preciso con
audio malo. Ese **sí sube el audio a un servidor externo** y necesita una clave de
pago. Está documentado, no está activado, y si lo pides se te avisa antes. Su clave,
si la usas, va a `.env.local`, que nunca viaja con el kit.

## Si usas Windows

Funciona igual, con dos avisos:

- Al instalar Python, **marca "Add python.exe to PATH"** en la primera pantalla del
  instalador. Es el fallo más común de todos.
- ffmpeg se instala dentro del kit, no en el sistema: no hace falta winget, ni tocar
  variables de entorno, ni permisos de administrador.

## Cuánto ocupa

| | |
|---|---|
| El kit descargado | Unos 3 MB |
| ffmpeg (se descarga al instalar) | Unos 90 MB, dentro de `bin/` |
| Modelo de voz | Unos 500 MB, una vez, en la carpeta de tu usuario |
| Chrome de los rótulos | Unos 150 MB, una vez (opcional) |
| Mientras monta un vídeo de 1 minuto | Hasta 2 GB temporales en `workspace/` |

Para desinstalarlo del todo: borra la carpeta del kit. Lo único que queda fuera es el
modelo de voz, en la caché de tu usuario.

## Si el vídeo se corta a mitad

No se pierde nada. Cada paso escribe su resultado, y `proyecto.json` guarda por
dónde iba. Al volver, dile *"continúa el vídeo"* y sigue por el primer paso que
falte.

## Cómo se cobra esto (rangos de mercado 2026)

Si editas para otros: **edición de un vídeo vertical corto 25-60 €**, **paquete de 8
vídeos al mes 250-500 €**, **gestión completa de contenido vertical (edición +
publicación + miniaturas) 600-1.500 €/mes**. Un clip que a mano son 40 minutos aquí
son 3 de trabajo tuyo, y ahí está el margen. El precio lo pones tú.
