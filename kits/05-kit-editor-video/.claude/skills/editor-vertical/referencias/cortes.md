# Cortes y transcripción

Cómo decide el kit qué se queda y qué se va, y cómo ajustarlo cuando al usuario no
le cuadra el ritmo.

## Transcribir

```
python scripts/transcribir.py "<proyecto>" [--modelo small] [--idioma es] [--refrescar]
```

| Modelo | Tamaño | Velocidad | Cuándo |
|---|---|---|---|
| `tiny` | 75 MB | Muy rápido | Solo para probar que la cadena funciona |
| `base` | 145 MB | Rápido | Audio muy limpio y vídeo largo con prisa |
| `small` | 500 MB | ~0,5x tiempo real | **Por defecto.** El equilibrio bueno |
| `medium` | 1,5 GB | ~1,5x tiempo real | Audio con ruido, acentos marcados, mucha jerga |
| `large-v3` | 3 GB | ~3x tiempo real | Solo si `medium` no basta y el usuario acepta la espera |

Cambiar de modelo obliga a `--refrescar`: si no, reutiliza la transcripción anterior.

**Pon siempre `--idioma es`** cuando sepas que habla español. La detección automática
mira los primeros segundos, y un vídeo que empieza con música o con un "hola" suelto
se detecta mal, con lo que sale una transcripción entera en portugués o en italiano.

Cada palabra sale con su probabilidad. Por debajo de 0,4 la transcripción "no lo tiene
claro", y eso es lo que usa la detección de muletillas.

### Corregir palabras mal transcritas

Los nombres técnicos son el punto débil de cualquier modelo de voz. El kit ya corrige
los habituales de estos vídeos ("cloud", "cloude", "clau" → Claude; "yipiti" → GPT;
"gitjub" → GitHub). Para añadir los del usuario, `trabajo/correcciones.json`:

```json
{"nombre mal oido": "Nombre Correcto", "sant mun": "santmun"}
```

Las claves van en minúsculas y sin acentos. Se aplica al dibujar los subtítulos, así
que basta con rehacer el paso 6 (`subtitulos.py --refrescar`) y volver a montar. No
hay que transcribir otra vez.

### Motor AssemblyAI (opcional, no activado)

```
python scripts/transcribir.py "<proyecto>" --motor assemblyai
```

Más preciso con audio malo, pero **sube el audio a un servidor externo** y necesita
una clave de pago. Antes de usarlo:

1. Avisa al usuario de que el audio sale de su ordenador. Es su decisión, y debe
   tomarla sabiéndolo.
2. La clave va en `.env.local`, en la línea `ASSEMBLYAI_API_KEY=...`. **Nunca en el
   chat.** Ese archivo está en el `.gitignore`.

Por defecto no se usa nunca: la transcripción local es gratis, offline y suficiente.

## El plan de cortes

```
python scripts/plan_cortes.py "<proyecto>" [opciones]
```

Cuatro señales que se combinan y luego se fusionan los solapes:

**1 · Silencios de verdad.** No basta con el hueco entre dos palabras de la
transcripción: los tiempos de un modelo de voz tienen unos milisegundos de holgura y
cortar por ahí se come el final de la palabra. Así que el hueco solo dice *dónde
mirar*, y el silencio real se mide en el audio con `silencedetect` (por debajo de
-32 dB). Se corta por donde el silencio empieza y acaba de verdad, dejando 0,10 s de
aire antes de la palabra siguiente y 0,12 s después de la anterior.

**2 · Pausas medianas: se acortan, no se quitan.** Un hueco de 0,4 s no es un
silencio muerto, es cómo habla la gente. Quitarlo entero suena atropellado y delata
que el vídeo está editado con una máquina. Los huecos entre 0,30 s y el umbral se
comprimen a 0,16 s. Esto es lo que hace que el resultado suene natural, y es lo
primero que hay que explicar cuando el usuario dice "pero se nota que está cortado".

**3 · Muletillas.** Se quitan siempre estas, cuando van solas: `eh`, `ehm`, `em`,
`emm`, `mm`, `mmm`, `hm`, `hmm`, `ah`, `uh`, `aah`, `ehh`, `mhm`.

Y estas otras **solo si la transcripción no las tiene claras** (probabilidad menor de
0,40): `e`, `a`, `o`, `y`, `pues`, `este`, `esto`, `bueno`. La distinción importa:
"pues" es una palabra real que empieza frases, y quitarla siempre destroza el
discurso. Si el modelo la oye con seguridad, se queda.

**4 · Tomas repetidas.** Si una frase de 2 a 6 palabras aparece y vuelve a aparecer
casi seguida (hasta 2 palabras de por medio y menos de 6 segundos de separación), lo
de en medio es un tropiezo: se quita desde la primera hasta la segunda, **que es la
buena**. Así se graba: te equivocas, vuelves a empezar la frase y sigues.

Se prueba primero la coincidencia más larga: si se repitieron cinco palabras, se
quitan las cinco, no solo las dos primeras.

Esto es lo que más tiempo ahorra al usuario y lo que nadie hace a mano. Menciónalo
cuando aparezca: sorprende.

## Ajustes

| Opción | Por defecto | Qué hace |
|---|---|---|
| `--umbral N` | 0.55 | Hueco (en segundos) a partir del cual se corta. Más bajo = más ritmo |
| `--sin-tomas` | — | No busca tomas repetidas |
| `--sin-muletillas` | — | No quita muletillas |
| `--sin-micropausas` | — | No acorta las pausas medianas; solo quita los silencios largos |

Qué hacer según lo que diga el usuario:

| Dice | Haz |
|---|---|
| "corta más", "va lento", "quedan pausas" | `--umbral 0.40`. Si sigue lento, `0.30` |
| "se come palabras", "corta a mitad de frase" | `--umbral 0.75`. Si sigue, añade `--sin-micropausas` |
| "suena atropellado", "no respira" | `--sin-micropausas`: son las pausas cortas lo que le falta |
| "ha quitado un 'pues' que hacía falta" | `--sin-muletillas` y explica el compromiso |
| "ha cortado algo que quería" | Ábrele `trabajo/plan-cortes.json`: cada trozo lleva su motivo. Se puede editar a mano el segmento concreto y correr `cortar.py --refrescar` |

Después de cambiar el plan hay que rehacer desde el paso 5:
`cortar.py --refrescar` → `subtitulos.py --refrescar` → `componer.py --refrescar` →
`sonido.py --refrescar`. **No hay que transcribir otra vez.**

## Editar el plan a mano

`trabajo/plan-cortes.json` es texto legible. Cada segmento:

```json
{"inicio": 3.69, "fin": 4.80, "accion": "quitar", "motivo": "silencio 1.33s"}
```

Cambiar `"quitar"` por `"mantener"` recupera ese trozo. Es la salida buena cuando el
usuario quiere conservar una pausa concreta (un efecto dramático, una risa) sin tocar
el resto del vídeo.

Los tiempos son **segundos del vídeo original**. La correspondencia entre el original
y el cortado está en la clave `mapa` del mismo archivo, y es la que usan los
subtítulos para saber en qué momento del vídeo final va cada palabra.
