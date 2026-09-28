---
description: Instala todo lo que necesita el kit y lo comprueba editando un vídeo de prueba
---

Eres el wizard de instalación del Kit Editor de Vídeo Vertical. Guía al usuario en
español, sin jerga, y **sin pedirle nunca que abra una terminal: los comandos los
ejecutas tú**. Valida cada paso antes de darlo por bueno (✓ o ✗ por línea) y
termina siempre diciendo la siguiente acción concreta.

Este kit sí instala programas de verdad (a diferencia de los otros): ffmpeg, que
corta y recomprime el vídeo, y un modelo de voz que transcribe lo que se dice.
Nada de eso pide contraseña de administrador ni cambia nada fuera de la carpeta
del kit. Dilo pronto, porque es la duda número uno.

Ejecuta estos pasos EN ORDEN. No te salgas del orden aunque parezca redundante:
cada paso comprueba lo que el siguiente da por hecho.

## 0 · Saludo (máximo 6 líneas)

Qué es el kit (un vídeo horizontal con silencios entra, un vertical de 1080x1920
con subtítulos quemados sale), qué vas a hacer ahora (instalar y probarlo con un
vídeo que fabricas tú mismo) y cuánto tarda: **5 a 15 minutos la primera vez**, casi
todo descargas. Avisa de que va a haber ratos en silencio mientras descarga y que
eso es normal.

## 1 · Python

Todo el motor del kit es Python. Compruébalo así, y quédate con el comando que
funcione:

- Mac o Linux: `python3 --version`
- Windows: `python --version` y, si falla, `py --version`

Tiene que responder con un número **3.9 o superior**. Ojo en Windows: si sale
*"Python was not found"* o se abre la tienda de Microsoft, Python NO está
instalado (eso es un atajo vacío que trae Windows).

Si no está:

- **Windows**: que lo instale desde python.org/downloads, y **muy importante**, que
  marque la casilla *"Add python.exe to PATH"* en la primera pantalla del
  instalador. Es la casilla que se olvida todo el mundo y sin ella no lo
  encontraremos. Después tiene que **cerrar y volver a abrir VS Code**.
- **Mac**: que lo instale desde python.org/downloads (el instalador normal, dos
  clics). Si prefiere no instalar nada, `xcode-select --install` también lo trae,
  pero tarda más.

Anota el comando que funciona (`python3`, `python` o `py`): lo vas a usar en todos
los pasos siguientes y lo guardarás al final. En este documento se escribe
`python`; sustitúyelo por el que funcione en este ordenador.

## 2 · Revisión completa

Ejecuta:

```
python scripts/doctor.py --json
```

Te devuelve un JSON con un punto por cada cosa que el kit necesita, y cada uno con
su estado (`ok`, `aviso`, `falta`) y su arreglo. Resúmeselo al usuario en lista
corta, con ✓ para lo que ya está y el nombre en cristiano de lo que falta. No le
pegues el JSON.

Lo que verás normalmente en un ordenador limpio: falta ffmpeg, falta Pillow, falta
faster-whisper y falta Playwright. Es lo esperado, no un problema.

## 3 · Instalación

Ejecuta:

```
python scripts/doctor.py --instalar
```

Esto hace, por este orden y sin pedir contraseña:

1. Descarga **ffmpeg y ffprobe** (unos 90 MB) dentro de la carpeta `bin/` del kit.
   No se instala en el sistema a propósito: así no hace falta Homebrew ni winget
   ni permisos de administrador, y se desinstala borrando esa carpeta.
2. Instala los paquetes de Python: **Pillow** (dibuja los subtítulos),
   **faster-whisper** (transcribe) y **playwright** (los rótulos animados).
3. Descarga el **Chrome sin ventana** que usan los rótulos (unos 150 MB).

Tarda entre 3 y 10 minutos según la conexión. Ve diciendo por dónde va.

Si algo falla, mira la tabla de errores de `CLAUDE.md` antes de improvisar. Los dos
casos frecuentes:

- **pip no puede instalar** (`externally-managed-environment`, permisos): el propio
  doctor reintenta sin `--user`. Si sigue fallando, el kit no puede seguir; pásale
  el error literal y dile que pregunte en la comunidad.
- **La descarga de ffmpeg falla** (red de empresa que bloquea GitHub): ejecuta
  `python scripts/instalar_ffmpeg.py` para ver el mensaje completo, que ya trae la
  vía alternativa para su sistema.

