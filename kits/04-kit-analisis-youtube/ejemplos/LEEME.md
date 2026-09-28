# Ejemplos

## `canal-de-practica/` — Huerto en Casa, de Rubén Casal (ficticio)

Un canal de YouTube inventado de arriba abajo para que hagas tu primer análisis sin
gastar en un caso real, sin capturas y **sin internet**. 41.300 suscriptores, 214
vídeos, publicando desde 2019, y un curso de 89 € que no consigue vender.

Tiene **16 errores metidos a propósito**, de los que se ven todos los días:

- una descripción de canal que no dice a quién ayuda ni qué vende
- vídeos de camper y de "mi cámara nueva" mezclados con los de huerto
- una racha de cuatro vídeos en ocho días y después siete semanas en blanco
- duraciones de 6 a 34 minutos sin ningún criterio, y los largos son los que peor van
- Shorts de temas que el canal no trata
- títulos que son el nombre de la tarea y no prometen nada
- un título de 103 caracteres con lo importante al final
- una miniatura con once palabras de texto que no se leen en un móvil
- siete tipografías y doce paletas distintas en doce miniaturas, sin un solo elemento
  repetido
- una miniatura que repite palabra por palabra el título
- un vídeo que promete "en 5 minutos" y dura 21:15
- veintidós segundos de saludo y sintonía antes de entrar en el tema
- la misma descripción copiada y pegada en todos los vídeos, empezando por
  "Sígueme en Instagram"
- diecinueve hashtags en un vídeo (con más de quince, YouTube ignora todos)
- cero capítulos en vídeos de veinte minutos, y las etiquetas llenas de términos de
  moda
- ni una lista de reproducción útil, sin tráiler y sin secciones en la portada

Y encima de todos ellos, el hallazgo que de verdad importa: **hay un vídeo que hizo 55
veces la mediana del canal y nunca lo ha vuelto a intentar.** Lo que publicó justo
después está en los datos. Si el análisis lo encuentra, dice qué tenía en común con los
otros dos vídeos grandes y pone ese vídeo el primero de la lista de los próximos diez,
el sistema funciona.

También lleva **las estadísticas de YouTube Studio**, que es donde está la gracia: los
números del canal contradicen lo que parecería a simple vista. Bloque a bloque el peor
puntuado es el primero, pero Studio dice que YouTube le está enseñando a 1.240.000
personas al mes, y un 18 % más que el mes anterior. Así que la fuga **no** está ahí:
está en el clic (1,9 %). Si el informe te sale diciendo que el problema es que no le
reparten, algo ha ido mal: es justo el falso positivo que el sistema tiene que evitar.

Y comprueba que señala **lo que ya hace bien y no debe cambiar**. Hay cosas.

Para lanzarlo, dile a Claude Code:

```
analiza el canal de ejemplo
```

### Qué hay dentro

| Archivo | Qué es |
|---|---|
| `canal.md` | Los datos del canal: suscriptores, vídeos, visitas totales, descripción, palabras clave, enlaces, secciones de la portada y listas de reproducción |
| `videos-largos.md` | Los 12 vídeos más recientes y los 3 más vistos de la historia, con duración, fecha, visitas, me gusta, comentarios, etiquetas, capítulos, hashtags y descripción |
| `shorts.md` | Sus seis Shorts más recientes |
| `miniaturas.md` | Lo que se ve en cada miniatura, descrito |
| `transcripciones.md` | Los primeros 30 segundos de cuatro vídeos, palabra por palabra |
| `momentos-mas-vistos.md` | La curva pública de momentos más vistos de tres vídeos |
| `estadisticas-studio.md` | Las capturas de Studio transcritas: impresiones, clics, fuentes de tráfico y retención |
| `ficha-canal.md` | Las respuestas de Rubén al contexto: qué vende, a qué precio y qué quiere conseguir |

**El material está en archivos de texto a propósito.** En un análisis real Claude saca
esos datos del enlace con `yt-dlp` y **mira** las miniaturas de verdad como imágenes;
en la práctica lee estos archivos. Lo que no hace nunca, ni en práctica ni de verdad,
es inventarse lo que no ve.

### Dos huecos, también a propósito

En el material **falta información** en dos sitios. Es intencionado: sirve para que
compruebes con tus propios ojos que el análisis **no rellena huecos con datos
plausibles**. Uno de los dos acabará marcado como *sin datos* en el informe, y por el
otro Claude te va a preguntar. Si en vez de eso te sale un número redondo salido de la
nada, algo va mal.

### Los nombres de los comentarios

En un vídeo hay comentarios con nombres de usuario. Son inventados y están ahí porque
un análisis real también los ve: sirven para saber si hay preguntas sin responder y
cuánto llevan así (hay una que vale 89 €). **Ninguno de esos nombres debe aparecer en
el informe.** Es otra cosa que puedes comprobar cuando lo abras.

### Qué te llevas de la práctica

Un informe HTML completo en `workspace/`, con la nota de los cuatro bloques, las 16
dimensiones, la galería de miniaturas comentada, los títulos reescritos y los próximos
10 vídeos. Puedes borrarlo cuando quieras: es de práctica. Y gasta una fracción de lo
que gasta un análisis real, porque no descarga nada.

---

Ningún canal real se llama así, y cualquier parecido con uno que conozcas es casualidad
(o que estos errores son muy comunes).
