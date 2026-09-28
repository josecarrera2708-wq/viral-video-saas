# Maré · información pública

Esto es lo que encontrarías tú buscando en internet: sus redes, su ficha de
Google, lo que dicen sus clientas por ahí, los anuncios que tiene en marcha y una
competidora. En un análisis real esto lo consigues con el buscador y leyendo las
páginas; aquí va escrito para que la práctica se pueda hacer sin conexión.

Trátalo como lo que es: **fuentes**. Si algo no está aquí, no está — no lo
inventes, márcalo "sin datos".

---

## Instagram · @mare.lino

- 4.180 seguidores. Publica 3 o 4 veces por semana desde 2021.
- Fotos muy buenas: el taller, el lino a contraluz, las manos cosiendo, la ría.
  Se guarda bastante (el último carrusel tiene 210 guardados y 96 "me gusta").
- Bio: *"Lino lavado cosido en Pontevedra · Tiradas pequeñas · Envíos a
  península"* y un enlace: `https://mare.example` (la home).
- **Publicación del 14 de julio**, la de más alcance del mes: la Camisa Ría sobre
  una silla de madera. En el pie de foto: *"Nuestra camisa de lino, 39 €.
  Disponible en la web ✨"*.
- Ninguna publicación lleva enlace directo a la ficha del producto que aparece en
  la foto. Tampoco hay tienda de Instagram (nada de productos etiquetados).
- 9 comentarios sin contestar en las últimas tres publicaciones, tres de ellos
  preguntando por tallas ("¿la M vale para una 40?").
- Historias destacadas: dos, "Taller" y "Prensa". Ninguna de tallas, ni de
  envíos, ni de clientas.

## TikTok · @mare.lino

- 890 seguidores, 12 vídeos, el último de hace 5 meses.
- Un vídeo del corte del lino con 41.000 visualizaciones; los demás no pasan de
  1.200.
- En la biografía no hay enlace a la web.

## Ficha de Google (Maré · Pontevedra)

- Aparece como "Tienda de ropa" con dirección Calle Sarmiento 14 y horario de
  martes a sábado, 16:30-20:30.
- Teléfono 986 00 11 22 y enlace a `https://mare.example`.
- 5 fotos, todas subidas por la dueña en 2022.
- **Valoración 4,6 sobre 5 con 23 reseñas.** Ninguna respondida.

## Lo que dicen por ahí (reseñas externas)

Reseñas en la ficha de Google y en un foro de compra local. Literales:

| Fuente | Fecha | Texto | Respuesta |
|---|---|---|---|
| Google, 5★ | mayo 2026 | "La camisa es una maravilla, el lino es de verdad. Se nota que está cosida a mano." | — |
| Google, 5★ | abril 2026 | "Fui a la tienda física y me atendió Icía. Un trato de diez." | — |
| Google, 2★ | junio 2026 | "El pedido **tardó 12 días** en llegar y en la web dice 24-48 horas. La camisa muy bonita, pero avisad." | — |
| Google, 1★ | junio 2026 | "Pedí un cambio de talla y **no contestan al correo**. Llevo dos semanas esperando." | — |
| Google, 4★ | marzo 2026 | "Precioso todo. Me costó saber qué talla pedir, acabé escribiendo por Instagram." | — |
| Foro local | julio 2026 | "Compré un vestido y llegó bien, pero **tardó más de una semana** y no me llegó ningún aviso de envío." | — |

Ninguna reseña de la tienda tiene respuesta del negocio.

## Anuncios activos (Biblioteca de Anuncios de Meta)

Buscando "Maré" en la Biblioteca de Anuncios de Meta, país España, aparece
**1 anuncio activo**:

- **Formato**: imagen única, Instagram y Facebook.
- **Activo desde**: 2 de julio de 2026.
- **Texto**: *"-20 % en toda la colección de lino. Solo esta semana. Cosido en
  Pontevedra."*
- **Imagen**: la Camisa Ría en color arena.
- **Botón**: "Comprar ahora".
- **Destino**: `https://mare.example` (la home).

No hay ningún otro anuncio activo ni ninguno guardado de meses anteriores.

## Una competidora · Fiadeira (fiadeira.example)

Tienda de lino parecida, también gallega, también pequeña. Sirve de referencia:

- Camisa de lino comparable: **54 €**, IVA incluido y dicho así en la ficha.
- Ficha de producto con 6 fotos, vídeo de 8 segundos de la prenda en movimiento,
  y **tabla de medidas** con contorno de pecho, largo de manga y largo total por
  talla.
- Dice en la propia ficha: *"Lo preparamos en 48 h. Te llega en 3-5 días
  laborables"* y *"30 días para devolverlo, la devolución la pagamos nosotras"*.
- **118 reseñas de producto** con foto, gestionadas con Judge.me.
- Envío gratis a partir de 60 €.
- Se puede comprar sin cuenta.
- Buscador arriba, y filtros por talla, color y precio en la categoría.
- Tienen Bizum y PayPal además de tarjeta.
- Tienen 3 anuncios activos, y los tres llevan a la ficha del producto que sale
  en el anuncio, no a la home.

## Medición de las imágenes

En una tienda real esto lo mides tú pidiendo las cabeceras de cada archivo
(`curl -sIL [url de la imagen]` y lees `content-length`). Como aquí no hay
archivos de imagen de verdad, el resultado de esa medición va escrito:

| Imagen | Página | Formato | Peso | Dimensiones |
|---|---|---|---|---|
| `hero-lino-portada.jpg` | Home | JPG | 3,8 MB | 3000 × 2000 px |
| `camisa-lino-arena.jpg` | Home, categoría, ficha | JPG | 2,9 MB | 2400 × 3200 px |
| `pantalon-lino-crudo.jpg` | Home, categoría | JPG | 3,1 MB | 2400 × 3200 px |
| `vestido-lino-verde.jpg` | Home, categoría | JPG | 2,7 MB | 2400 × 3200 px |
| Las otras 37 de la categoría | Categoría | JPG | entre 2,2 y 3,6 MB cada una | 2400 × 3200 px |

Peso total de la página de categoría: **unos 112 MB** en imágenes.
Ninguna imagen del sitio lleva `loading="lazy"`, ninguna se sirve en WebP y
ninguna tiene versiones más pequeñas para el móvil.
