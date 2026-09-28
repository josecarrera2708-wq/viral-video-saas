# Cuando algo falla

La tabla de `CLAUDE.md` cubre lo habitual. Esto es lo de después: los mensajes
literales del motor, los fallos que no dan error y qué hacer cuando nada encaja.

**Regla de oro: no repitas el comando que falló.** Estos scripts explican en el propio
mensaje qué ha pasado y qué comando lo arregla. Léelo entero antes de actuar.

## Primero: ¿el kit o este vídeo?

Antes de investigar nada, decide en qué lado está el problema. Son dos comandos:

```
python scripts/doctor.py --json     ¿están los programas?
python scripts/prueba.py --json     ¿funciona la cadena completa?
```

| Doctor | Prueba | Dónde está el problema |
|---|---|---|
| Falta algo | — | Instalación. `doctor.py --instalar` |
| Todo bien | Falla | El kit. Mira qué paso de la prueba cayó: ahí está |
| Todo bien | Pasa | **Este vídeo concreto.** El kit funciona; algo de ese archivo no |

El doctor comprueba que los programas *están*, no que *funcionen*. `prueba.py` fabrica
su propio vídeo con voz sintética y lo edita de punta a punta: eso sí lo comprueba.
Cuando el doctor sale verde y editar falla, `prueba.py` es el siguiente paso, no
volver a mirar el doctor.

En el JSON del doctor: `listo` (si se puede editar), `visuales` (si hay rótulos), y
cada punto con estado `ok`, `aviso` o `falta`. **`aviso` no bloquea nada**: son los
visuales, el modelo de voz sin descargar o el disco justo.

## Mensajes del motor, literales

| Mensaje | Qué pasa | Qué haces |
|---|---|---|
| `No encuentro 'ffmpeg', el programa que trabaja con el vídeo` | No está en este ordenador | `python scripts/instalar_ffmpeg.py`. Sin contraseña, dentro del kit |
| `Tu ffmpeg viene recortado` / `falta libx264` | Hay un ffmpeg del sistema sin codificadores (típico de builds mínimos de Linux o de instalaciones a medias) | `python scripts/instalar_ffmpeg.py --forzar`. La copia de `bin/` tiene prioridad sobre la del sistema |
| `No encuentro el vídeo en <ruta>` | La ruta no existe o tiene un espacio mal escapado | Pídele que arrastre el archivo al chat: sale la ruta buena. Y comilla siempre las rutas |
| `Ese archivo dura 0.0s o no es un vídeo que ffmpeg entienda` | Archivo corrupto, descarga a medias, o no es vídeo | Que lo abra en su reproductor. Si tampoco se abre, el archivo está roto: no es cosa del kit |
| `No encuentro el vídeo original en <ruta>. Corrige 'origen' en proyecto.json` | El vídeo se movió o se renombró después de empezar | Localiza el archivo y corrige el campo `origen` de `proyecto.json`. No hace falta rehacer nada |
| `El plan tiene N trozos y eso es demasiado para una pasada` | Más de 400 cortes: pasa con vídeos largos y umbral muy bajo | `plan_cortes.py --umbral 0.9` para agrupar. O edita solo un trozo del vídeo |
| `No module named 'faster_whisper'` (o `PIL`, o `playwright`) | Falta un paquete de Python | `python scripts/doctor.py --instalar` |
| `Falta la tipografía '<familia>' en assets/fuentes` | El kit se descargó incompleto o se descomprimió a medias | Que vuelva a descargar y descomprimir el kit. No se puede arreglar de otra forma: las tipografías vienen dentro |
| `El vídeo no tiene pista de audio` | Grabó sin sonido o el sonido va aparte | Sin audio: no hay transcripción, ni subtítulos, ni cortes por silencio. Se puede pasar a vertical con rótulos. Pregunta si grabó el sonido por separado |
| `El centro va de 0.0 a 1.0 (0.5 es el medio)` | Se pasó `--centro 35` en vez de `0.35` | Es un fallo tuyo al escribir el comando, no del usuario |
| `Falló: ffmpeg …` con doce líneas debajo | Error de ffmpeg. Las últimas líneas dicen cuál | Lee esas líneas: casi siempre es disco lleno, un archivo que falta o un filtro con un tiempo imposible |
| `Executable doesn't exist` (Playwright) | Falta el Chrome de los rótulos | `python -m playwright install chromium`. Si no se puede, **sigue sin rótulos** |
| `AssemblyAI respondió 401` | Clave mal o caducada | La clave va en `.env.local`, nunca en el chat. O vuelve al motor local: `--motor whisper` |
| `AssemblyAI tarda demasiado` | Su servidor va lento o la subida se cortó | `--motor whisper --refrescar`. Es local, gratis y no depende de nadie |
| `No space left on device` | Disco lleno | Un vídeo de un minuto puede ocupar 2 GB mientras se monta. Borra las carpetas `trabajo/` de proyectos terminados |