Cuando acabe, vuelve a ejecutar `python scripts/doctor.py --json` y confirma que
`listo` es `true`. Si `visuales` es `false`, no pasa nada: el kit edita igual y solo
se queda sin rótulos animados. Díselo así, sin dramatismo.

## 4 · El modelo de voz (avisa antes)

La transcripción usa un modelo que se descarga la primera vez que se transcribe:
**unos 500 MB**. No lo descargues aparte: se baja solo en el paso siguiente. Lo que
tienes que hacer es **avisar antes de lanzarlo**, porque son varios minutos con la
pantalla quieta y sin barra de progreso, y sin el aviso parece que se ha colgado.

Dilo en una línea: *"ahora va a descargar el modelo de voz, unos 500 MB, una sola
vez; puede tardar varios minutos sin dar señales de vida"*.

## 5 · La prueba de verdad (esto es lo que decide si está listo)

No des el kit por instalado porque los programas existan. Compruébalo editando:

```
python scripts/prueba.py --json
```

Este script fabrica él mismo un vídeo horizontal de unos 13 segundos con la voz del
propio ordenador, silencios largos metidos a propósito y una frase dicha dos veces
seguidas. Y lo pasa por **toda** la cadena: transcribir, decidir cortes, pasar a
vertical, dibujar subtítulos, un rótulo, montar y mezclar sonido.

Después comprueba el resultado, no solo que no diera error: que mida 1080x1920, que
tenga sonido, que dure menos que el original (o sea, que cortó los silencios) y que
la transcripción encontrara palabras.

Lee el JSON y actúa:

- `"ok": true` → di lo que ha comprobado con datos concretos del propio JSON:
  duración original vs. final, cuántos grupos de subtítulos y las primeras palabras
  que leyó (`muestra_subtitulos`). Si `toma_repetida_detectada` es `true`,
  menciónalo: es la parte que más sorprende, ha quitado sola la toma repetida.
- `"avisos"` con algo dentro → tradúcelo y ponlo en su sitio: un aviso no rompe el
  kit. El habitual es que el ordenador no tenga lector de textos (entonces la
  prueba va con tonos y la transcripción queda sin comprobar hasta el primer vídeo
  de verdad).
- `"ok": false` → NO digas que está listo. El campo `error` dice en qué paso se
  rompió y con el mensaje real de ese paso. Arréglalo y vuelve a lanzar la prueba.
  Máximo 2 intentos; después, comunidad con el error literal.

Abre el vídeo de prueba para que lo vea con sus ojos (`open` en Mac, `start` en
Windows) y dile qué tiene que ver: vertical, subtítulos que se encienden palabra a
palabra y el rótulo "Instalación correcta". Que lo mire de verdad: es la única forma
de saber que ha salido bien.

Cuando lo haya visto, límpialo:

```
python scripts/prueba.py --limpiar
```

## 6 · Deja el terreno listo y recuerda lo aprendido

- Crea las carpetas `entrada/` y `workspace/` si no existen.
- Si ya hay vídeos en `entrada/`, dilo: son los que va a poder editar.
- Escribe `.claude/setup-completado.json` con:

```json
{
  "fecha": "AAAA-MM-DD",
  "sistema": "Darwin | Windows | Linux",
  "python": "python3 | python | py",
  "ffmpeg": "la ruta que devolvió el doctor",
  "visuales": true,
  "prueba_ok": true,
  "segundos_prueba": 11
}
```

`segundos_prueba` es el `segundos_totales` que devolvió la prueba: sirve para saber
cómo de rápido es este ordenador y ajustar lo que le digas que va a tardar.

Ese archivo es lo que indica que el kit ya está instalado en este ordenador, y el
campo `python` evita que en cada sesión haya que volver a averiguar qué comando
funciona aquí.

## 7 · Primer vídeo

Cierra con el resumen de ✓ (una línea) y las dos salidas, en este orden:

- **Con un vídeo tuyo**: "arrastra un vídeo a la carpeta `entrada/` y dime *edita
  este vídeo*". Recuérdale lo único que importa al grabar: hablar seguido y **no
  cortar los silencios ni las repeticiones a mano**, que de eso se encarga el kit.
- **Con el ejemplo**: si no tiene nada a mano, en `ejemplos/` está el guion de un
  clip de 20 segundos que puede grabar con el móvil ahora mismo
  (`ejemplos/GUION-DEMO.md`), pensado para que se vea funcionando todo: cortes,
  subtítulos y un rótulo.

Y avisa de lo que va a tardar el primer vídeo de verdad, para que no se preocupe:
**alrededor de 1 minuto de proceso por cada minuto de vídeo** en un portátil normal,
casi todo en la transcripción.
