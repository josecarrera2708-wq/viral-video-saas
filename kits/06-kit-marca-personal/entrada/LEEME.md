# Aquí van tus capturas

Esta carpeta es la bandeja de entrada del kit. Arrastra aquí las capturas de
pantalla del perfil que vas a analizar y dile a Claude Code que ya están.

## Por qué capturas y no el enlace

Instagram y TikTok **no dejan que un programa lea sus páginas**: devuelven una
pantalla de verificación o mandan el contenido como imágenes. No es un fallo del
kit y no se arregla insistiendo. LinkedIn y las webs propias sí se leen desde el
enlace, y esas las lee Claude solo.

Pero hay algo mejor: la pantalla de **Estadísticas** de la propia aplicación. Ahí
está el alcance real, las visitas al perfil y los clics en el enlace. Eso **solo lo
ve el dueño de la cuenta** — ningún programa que rastree internet puede conseguirlo.
Con una captura de esa pantalla, el análisis ve más de lo que vería cualquier
herramienta automática.

## Las cinco capturas (un minuto de móvil)

| # | Qué capturar | Nombre sugerido |
|---|---|---|
| 1 | **El perfil completo**: foto, nombre, bio, enlace, botones, seguidores y destacados. Sin recortar | `1-perfil.png` |
| 2 | **La parrilla**: los últimos 9-12 posts en cuadrícula, tal como los ve alguien que llega | `2-parrilla.png` |
| 3 | **Un post abierto** con su texto y sus comentarios (elige uno normal, no el mejor) | `3-post.png` |
| 4 | **Estadísticas → Últimos 30 días**: alcance, visitas al perfil, clics en el enlace, seguidores nuevos | `4-estadisticas.png` |
| 5 | **Tu mejor post**, el que más funcionó, con sus números a la vista | `5-mejor-post.png` |

Las **1 y 2 son imprescindibles**. La **4 es la que más vale**: es la que permite
decir si la gente no te encuentra, no te entiende o no te contrata. Las demás
afinan el análisis.

Los nombres son una sugerencia para tu orden; Claude las reconoce igual. Si falta
alguna, el informe marca esa parte como *sin datos* — nunca se la inventa.

### Dónde está la pantalla de Estadísticas

- **Instagram**: tu perfil → *Panel profesional* (o el icono de gráfico) →
  *Estadísticas* → arriba, cambia el periodo a **Últimos 30 días**. Baja hasta ver
  *Visitas al perfil* y *Clics en el enlace*.
  - Si no te aparece: tu cuenta es personal. Se cambia gratis en
    *Configuración → Tipo de cuenta → Cambiar a cuenta profesional*. Es
    reversible y no cambia nada de lo que ya has publicado.
- **TikTok**: tu perfil → menú (☰) → *Herramientas para creadores* →
  *Estadísticas* → pestaña *Información general*, periodo de 28 o 30 días.
- **LinkedIn**: no hace falta captura del perfil (Claude lo lee del enlace). Si
  quieres, añade una del panel de *Impresiones de publicaciones* de los últimos 30
  días.
- **YouTube**: *YouTube Studio → Estadísticas → Últimos 28 días*.

## Formatos

Sirven `.png`, `.jpg`, `.jpeg` y `.webp`. Las capturas del móvil ya salen así.

Si alguna es `.heic` (fotos de iPhone), dile a Claude que la convierta: lo hace él,
tú no tienes que abrir nada.

**Hazlas a pantalla completa, sin recortar y sin zoom.** Si el texto sale pequeño o
borroso, no se puede leer y habrá que repetirla.

## Privacidad — lo que este kit no hace

- **Nunca** hacen falta capturas de mensajes privados. No las pidas ni las pongas
  aquí.
- En la captura de comentarios salen **nombres de otras personas**. Se usan para
  ver si hay preguntas sin responder y cuánto tiempo llevan así. **Ningún nombre de
  quien comenta aparece en el informe.**
- Si en una captura hay teléfonos, correos o direcciones, Claude te avisa y no los
  mete en el informe.
- Las capturas **no se incrustan** en el informe: si se lo enseñas a alguien, no va
  nada tuyo dentro que no quieras.
- Todo se queda en tu ordenador. Esta carpeta está excluida de git: no se sube ni
  se comparte con el kit.
- El kit **nunca entra en tu cuenta** ni te pide una contraseña. Si algún día algo
  te pide la contraseña de tu red social, no es este kit.

## Ya las tengo, ¿ahora qué?

Dile a Claude Code:

```
ya están las capturas en entrada/
```

Y si aún no habías lanzado el análisis:

```
analiza esta marca personal: [enlace del perfil]
```

Cuando termines un análisis puedes borrar las capturas: el informe ya guarda todo
lo que hacía falta en `workspace/`.