## Fallos que no dan error

Los peores: el comando termina bien y el resultado está mal. Aquí no hay mensaje que
leer, hay que mirar.

| Lo que se ve | Causa real | Solución |
|---|---|---|
| Subtítulos con palabras que el usuario no dijo | La transcripción entendió otra cosa | `trabajo/correcciones.json` y rehacer el paso 6. **Nunca lo arregles escribiendo el texto que "debería" decir** |
| Subtítulos en otro idioma | Detección automática fallida (vídeo que empieza con música o con un "hola" suelto) | `transcribir.py --idioma es --refrescar` |
| La cara cortada en todo el vídeo | Encuadre mal elegido en el paso 4 | `encuadre.py --centro <otro>` y `cortar.py --refrescar`. Si la acción se mueve, `--modo marco` |
| El vídeo suena atropellado, sin respirar | Se quitaron también las pausas cortas | `plan_cortes.py --sin-micropausas` |
| Se come el final de las palabras | Umbral demasiado bajo | `--umbral 0.75` |
| Falta una frase entera que el usuario quería | El detector de tomas repetidas la tomó por un tropiezo | Abre `plan-cortes.json`, cambia ese segmento a `"mantener"` y `cortar.py --refrescar`. O `--sin-tomas` |
| El vídeo sale del revés o tumbado | Rotación en los metadatos del móvil | El kit ya lo tiene en cuenta. Si aun así pasa, guarda la salida de `nuevo.py`: hace falta para arreglarlo de verdad |
| Los rótulos se pisan entre ellos | Dos visuales a la vez a la misma altura | Sepáralos en el tiempo o pon `y` a mano (`referencias/visuales.md`) |
| Un rótulo aparece cuando no toca | El `inicio` se puso en segundos del vídeo **original** | Los tiempos son del vídeo cortado. Mira `trabajo/subs.json` |
| Un efecto suena tarde | Efecto con carrerilla alineado por el inicio | `"alinear": "final"` (`referencias/sonido.md`) |
| El vídeo se oye más bajo que el resto del feed | El paso 9 no se corrió, o se corrió con `--sin-nivelar` | `sonido.py --refrescar` |

## Cuando se corta a mitad

Se cierra el portátil, se va la luz, se acaba el límite de uso. **No se pierde nada.**

`proyecto.json` guarda en `pasos` qué está hecho. Léelo, di en una línea por dónde iba
("ya estaba transcrito y cortado, faltaban los subtítulos") y sigue por el primero que
falte. Transcribir otra vez son minutos tirados a la basura.

Si un archivo intermedio quedó a medias (se cortó justo al escribirlo), el paso que lo
usa dará un error de JSON o de archivo corrupto. Ese paso concreto se rehace con
`--refrescar`; los anteriores no se tocan.

## Windows

| Síntoma | Qué es |
|---|---|
| Se abre la Microsoft Store al llamar a Python | Es el atajo vacío que trae Windows. Python **no** está instalado: python.org, marcando "Add python.exe to PATH" |
| `python` no funciona pero `py` sí | Normal. El campo `python` de `setup-completado.json` guarda el que va: úsalo |
| Rutas con acentos o eñes que fallan | Comilla siempre las rutas. Si sigue fallando, mueve el vídeo a `entrada/` con un nombre sin acentos |
| Antivirus bloquea la descarga de ffmpeg | Pásale la ruta de `bin/` como excepción, o que baje ffmpeg a mano y lo ponga ahí. Dile qué carpeta es |
| `pip install --user` falla | El script ya reintenta sin `--user`. Si tampoco, es un Python restringido: puede hacer falta otro Python |

## Antes de rendirse

1. Un solo intento de arreglo. Si falla, uno más. **Al segundo, para.**
2. Deja el vídeo en el mejor estado posible. Un vertical con subtítulos y sin rótulos
   es un buen vídeo; uno sin terminar no es nada.
3. Dile con franqueza qué funciona y qué no. Sin adornos y sin echarle la culpa a su
   ordenador.
4. Mándale a la comunidad donde consiguió el kit **pegando el error literal**, no un
   resumen. El mensaje completo es lo que permite ayudarle.
5. Si has averiguado algo que no estaba escrito, **añade la fila** a la tabla de
   `CLAUDE.md` antes de cerrar. El siguiente que lo tenga no debería investigarlo otra
   vez.

Lo que no se hace nunca, por muy atascado que estés: rellenar un hueco inventando. Ni
una palabra de un subtítulo, ni un tiempo, ni un dato sobre lo que dice el vídeo.
