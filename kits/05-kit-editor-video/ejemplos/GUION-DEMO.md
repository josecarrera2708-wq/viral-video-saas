# Graba esto con el móvil (20 segundos)

Un guion pensado para que veas funcionando **todo** lo que hace el kit en un solo
clip. No es para publicarlo: es para que veas el antes y el después con tu propia voz
y tu propia cara.

Si no quieres grabar nada, salta al final: el kit fabrica su propio vídeo de prueba.

## Antes de darle a grabar

| | |
|---|---|
| **Cómo** | El móvil **en horizontal** (tumbado). Sí, en horizontal: así ves cómo lo pasa a vertical, que es la mitad del truco |
| **Dónde** | Cualquier sitio con algo de luz en la cara. No hace falta nada más |
| **Sonido** | Los auriculares del móvil ya son mejor que nada. Si no tienes, habla cerca |
| **Sitúate** | **No en el centro: ponte a un lado del encuadre.** Ahí se ve para qué sirve el paso del recorte |
| **Duración** | Unos 20 segundos con las pausas. No pasa nada si son 30 |

## El guion

Lee esto tal cual, **con las pausas de verdad**. Las pausas son la mitad del guion: son
lo que el kit va a quitar.

> **Hola.**
>
> *(cuenta dos segundos en silencio, mirando a cámara)*
>
> **Eeeh… esto es una prueba del kit de edición.**
>
> *(dos segundos de silencio otra vez)*
>
> **Lo que hace es… lo que hace es quitarme los silencios.**
>
> *(un segundo)*
>
> **Y me pone los subtítulos solo.**
>
> *(dos segundos de silencio, sin cortar la grabación)*
>
> **Si ves esto en vertical y con letras, ya funciona.**

Y ya. Para de grabar.

## Qué está probando cada trozo

| El trozo | Lo que se comprueba |
|---|---|
| Grabar en horizontal | El paso del recorte: de 1920x1080 a 1080x1920 |
| Ponerte a un lado | Que el kit te pregunta **dónde estás** antes de recortar, en vez de adivinar |
| Los silencios de dos segundos | El corte de silencios. Son ~7 s de los 20: se van |
| El "Eeeh…" | La detección de muletillas |
| **"Lo que hace es… lo que hace es"** | La detección de tomas repetidas: se queda con la segunda. Esto es lo que más sorprende |
| Hablar seguido | Los subtítulos karaoke, palabra por palabra |

## Después de grabar

1. Pasa el vídeo al ordenador y déjalo en la carpeta **`entrada/`** del kit.
2. En Claude Code, escribe:

```
edita este vídeo
```

3. Te va a preguntar **una sola cosa**: en qué parte del encuadre estás. Te enseñará
   tres fotogramas con una regla encima para que lo veas.

De unos 20 segundos vas a salir con unos 12, en vertical y con subtítulos.

## Lo que vas a ver en el resultado

- **Vertical de 1080x1920**, el formato de TikTok, Reels y Shorts.
- **Sin las pausas** — pero fíjate en que las pausas cortas siguen ahí: se acortan, no
  se quitan. Si se quitaran todas, sonaría atropellado.
- **Sin el "eeeh"**.
- **La frase repetida, una sola vez.** Busca el momento: dijiste dos veces "lo que hace
  es" y en el vídeo final solo hay una.
- **Subtítulos que se encienden** palabra a palabra mientras hablas.

## Si no quieres grabar nada

El asistente de instalación (`/setup`) fabrica su propio vídeo de prueba, con la voz
del ordenador, y lo edita de punta a punta. Termina abriéndotelo para que lo veas.
Tarda unos 15 segundos y comprueba exactamente lo mismo — salvo que la voz no es tuya
y la cara no sale.

Es más rápido, pero con tu clip se entiende mejor lo que estás mirando.

## Un aviso, ya que estás

Cuando grabes de verdad, **no edites nada a mano antes de pasárselo al kit**. Déjalo
todo: las pausas para pensar, los "eeeh", y la frase que has repetido cuatro veces
hasta que salió. Cortar tú antes solo le quita información al kit y te quita tiempo a
ti.
