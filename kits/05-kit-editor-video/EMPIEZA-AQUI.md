# Kit 05 · Empieza aquí — 15 minutos y a editar

Este kit convierte Claude Code en tu editor de vídeo. Le das el vídeo tal como
salió de la cámara —horizontal, con silencios, con tus "eeeh" y con la frase que
repetiste tres veces— y te devuelve un **vertical de 1080x1920 con subtítulos
quemados**, las pausas muertas fuera y ritmo. Todo en tu ordenador: nada se sube a
ningún sitio y no hay ninguna clave que pagar. 4 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code" →
   Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con suscripción
   (Pro o superior) o con cuenta API de Anthropic.
3. **Python** — en python.org/downloads, el botón grande. Es el idioma en el que
   está escrito el motor del kit.
   - **En Windows, en la primera pantalla del instalador marca la casilla
     "Add python.exe to PATH"**. Se olvida todo el mundo y sin ella el kit no lo
     encuentra. Si te has pasado, vuelve a lanzar el instalador y marca la casilla.
   - En Mac, el instalador normal, dos clics.
4. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo
   "siguiente") — Claude Code lo necesita para funcionar.

No hace falta instalar ffmpeg, ni Homebrew, ni ningún programa de vídeo: de eso se
encarga el paso 4 y no te va a pedir la contraseña del ordenador.

## Paso 2 · Abre la carpeta

- Antes de nada: si aún ves el kit dentro del ZIP, descomprímelo (en Windows: clic
  derecho sobre el ZIP → "Extraer todo") y trabaja siempre con la carpeta extraída
  — nunca desde dentro del ZIP.
- En VS Code: `Archivo → Abrir carpeta...` y elige esta carpeta del kit.
- Abre Claude Code desde el panel lateral. La primera vez te preguntará en inglés
  *"Do you trust the files in this folder?"* — elige **Yes, proceed** (es un aviso
  estándar de seguridad). Mientras trabaja también te pedirá algún permiso en
  inglés (botones "Allow" o "Yes"): es normal, acéptalos.

## Paso 3 · Deja el vídeo a mano

Arrastra tu vídeo a la carpeta **`entrada/`** del kit. Vale cualquier cosa que
salga de un móvil o de una cámara: `.mp4`, `.mov`, `.mkv`, `.webm`.

¿No tienes nada grabado? En **`ejemplos/GUION-DEMO.md`** tienes un guion de 20
segundos para grabar con el móvil ahora mismo, pensado para que se vea funcionando
todo. Y si quieres verlo antes de grabar nada, el paso 4 fabrica su propio vídeo de
prueba.

## Paso 4 · Escribe /setup

El asistente instala lo que falta (unos 700 MB de descargas, una sola vez y sin
contraseña de administrador), y después **se comprueba a sí mismo editando un vídeo
de prueba que fabrica él**: te enseña el resultado en vertical, con subtítulos y con
un rótulo. Si eso sale bien, el kit funciona en tu ordenador. Sin más.

Luego, editar es una frase:

```
edita este vídeo
```

## Lo único que tienes que saber antes de grabar

**No edites nada a mano.** Habla seguido y déjalo todo: las pausas para pensar, los
"eeeh", y la frase que has repetido cuatro veces hasta que salió bien. El kit quita
los silencios, quita las muletillas y, cuando repites una toma, **se queda con la
última**. Cortarlo tú antes solo le quita información y te quita tiempo.

Dos cosas más que ayudan mucho:

- **Habla mirando a un lado fijo del encuadre.** Si grabas en horizontal, la mitad
  de la imagen se va a ir (en vertical no cabe): el kit te preguntará qué franja se
  queda, y es más fácil si no te mueves de lado a lado.
- **Graba el sonido lo mejor que puedas.** Los subtítulos salen de entender lo que
  dices: con ruido de fondo o con la mano tapando el micro, salen peor. Los
  auriculares del móvil ya son mejores que nada.

## Cuánto tarda

| | |
|---|---|
| Instalación (una vez) | 5-15 minutos, casi todo descargas |
| Editar un vídeo | Alrededor de **1 minuto por cada minuto de vídeo** |
| La primera transcripción | Suma unos minutos: baja el modelo de voz (500 MB, una vez) |

Va todo en tu ordenador, así que en un portátil antiguo tarda más. No consume nada
de tu plan de Claude: el vídeo lo procesa tu máquina, no el modelo.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| "Python was not found" o se abre la tienda de Microsoft | Python no está instalado (eso es un atajo vacío de Windows) | Instálalo de python.org marcando "Add python.exe to PATH", cierra VS Code y vuelve a abrirlo |
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| Se queda parado varios minutos al transcribir por primera vez | Está bajando el modelo de voz (500 MB) | Espera. Es una sola vez |
| "No encuentro ffmpeg" | El programa de vídeo no se descargó | Dile a Claude: *"instala ffmpeg"*. Lo baja dentro del kit, sin contraseña |
| Los rótulos no salen pero el vídeo sí | Falta el Chrome interno de los rótulos | Es opcional: el vídeo se hace igual. Si los quieres, dile *"instala los visuales"* |
| El vídeo sale con tu cara cortada | Se eligió mal la franja vertical | Dile *"la cara está más a la izquierda"* y lo vuelve a montar |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan de Claude | Espera a que se restablezca. Lo ya hecho no se pierde: al volver di *"continúa el vídeo"* |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué hace cada paso, qué se puede cambiar y qué no
hace el kit.
