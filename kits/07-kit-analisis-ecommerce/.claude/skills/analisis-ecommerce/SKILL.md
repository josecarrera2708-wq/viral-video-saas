---
name: analisis-ecommerce
description: "Analiza una tienda online completa: plataforma, ficha de producto, carrito y checkout, envíos y devoluciones, catálogo y buscador, ticket medio, móvil y velocidad, captación y carrito abandonado, anuncios activos, redes como canal de venta, medición, recompra y reseñas. Puntúa cada dimensión con evidencia, detecta las fugas del embudo de compra, calcula el impacto en euros solo con los números reales del dueño, y genera un informe HTML más la ficha del producto estrella reescrita lista para pegar. Usa esta skill cuando el usuario quiera analizar una tienda online, auditar un ecommerce, saber por qué su tienda tiene visitas pero no ventas, mejorar su conversión, arreglar sus fichas de producto o revisar su checkout. Triggers: 'analiza esta tienda', 'analiza mi tienda', 'auditoría de ecommerce', 'por qué no vendo', 'tengo visitas pero no ventas', 'revisa mi checkout', 'mejora mis fichas de producto', 'análisis de conversión', 'mi tienda online', 'analiza la tienda de ejemplo'."
---

# Análisis de Ecommerce

Le das la URL de una tienda online y la recorres como la recorrería un comprador
—home, categoría, ficha de producto, carrito, checkout hasta el último paso antes
de pagar—, miras de dónde le viene el tráfico y qué pasa después de la primera
compra. La salida son tres archivos: el informe HTML con nota y plan, la ficha del
producto estrella reescrita lista para pegar, y el cuaderno de hallazgos.

**Regla fundamental: análisis honesto y basado en datos reales.** No suavices los
problemas ni exageres los aciertos. El valor de un análisis está en la verdad.

**Segunda regla: cero invención.** Cada afirmación se apoya en algo que has leído
de verdad. Si no lo has podido leer, se marca "sin datos" y no puntúa. Un solo
dato inventado destruye la credibilidad del informe entero (y la venta).

**Tercera regla, propia de este kit: NUNCA completes una compra.** Recorres hasta
el último paso antes de pagar y paras. Cero datos de tarjeta, cero pedidos
completados, cero cuentas creadas en tiendas ajenas. Si para ver el checkout hace
falta registrarse, esa parte queda "sin datos" y se dice en el informe.

---

## Paso 0 — ¿Análisis real o de práctica?

Si el usuario dice "analiza la tienda de ejemplo", "la de práctica" o similar,
entra en **modo práctica**:

- La tienda es **Maré**, una tienda de ropa de lino ficticia de Pontevedra.
- No uses internet. Todo está en `ejemplos/tienda-de-practica/`:
  - `web/index.html` — su home
  - `web/coleccion-lino.html` — su categoría principal
  - `web/producto-camisa-lino.html` — la ficha de su producto estrella
  - `web/carrito.html` — el carrito y el primer paso del checkout
  - `web/envios-y-devoluciones.html` — sus políticas
  - `datos-publicos.md` — su Instagram, TikTok, ficha de Google, reseñas
    externas, sus anuncios activos en Meta, un competidor y **la tabla con el
    peso medido de sus imágenes**
  - `ficha-tienda.md` — las respuestas de la dueña a los dos bloques del Paso 1,
    **con sus números reales incluidos** (para que se vea funcionar el cálculo
    de euros del Paso 5)
- **El peso de las imágenes no se mide con `curl` en modo práctica** (no hay
  internet y las URLs son ficticias): está ya medido en la tabla de
  `datos-publicos.md`. Úsala tal cual para la dimensión 6. Si buscas los pesos
  con `curl` y no los encuentras, no dejes la dimensión en "sin datos": están en
  ese archivo.
- Sáltate el Paso 1 (las respuestas ya están en `ficha-tienda.md`) y haz el resto
  **exactamente igual** que en un análisis real: detectar plataforma, recorrer,
  puntuar, calcular, generar el HTML y la ficha reescrita, y presentarlo.
- Dilo al empezar en una línea: es una tienda ficticia con errores metidos a
  propósito, y sirve para ver el sistema entero de principio a fin.
- El nombre para los archivos es `mare-example`.
- Al presentar, recuérdale que puede borrar los archivos de `workspace/` cuando
  quiera: son de práctica.

En cualquier otro caso es un análisis real: sigue en el Paso 1.

---

## Paso 1 — Recoger la información

Pregunta al usuario lo necesario. Agrupa en **2 mensajes** (no de una en una).

### Bloque 1 — La tienda

- **URL de la tienda**.
- **¿Qué vende exactamente?** — categoría de producto, y si es producto físico,
  digital, suscripción o servicio.
- **¿Cuál es su producto estrella?** — el que más vende o el que más le interesa
  vender. Es el que se reescribirá en el Paso 7. Si no lo sabe, se coge el más
  destacado de la home y se dice.
- **¿Quién es su cliente?** — a quién le vende, y si vende a consumidor final o a
  otras empresas (cambia lo del IVA y la fiscalidad de los precios).
- **¿A qué países envía?**
- **Redes sociales** — las que tenga (con @ o URLs).
- **¿Hace publicidad?** — si sabe que sí, en qué plataformas.
- **¿Tiene competidores directos que conozca?** — 1-2 URLs para comparar.
- **¿Hay algo que crea que no funciona?** — a veces ya sabe dónde le duele.

### Bloque 2 — Sus números (opcional, pero cambia el informe)

Presenta este bloque tal cual, dejando claro que es **opcional** y que se saca
del panel en dos minutos:

> Con estos cuatro números, cada oportunidad del informe sale con los euros al
> lado y la cuenta a la vista. Sin ellos, el análisis se hace igual y se prioriza
> por impacto y esfuerzo — pero no aparecerá ninguna cifra en euros.
>
> - **Visitas al mes** — *Shopify → Analytics · WooCommerce → Estadísticas ·
>   Google Analytics 4 → Informes*
> - **Tasa de conversión** — el % de visitas que acaban en pedido (en Shopify sale
>   directa; en WooCommerce, pedidos ÷ visitas)
> - **Ticket medio** — lo que se gasta de media en un pedido (facturación ÷
>   pedidos)
> - **Pedidos al mes**
>
> Y si los tiene a mano, dos más que afinan mucho: **margen bruto** (%) y **lo que
> le cuesta a él cada envío**.

Reglas de este bloque:

- Si el usuario da los números, **guárdalos literalmente** en el cuaderno de
  hallazgos y úsalos en el Paso 5. Si alguno es una estimación suya, márcalo como
  tal en el informe.
- Si no los da, o no los tiene, dilo y sigue sin problema. **No los estimes.**
  Ni por el tamaño de la tienda, ni por "la media del sector", ni por los precios
  del catálogo.
- Si los números que da son incoherentes (pedidos que no cuadran con visitas ×
  conversión), no lo corrijas por tu cuenta: dile lo que has visto y pregúntale
  cuál de los dos es el bueno.

Pregunta también, si no lo sabes ya por `.claude/setup-completado.json`, si es
**su tienda** o la de **un cliente**: cambia el tono del informe.

> Guarda todas las respuestas. En el Paso 4, comparar lo que dice el dueño con lo
> que enseña la tienda es la fuente de los hallazgos más valiosos.

---

## Paso 2 — Detectar la plataforma y las herramientas

Esto va primero porque cambia **todas** las recomendaciones: dónde se pega cada
cosa, qué se puede tocar y qué limita el tema.

Lee el HTML de la home y de una ficha de producto y busca:

| Señal en el código | Plataforma |
|---|---|
| `cdn.shopify.com`, `Shopify.theme`, `/cart/add`, `myshopify.com` | Shopify |
| `wp-content/plugins/woocommerce`, `woocommerce-page`, `wc-ajax` | WooCommerce |
| `/modules/`, `prestashop`, `id_product` | PrestaShop |
| `Mage.Cookies`, `/static/version`, `catalog/product/view` | Magento / Adobe Commerce |
| `wixstores`, `static.parastorage.com` | Wix Stores |
| `squarespace.com/universal`, `sqs-` | Squarespace |
| `bigcommerce.com` | BigCommerce |
| `etsystatic.com`, o la tienda vive dentro de Amazon/Etsy | Marketplace (no es tienda propia) |

También el `<meta name="generator">` cuando existe.

Y busca en el código qué herramientas tiene conectadas, porque su ausencia es
media auditoría:

- **Analítica y píxeles** — Google Analytics 4 (`gtag`, `G-`), Google Tag Manager
  (`GTM-`), píxel de Meta (`fbq`, `connect.facebook.net`), TikTok, Pinterest,
  Google Ads.
- **Email marketing** — Klaviyo, Mailchimp, Omnisend, Brevo, MailerLite,
  ActiveCampaign, Connectif.
- **Reseñas** — Judge.me, Loox, Yotpo, Stamped, Trustpilot, Opiniones Verificadas.
- **Chat y atención** — Tidio, Crisp, Intercom, WhatsApp Business, Zendesk.
- **Buscador interno** — Algolia, Doofinder, Searchanise, o el buscador nativo.
- **Pasarelas de pago** — Stripe, PayPal, Redsys, Bizum, Klarna, SeQura, Aplazame.
- **Apps de conversión** — recuperación de carrito, upsell, packs, temporizadores.

Si la plataforma no se puede identificar, ponlo como "no identificada" y da las
recomendaciones en genérico. **No la adivines.**

Cierra este paso escribiendo en el cuaderno la ficha técnica de la tienda:
plataforma, herramientas encontradas y — más importante — **las que no están**.

---

## Paso 3 — Recorrer la tienda como un comprador

Usa `WebFetch`, `WebSearch`, `curl` para las cabeceras y el navegador si está
disponible. Recorre en el orden en el que compra una persona, no en el orden en el
que está construida la web.

**Abre el cuaderno de hallazgos antes de empezar.** Crea
`workspace/[tienda]-hallazgos.md` y ve escribiendo cada dimensión en cuanto la
cierres: la evidencia literal encontrada, la nota y por qué. Dos razones: si la
sesión se corta no se pierde el trabajo (con "continúa el análisis" se retoma por
la primera dimensión que falte), y al generar el HTML no tendrás que recordar de
dónde salía cada cosa.

Narra al usuario cada fase en una línea mientras avanzas ("Detectando la
plataforma…", "Recorriendo el checkout…", "Midiendo el peso de las fotos…"). Un
análisis es largo: que no se quede mirando una pantalla quieta.

### Cuando una fuente se bloquea

Las tiendas con protección anti-bots, los carritos que se montan con JavaScript y
las redes sociales tras login son lo normal. Cuando pase, en este orden:

1. Vía alternativa: navegador automatizado, `WebSearch`, el HTML crudo, el
   sitemap, la versión móvil, el feed de producto.
2. Pídeselo al usuario: que recorra él el checkout y te diga cuántos pasos y
   cuántos campos hay, o que pegue la bio, o una captura.
3. Si tampoco: esa dimensión queda **"sin datos"**, se explica por qué en el
   informe, no puntúa y su peso se reparte entre las demás.

Nunca la rellenes con una estimación.

---

### 3A · Ficha de producto — peso 14

**La página que vende.** Es la dimensión con más peso porque es donde se decide la
compra. Analiza la del producto estrella y **2-3 más** para ver si el problema es
de una ficha o del sistema entero.

- **Fotos** — cuántas hay. Una sola foto es un problema grave. ¿Hay detalle,
  escala (el producto usado o en contexto), zoom, vídeo? En ropa o decoración, la
  foto de contexto es la que vende.
- **Título** — ¿dice qué es, de qué está hecho y para quién, o es solo un nombre
  de fantasía? "Camisa Ría" no dice nada; "Camisa de lino lavado — corte holgado,
  unisex" sí.
- **Descripción** — ¿resuelve dudas o es literatura? Busca lo concreto:
  materiales o composición, medidas, cuidados, qué incluye, de dónde viene.
- **Variantes** — tallas y colores: ¿se ven, se entienden, hay **guía de tallas o
  tabla de medidas**? La falta de tabla de medidas en ropa es de las fugas más
  caras que existen (no compran, o compran y devuelven).
- **Stock y urgencia real** — ¿dice si hay stock? ¿La urgencia es real o es un
  contador falso? Un temporizador que se reinicia al recargar destruye confianza.
- **Plazo de entrega en la ficha** — ¿está ahí o hay que buscarlo? "Te llega el
  jueves" convierte; "consultar condiciones de envío" no.
- **Devolución en la ficha** — el plazo y quién paga el porte de vuelta, ahí
  mismo, antes de añadir al carrito.
- **Reseñas del producto** — ¿hay? ¿cuántas? ¿con foto? Cero reseñas en toda la
  tienda es una dimensión entera perdida (ver 3M).
- **Precio y comparativa** — ¿se entiende? ¿Hay precio tachado real o inflado?
- **Botón de añadir al carrito** — visible sin bajar en móvil, texto claro, y qué
  pasa después de pulsarlo (¿avisa? ¿lleva al carrito? ¿ofrece seguir comprando?).
- **Venta cruzada** — ¿hay productos relacionados o "combina con"? ¿Tienen sentido
  o son aleatorios?
- **Preguntas sin responder** — apunta cada duda que te queda al leer la ficha:
  esas son las objeciones que se convertirán en el bloque de FAQ del Paso 7.

Guarda **frases literales** de la ficha: las necesitarás para el antes/después.

### 3B · Carrito y checkout — peso 14

**Donde se pierde el dinero ya ganado.** Recuerda: llegas al último paso antes de
pagar y paras.

- **Añadir al carrito** — ¿se puede seguir comprando o te expulsa? ¿Hay carrito
  lateral que deja seguir?
- **Costes que aparecen ahora** — el momento más caro de la tienda. ¿Aparece un
  gasto de envío que no estaba anunciado? ¿Sube el IVA que no estaba incluido?
  Toda sorpresa de precio en el carrito es una fuga crítica: es la causa número
  uno de abandono.
- **Envío gratis** — si hay umbral, ¿se dice **antes** del carrito? ¿Hay barra de
  "te faltan X € para el envío gratis"? Eso es a la vez confianza y ticket medio.
- **Editar el carrito** — cambiar cantidad o quitar algo sin recargar y sin perder
  el carrito.
- **Cupones** — ¿hay una casilla de descuento enorme y vacía? Provoca que la gente
  se vaya a buscar un cupón y no vuelva.
- **Pasos hasta pagar** — cuéntalos: 1 página, 3 pasos, 5 pantallas. Cada paso
  extra cuesta pedidos.
- **Campos del formulario** — cuéntalos también, y mira cuáles son obligatorios.
  Un NIF obligatorio en una tienda para consumidor final, un teléfono obligatorio,
  un "empresa" obligatorio: cada uno es gente que se va.
- **Compra como invitado** — ¿se puede comprar sin crear cuenta? Si obliga a
  registrarse, es una de las fugas más grandes y más fáciles de arreglar.
- **Métodos de pago visibles** — tarjeta, PayPal, Bizum, transferencia,
  contrareembolso, pago aplazado. Faltar el que usa su público es perder ese
  público.
- **Confianza en el paso de pago** — candado, condiciones enlazadas, teléfono de
  contacto visible, sin errores de idioma.
- **Móvil** — repite el recorrido en móvil si puedes: es donde compra la mayoría y
  donde se rompen los formularios.

Si el checkout exige cuenta o no se puede leer: aplica el protocolo de fuente
bloqueada. Pídele al usuario que lo recorra él (es su tienda o la de su cliente) y
que te diga pasos, campos y métodos de pago. Si tampoco, **"sin datos"**.

### 3C · Confianza y transparencia — peso 10

Lo que hace que un desconocido se atreva a dejar su tarjeta:

- **Envíos** — plazo, precio, países, transportista, qué pasa si no está en casa.
  ¿Está claro y en un solo sitio?
- **Devoluciones** — plazo, quién paga el porte, cómo se inicia, cuánto tarda el
  reembolso. **Busca contradicciones entre el pie, la página de envíos y el FAQ**:
  son frecuentísimas y matan la confianza.
- **Páginas legales** — aviso legal, condiciones de compra, privacidad, cookies.
  En una tienda española: identidad del vendedor, NIF, dirección y el derecho de
  desistimiento de 14 días. Si algo no está, dilo como hallazgo (sin dar
  asesoramiento legal: se recomienda revisarlo con quien corresponda).
- **Aviso de cookies** — ¿existe? ¿Se pueden rechazar? ¿Carga los píxeles antes de
  aceptar?
- **Contacto real** — teléfono, email, dirección, formulario. Una tienda sin
  ninguna forma de hablar con un humano vende menos.
- **Sobre nosotros** — ¿hay cara, historia, taller, ubicación? En marcas pequeñas
  es una de las páginas más visitadas antes de comprar.
- **Sellos y pasarelas** — logos de pago reconocibles, sellos de confianza reales
  (no imágenes decorativas).
- **Coherencia de datos de contacto** — teléfono y email iguales en la web, la
  ficha de Google y las redes.

### 3D · Catálogo y navegación — peso 8

- **Menú** — ¿se entiende qué categorías hay? ¿Hay 14 entradas o 5 claras?
- **Cuántos clics** de la home al producto. Más de 3 es un problema.
- **Filtros** — talla, color, precio, material, disponibilidad. Una categoría con
  40 productos y sin filtros es una categoría que no se compra.
- **Orden** — ¿se puede ordenar por precio o por novedad?
- **Paginación** — ¿todo en una página infinita, o páginas manejables?
- **Buscador interno** — ¿existe? Es la herramienta de la gente con intención de
  compra: quien busca convierte mucho más. Si existe, pruébalo con el nombre de
  un producto real, con una falta de ortografía y con una categoría. Si no
  existe, es un quick win claro.
- **Fichas de categoría** — ¿tienen texto y sentido, o son una parrilla de fotos?
- **Productos agotados** — ¿siguen ahí sin avisar? ¿Hay avisar-cuando-vuelva?

### 3E · Precio y ticket medio — peso 8

La dimensión que más dinero mueve con menos esfuerzo.

- **IVA** — ¿los precios lo incluyen y se dice? En tienda para consumidor final,
  precios sin IVA que suben al final es una fuga grave.
- **Umbral de envío gratis** — ¿existe? ¿Está por encima del ticket medio (bien) o
  por debajo (regalando margen)? Si el usuario dio su ticket medio, aquí hay una
  palanca con cuenta exacta.
- **Packs y lotes** — ¿hay forma de comprar 2 o 3 con ventaja?
- **Venta cruzada y complementos** — en la ficha, en el carrito, en el checkout.
- **Cantidad** — ¿se puede subir la cantidad fácilmente?
- **Gama** — ¿hay un producto caro que haga parecer razonable al de gama media?
- **Suscripción o recurrencia** — si el producto se consume, ¿se puede suscribir?
- **Descuentos permanentes** — un "-20 % siempre" no es una oferta, es un precio
  con letra grande. Si toda la tienda está de rebajas todo el año, dilo.

### 3F · Móvil y velocidad — peso 8

**Mide, no estimes.**

- **Peso de las imágenes** — coge las 3-5 imágenes principales (la del hero y las
  del producto estrella) y mide cada una con
  `curl -sIL "[url de la imagen]"` leyendo `content-length`. Conviértelo a KB o MB
  y ponlo en el informe con el número exacto. Referencia: una foto de producto
  bien preparada pesa entre 80 y 250 KB. Por encima de 1 MB es un problema; por
  encima de 3 MB es un problema grave en móvil con datos.
- **Formato** — ¿JPG/PNG o WebP/AVIF? ¿Tienen `srcset` para servir tamaños
  distintos según pantalla?
- **Carga diferida** — ¿hay `loading="lazy"` en las imágenes que no se ven al
  entrar?
- **Cantidad de peticiones y scripts** — cuenta los scripts externos de la home.
  Muchas apps instaladas = tienda lenta.
- **Primera impresión en móvil** — ¿se entiende qué vende sin bajar? ¿El botón
  principal se ve? ¿Hay pop-up que tapa todo al entrar?
- **Zonas pulsables** — botones y enlaces suficientemente grandes y separados.
- **Fuentes y CSS bloqueantes**, si se puede ver.
- Si el usuario tiene una medición real (PageSpeed, su panel), pídesela. Si no
  la hay, **no inventes una puntuación de velocidad**: informa de lo que has
  medido de verdad (pesos, formatos, número de scripts).

### 3G · SEO de tienda — peso 4

Solo lo que afecta a vender, sin entrar en SEO avanzado:

- **Título y meta descripción** de la home, de una categoría y de la ficha
  estrella: ¿existen, son distintos, incluyen el producto?
- **Datos estructurados** — busca en el HTML un bloque `application/ld+json` con
  `Product` y `Offer` (y `AggregateRating` si tiene reseñas). Sin ellos, el
  producto no puede salir con precio, disponibilidad y estrellas en Google. Es de
  los arreglos con mejor relación esfuerzo/resultado y se entrega hecho en el
  Paso 7.
- **Encabezados** — un `h1` por página, y que diga algo.
- **URLs** — legibles o llenas de parámetros.
- **`sitemap.xml` y `robots.txt`** — pruébalos. ¿Están? ¿El sitemap incluye los
  productos?
- **Texto alternativo de las imágenes** — vacío en toda la tienda es habitual y es
  a la vez SEO y accesibilidad.
- **Contenido indexable** — ¿la categoría tiene texto propio o solo fotos?
- **Blog o guías** — si existe, ¿está vivo y lleva a producto?

### 3H · Captación y recuperación — peso 8

Lo que hace con el 97 % que no compra hoy.

- **Captura de email** — ¿hay? ¿Qué ofrece a cambio? Un "suscríbete a nuestra
  newsletter" no es una oferta; un 10 % de bienvenida o una guía sí.
- **Cuándo aparece el pop-up** — a los 2 segundos de entrar es demasiado pronto.
  ¿Se puede cerrar? ¿Vuelve a salir en cada página?
- **Y sobre todo: ¿manda algo después?** Cruza esto con el Paso 2: si no hay
  ninguna herramienta de email en el código, **está recogiendo emails que no usa**.
  Es un hallazgo de los que se entienden solos.
- **Recuperación de carrito abandonado** — la palanca de recuperación más rentable
  que existe. ¿Hay señales de que exista (app instalada, herramienta de email
  conectada)? Si el usuario tiene la tienda, pregúntale directamente: es un dato
  que él sabe.
- **Secuencia de bienvenida** — ¿el que se suscribe recibe algo o cae en el vacío
  hasta la próxima campaña?
- **Notificaciones de vuelta de stock** — para productos agotados.
- **WhatsApp o chat** — ¿hay una vía rápida para la duda que impide comprar?

### 3I · Anuncios (Meta Ads) — peso 6

La Biblioteca de Anuncios de Meta es **pública**: enseña todos los anuncios
activos de cualquier anunciante.

**Cómo buscar** (prueba varias vías antes de concluir que no tiene):

1. `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=ES&q=[nombre de la tienda]`
   (cambia `country` al país que corresponda; `ALL` si no lo sabes)
2. Variantes del nombre: la marca, la marca con la ciudad, el dominio.
3. `WebSearch`: `"[nombre tienda]" facebook ads library`
4. Si encuentras su página de Facebook: *Transparencia de la página → Anuncios*.

Si la biblioteca no carga con `WebFetch` (es muy dinámica), usa el navegador si
está disponible; si no, protocolo de fuente bloqueada.

**Si tiene anuncios activos, saca de cada uno:** fecha de primera publicación,
plataformas, formato, **copy literal** (el gancho, la oferta, el CTA), creatividad
(¿producto real o banco de imágenes?), **destino** y número de variantes.

**Y la lectura, que es lo que importa en una tienda:**

- **¿A dónde aterriza?** — un anuncio de un producto que lleva a la **home** es
  dinero tirado: el que hace clic tiene que volver a buscar lo que le prometieron.
  Comprueba el destino uno a uno.
- **Coherencia anuncio ↔ ficha ↔ precio** — el error más caro y el más común: el
  anuncio promete un descuento, un precio o un plazo que la ficha no confirma.
  Compáralo literalmente y cita las dos frases.
- **¿Hay píxel?** (3K) — si paga tráfico sin medición, no puede optimizar ni
  volver a alcanzar a quien ya visitó. Es la combinación más caótica que existe.
- **Antigüedad como señal** — un anuncio con meses activo suele estar
  funcionando; nadie mantiene lo que no le devuelve dinero. Dilo como **señal**,
  nunca como prueba.
- **Anuncios de la competencia** — búscalos en la misma biblioteca: qué mensaje
  usan, desde cuándo, a dónde llevan. Inteligencia competitiva gratis y una de
  las partes que más impresiona del informe.

**Lo que la biblioteca NO dice** (y por tanto no puedes afirmar): cuánto gasta,
cuántos clics tiene, si convierte, su retorno. No lo inventes ni lo estimes.

**Si no tiene anuncios activos**: no es automáticamente un error. Decide si
debería tenerlos según la tienda y su objetivo — pero antes de recomendar
publicidad, mira si la tienda convierte: mandar tráfico pagado a un checkout roto
es quemar dinero, y decirlo así es lo que separa un informe honesto de una venta
de humo.

### 3J · Redes como canal de venta — peso 5

No juzgues las redes como un experto en contenido: júzgalas como puerta de la
tienda.

- **Link en bio** — ¿lleva a la home genérica o al producto del que habla el
  último post? ¿Está roto? ¿Es un enlace intermedio con 12 opciones?
- **¿El contenido lleva a producto?** — se puede publicar mucho y no vender nada.
  Mira si los pies de foto tienen alguna llamada a la acción.
- **Precios en redes vs. web** — cruza precios de posts con los de la web. Los
  precios antiguos en Instagram son un clásico y provocan discusiones con
  clientes.
- **Tienda etiquetada** (Instagram Shopping, TikTok Shop) — ¿tiene el catálogo
  conectado y los productos etiquetados en los posts?
- **Bio** — ¿dice qué vende, a quién y desde dónde envía?
- **Frecuencia y abandono** — una red parada 8 meses hace pensar que la tienda
  cerró. Es peor que no tenerla.
- **Coherencia visual** — que la tienda y las redes parezcan la misma marca.
- **Contenido de cliente** — fotos de clientes reales usando el producto, y si se
  reutilizan en las fichas (es la mejor foto y es gratis).

### 3K · Medición — peso 3

- **Analítica** — ¿hay GA4 u otra? ¿Está puesta o solo pegada?
- **Píxeles publicitarios** — Meta, TikTok, Google Ads: si anuncia, tienen que
  estar.
- **Eventos de ecommerce** — busca señales de eventos de compra
  (`view_item`, `add_to_cart`, `purchase`, o el `fbq('track', 'Purchase')`). Sin
  el evento de compra no sabe qué campaña le trae ventas: mide visitas, no
  dinero.
- **Consentimiento de cookies** — si los píxeles cargan antes de aceptar, es un
  problema a revisar. Dilo como hallazgo, no como asesoramiento legal.
- **Búsquedas internas medidas** — lo que la gente busca y no encuentra es la lista
  de productos que debería tener. Si tiene buscador, ¿lo mide?

### 3L · Retención y recompra — peso 7

Lo más barato que existe es volver a venderle a quien ya compró. Y es lo que casi
nadie hace.

- **Después de comprar** — ¿hay email de confirmación con expectativa clara
  (cuándo sale, cómo se sigue)? Si es la tienda del usuario, pregúntaselo.
- **Petición de reseña** — ¿pide reseña tras la entrega? Cruza esto con 3M: si no
  hay reseñas en toda la tienda, aquí está el motivo.
- **Recurrencia** — ¿el producto se acaba, se repone, cambia de temporada? ¿Hay
  algo que traiga de vuelta al cliente en el momento adecuado?
- **Suscripción** — cuando el producto lo permite.
- **Fidelización** — puntos, descuento a la segunda compra, ventajas de cliente.
- **Clientes dormidos** — ¿hay alguna acción para el que compró hace 8 meses y no
  volvió?
- **Unboxing y postventa física** — nota dentro del paquete, código para la
  siguiente compra, invitación a la comunidad.
- **Atención posventa** — si las reseñas se quejan de que no contestan, esto es una
  fuga con nombre y apellidos.

### 3M · Reputación y reseñas — peso 5

- **Reseñas de producto en la tienda** — cuántas, con foto, verificadas, y si se
  ven en la ficha antes de comprar. Cero reseñas es la señal más común de tienda
  que no pide nada a sus clientes.
- **Reseñas externas** — Google, Trustpilot, Amazon si también vende ahí, redes.
  Busca con `WebSearch`.
- **Patrones** — si tres reseñas dicen lo mismo, es un problema real del negocio,
  no una opinión. Los patrones típicos en ecommerce: plazo de entrega,
  devoluciones, atención que no responde, producto distinto a la foto, talla que
  no corresponde. **Cruza cada patrón con lo que promete la web** y cítalo:
  "promete 24-48 h y tres reseñas dicen 12 días" es un hallazgo demoledor y
  literal.
- **¿Responde?** — a las negativas sobre todo. No responder a una queja pública es
  un error visible para todo el que la lea.
- **Ficha de Google / Maps** — si la tienda tiene también local o taller.
- **Prueba social en la web** — testimonios, número de clientes, prensa, "más de
  X pedidos enviados". ¿Está o se lo guarda?

### 3N · Competencia (contexto, no puntúa)

Si el usuario dio competidores, compáralos en lo que decide una compra:

| Qué comparar | Por qué importa |
|---|---|
| Precio del producto equivalente | Posicionamiento real |
| Envío: precio, umbral de gratis y plazo | Es lo primero que compara un comprador |
| Devoluciones: plazo y quién paga | Elimina o crea el miedo a comprar |
| Reseñas: cuántas y qué nota | Confianza |
| Ficha de producto: fotos, medidas, detalle | Quién resuelve mejor las dudas |
| Checkout: pasos y pagos | Dónde es más fácil comprar |
| Qué anuncia y a dónde lleva | Su estrategia, gratis (3I) |

Cierra con **oportunidades de diferenciación concretas**, no genéricas. No "ser
más innovador", sino "es la única que hace la prenda a medida y no lo dice en
ninguna parte: la competencia no ofrece ese servicio".

---

## Paso 4 — Puntuar cada dimensión (con evidencia)

Trece dimensiones puntúan. La competencia es contexto y no puntúa.

| # | Dimensión | Bloque | Peso |
|---|---|---|---|
| 1 | Ficha de producto | La tienda | 14 |
| 2 | Carrito y checkout | La tienda | 14 |
| 3 | Confianza y transparencia | La tienda | 10 |
| 4 | Catálogo y navegación | La tienda | 8 |
| 5 | Precio y ticket medio | La tienda | 8 |
| 6 | Móvil y velocidad | La tienda | 8 |
| 7 | SEO de tienda | La tienda | 4 |
| 8 | Captación y recuperación | El tráfico | 8 |
| 9 | Anuncios (Meta Ads) | El tráfico | 6 |
| 10 | Redes como canal de venta | El tráfico | 5 |
| 11 | Medición | El tráfico | 3 |
| 12 | Retención y recompra | La retención | 7 |
| 13 | Reputación y reseñas | La retención | 5 |

**Anclajes de la nota** (para que no sea a ojo):

| Nota | Significado |
|---|---|
| 0-20 | No existe, **o existe y resta** (ver abajo) |
| 21-40 | Existe pero está mal o abandonado |
| 41-60 | Cumple lo mínimo, sin nada que le diferencie |
| 61-80 | Bien hecho, con fallos concretos identificados |
| 81-100 | Referencia del sector |

**Cuando lo que hay es peor que no tener nada.** La banda de 0-20 no es solo para
lo que no existe: también para lo que existe y **hace daño activamente**. Un
anuncio que promete un descuento que no está creado, un formulario que recoge
correos que no se guardan en ningún sitio, un plazo de entrega prometido que las
reseñas desmienten: eso no es "existe pero está mal", es peor que la ausencia,
porque gasta dinero o rompe la confianza. En ese caso **baja de 21 sin problema**
y dilo en el informe con esa frase: *"es peor que no tener nada, porque…"*. Lo que
no vale es bajar de 21 por severidad general o por acumular fallos: hace falta
señalar el daño concreto que causa lo que hay.

**Reglas de puntuación:**

- Cada nota va con **al menos dos evidencias** concretas: una frase literal, una
  URL, un precio, un peso en MB, un número de reseñas. Sin evidencia no hay nota.
- **No aplica**: si la dimensión no tiene sentido en esa tienda (envíos en
  productos digitales, anuncios en una tienda que no hace publicidad, checkout en
  un marketplace), no puntúa y su peso se reparte proporcionalmente entre las
  demás. Se dice en el informe.
- **Sin datos**: si aplica pero no se pudo leer, tampoco puntúa; se explica por
  qué y su peso se reparte igual. Nunca pongas una nota "prudente" para rellenar.
- **Nota global** = media ponderada de las dimensiones que sí puntúan.
- Bandas de la global: **0-39 crítico · 40-59 flojo · 60-74 aceptable · 75-89
  bueno · 90-100 referencia**.
- Sé exigente con la nota alta. Un 80 significa "esto ya está bien hecho". La
  mayoría de las tiendas pequeñas están entre 30 y 55, y decirlo claro es el
  servicio que estás vendiendo.

---

## Paso 5 — Las fugas y los euros

### 5.1 · Las fugas del embudo

Cada hallazgo se coloca en el paso del embudo donde ocurre, porque eso es lo que
hace entender el problema:

```
Descubrimiento → Categoría → Ficha → Carrito → Checkout → Pago → Post-compra → Recompra
```

Para cada fuga: **qué pasa · la evidencia literal · en qué paso ocurre · por qué
cuesta dinero · cómo se arregla · prioridad (alta/media/baja)**. Un problema sin
solución al lado es una queja, no un análisis.

Fugas típicas de ecommerce, para que no se te escape ninguna:

- Coste de envío que aparece por primera vez en el carrito
- IVA que sube al final en una tienda para consumidor final
- Registro obligatorio para comprar
- Formulario de pago con campos obligatorios innecesarios
- Falta la tabla de medidas o las especificaciones que deciden la compra
- Plazo de entrega invisible hasta el checkout
- Devolución no explicada, o explicada de tres formas distintas
- Una sola foto por producto, sin contexto ni zoom
- Cero reseñas en toda la tienda
- Categoría grande sin filtros, sin orden y sin buscador
- Fotos de varios MB en móvil
- Emails recogidos con un pop-up que nunca reciben nada
- Sin recuperación de carrito abandonado
- Anuncio que aterriza en la home en lugar de en el producto anunciado
- Precio del anuncio o de Instagram distinto al de la web
- Publicidad pagada sin píxel ni evento de compra
- Reseñas que denuncian plazos que la web promete más cortos, sin responder
- Cero post-venta: nadie vuelve porque nadie se lo recuerda

### 5.2 · Los euros, si hay números

**Si el dueño dio sus números** (Paso 1, bloque 2), calcula el escenario de las
palancas principales. Tres capas siempre separadas y visibles:

1. **Sus números** — reales, citados tal como los dio.
2. **La mejora** — hipótesis, **etiquetada como escenario**, con el razonamiento
   al lado ("quitar el registro obligatorio y el coste sorpresa del carrito son
   las dos causas más habituales de abandono en el checkout").
3. **La cuenta** — escrita entera en el informe.

Formato obligatorio de cada palanca, tal cual:

> **Palanca:** permitir comprar sin registrarse
> **Sus números:** 6.400 visitas/mes · 0,7 % de conversión · 46 € de ticket medio
> **Escenario:** conversión 0,7 % → 1,0 %
> **Cuenta:** 6.400 × (1,0 % − 0,7 %) = **+19 pedidos/mes** × 46 € = **+874 €/mes**
> *Escenario calculado con los datos facilitados por la tienda, no una previsión.*

Palancas que suelen tener cuenta clara:

- **Conversión del checkout** — invitado, menos campos, costes visibles antes.
- **Ticket medio** — subir el umbral de envío gratis hasta un poco por encima del
  ticket medio actual, packs, venta cruzada. Cuenta: `pedidos/mes × subida del
  ticket`.
- **Recuperación de carrito** — necesita el número de carritos abandonados; si no
  lo tiene, **no pongas euros**: deja la palanca en la lista con su prioridad.
- **Recompra** — `clientes/mes × % que repite × ticket medio`. Si no sabe cuántos
  repiten, se queda sin euros.
- **Margen del envío** — si dio lo que le cuesta el envío y el umbral de gratis,
  se puede ver si está regalando margen.

Reglas duras:

- **Sin sus números, ni un euro en el informe.** Se prioriza por impacto y
  esfuerzo, y punto.
- Cada cifra derivada lleva su operación a la vista.
- Si das un **total**, di explícitamente que las palancas se solapan y que el
  total es el techo del escenario, no la suma esperada.
- Nunca uses una cifra del sector como si fuera de esta tienda.
- Si un número lo dio como estimación, márcalo como estimación del dueño.

---

## Paso 6 — Generar el informe HTML

Dashboard visual, autocontenido. Libertad creativa en el diseño; el contenido y
el orden, no.

### Secciones obligatorias, en este orden

1. **Cabecera** — nombre de la tienda, dominio, **plataforma detectada**, fecha y
   quién firma (nombre o agencia de `.claude/setup-completado.json`). Si ese
   archivo no existe todavía, no inventes una firma: en modo práctica pon
   "Análisis de práctica", y en un análisis real pregunta con qué nombre firmarlo.
2. **Titulares** — nota global (0-100) con su banda · número de fugas críticas ·
   impacto mensual del escenario **solo si hay números del dueño**.
3. **Resumen ejecutivo** — 3 párrafos: dónde está la tienda · por qué no vende más
   · qué gana si lo arregla.
4. **Las fugas** — lo primero que mira el cliente. Cada una con qué pasa,
   evidencia literal, paso del embudo, coste, arreglo y prioridad.
5. **Mapa del embudo de compra** — diagrama incrustado (HTML/CSS o SVG inline, sin
   dependencias externas) con los ocho pasos, marcando dónde se cae la gente y qué
   pasos **no existen** en esta tienda.
   **Aviso obligatorio al pie del diagrama:** el ancho de cada tramo **ilustra**
   el estrechamiento del recorrido, no lo mide — salvo que la tienda tenga los
   eventos de ecommerce midiendo de verdad y te haya dado esas cifras. Lo normal
   es que no los tenga (es uno de los hallazgos habituales de la dimensión 11), y
   entonces un embudo con anchos que parecen datos es un dato inventado con forma
   de dibujo. Dilo en una línea: qué falta por medir y qué habría que activar para
   convertir el dibujo en una medición.
6. **Diagnóstico por área** — las 13 dimensiones agrupadas en los tres bloques (La
   tienda · El tráfico · La retención), cada una con su nota, la evidencia literal
   que la justifica, lo que está bien, lo que está mal y las acciones concretas.
   Las que no apliquen o queden sin datos se muestran marcadas como tales, no con
   un cero.
7. **La ficha de producto: antes y después** — el antes/después resumido con sus
   frases reales, y la referencia al archivo completo que se deja al lado.
8. **Palancas de ticket medio y conversión** — cada una con su cuenta a la vista
   (Paso 5.2). Si no hay números, esta sección se convierte en la lista de
   palancas ordenada por impacto y esfuerzo, sin cifras.
9. **Comparativa con la competencia** (si aplica) — tabla lado a lado.
10. **Plan priorizado** — tabla: prioridad · acción · impacto · esfuerzo · área.
11. **Quick wins de esta semana** — 3-5 acciones concretas, con resultado esperado
    y tiempo estimado de ejecución.
12. **Nota metodológica** — qué se leyó y qué no; la fecha; que **no se completó
    ninguna compra ni se accedió a ningún panel privado**; qué quedó "sin datos" y
    por qué; y el aviso de que las cifras en euros son escenarios calculados con
    los datos facilitados por la tienda.

### Requisitos del dashboard

- **Autocontenido**: CSS y JS inline, SVG inline, sin dependencias externas. Un
  solo archivo que se abre en cualquier navegador aunque no haya internet.
- **Responsive**: se lee bien en móvil (el cliente lo va a abrir en el móvil).
- **Imprimible**: al imprimir a PDF no se cortan las secciones ni se pierden los
  colores de las notas (usa `@media print`).
- **Navegación interna** entre secciones.
- **Cero emojis decorativos.** Tono profesional y directo: esto se le enseña a un
  dueño de tienda, no es un post de Instagram.
- Que no parezca un informe de consultoría genérico: cada afirmación con el dato
  de la tienda al lado.

---

## Paso 7 — La ficha de producto reescrita

El segundo entregable, y el que más impresiona porque es trabajo hecho, no
diagnóstico. Se hace sobre el **producto estrella** (el que dijo el dueño; si no
lo dijo, el más destacado de la home, y se dice cuál se ha elegido).

Guarda `workspace/[tienda]-ficha-[producto]-reescrita.md` con, en este orden:

1. **Título** — versión actual y versión nueva, una debajo de la otra. La nueva:
   producto + característica diferencial + para quién.
2. **Cinco bullets de venta** — cada uno un beneficio con su dato concreto, no
   adjetivos. "Lino lavado de 190 g: cae sin arrugarse como el lino rígido" en
   lugar de "máxima calidad".
3. **Descripción larga** — con esta estructura: para quién es · qué problema
   resuelve · materiales o composición · cómo se usa o se cuida · qué incluye.
4. **Tabla de medidas o variantes** — la que falte. Si no tienes los datos reales,
   deja la tabla montada con los huecos marcados `[medir]` y una línea explicando
   cómo medirlo. Un hueco honesto vale; un número inventado, no.
5. **Bloque de envío y devolución para la ficha** — con los plazos **reales de la
   tienda**, citados de su propia web. Si sus plazos se contradicen entre páginas
   (pasa a menudo), escribe el bloque con el plazo que él confirme y avisa de la
   contradicción.
6. **Cinco preguntas frecuentes** — sacadas de objeciones **reales**: las dudas que
   te quedaron al leer su ficha, los patrones de sus reseñas, lo que su
   competencia sí explica.
7. **Datos estructurados (JSON-LD)** — bloque `Product` + `Offer` listo para
   pegar, con los datos reales que tengas y `[completar]` en los que no. El
   `AggregateRating` va **comentado** con una nota: se activa cuando tenga
   reseñas reales. Nunca escribas una valoración que no existe.
8. **Dónde se pega cada cosa** — según la plataforma detectada en el Paso 2:
   - *Shopify*: Productos → el producto → Título, Descripción, Multimedia; el
     JSON-LD en la plantilla del producto o con una app de SEO.
   - *WooCommerce*: Productos → Editar producto → Descripción corta (bullets) y
     Descripción larga; el JSON-LD con el plugin de SEO que tenga.
   - *PrestaShop*: Catálogo → Productos → pestañas Ajustes básicos y Descripción.
   - Si la plataforma es "no identificada": explícalo en genérico ("el título del
     producto", "la descripción corta") sin inventar rutas de menú.

Cierra el archivo con una nota de una línea: los textos están escritos para esta
tienda con sus datos reales, y todo lo marcado `[completar]` o `[medir]` necesita
un dato que solo tiene el dueño.

---

## Paso 8 — Guardar y presentar

Guarda en `workspace/`:

| Archivo | Qué es |
|---|---|
| `analisis-ecommerce-[tienda].html` | El informe completo |
| `[tienda]-ficha-[producto]-reescrita.md` | La ficha lista para pegar |
| `[tienda]-hallazgos.md` | El cuaderno con la evidencia de cada dimensión |

`[tienda]` = dominio sin `www` y con los puntos cambiados por guiones:
`mare.example` → `mare-example`. Si no hay dominio propio, el nombre en
minúsculas, sin tildes, con guiones. `[producto]` igual: minúsculas, sin tildes,
con guiones.

Abre el informe en el navegador.

Presenta al usuario, en este orden y corto:

1. La nota global y su banda.
2. La fuga principal **en una frase**.
3. El impacto del escenario, **solo si hay números**, con su cuenta.
4. Los 3 quick wins más urgentes.
5. Que la ficha reescrita está lista para pegar, y dónde.
6. Los caminos posibles: profundizar en un área ("profundiza en el checkout"),
   reescribir la ficha de otro producto, o pasar a arreglar lo detectado.

---

## Reglas de la skill

- **Nunca completes una compra.** Último paso antes de pagar y paras. Cero datos
  de tarjeta, cero pedidos, cero cuentas creadas. Si el checkout exige cuenta,
  "sin datos".
- **No toques la tienda.** Diagnosticas y escribes textos; no publicas, no cambias
  el tema, no instalas apps.
- **Cero invención.** Ni reseñas, ni plazos, ni pesos de imagen, ni ventas, ni
  conversión, ni precios de la competencia. Todo con evidencia o marcado "sin
  datos".
- **Los pesos de imagen se miden** con `curl -sIL`. Si no se pueden medir, se dice.
- **Sin los números del dueño no hay euros.** Y con ellos, siempre con la cuenta a
  la vista y la etiqueta de escenario.
- **Solo información pública.** No entras en paneles, ni en analítica, ni en
  pedidos. Si el usuario ofrece claves de acceso, recuérdale que este kit no las
  necesita y no las aceptes.
- **Honesto, no cruel.** Cada problema sale con su solución al lado. El informe
  tiene que dejar al dueño con ganas de arreglarlo, no hundido.
- **El informe es para la tienda analizada.** Dentro del HTML no van las tarifas
  del usuario ni consejos de cómo venderle a este cliente. Los precios que sí van
  son los **de la tienda analizada**, cuando el hallazgo es sobre ellos. Lo de
  cuánto cobrar por el análisis se habla en el chat — está en el `CLAUDE.md`.
- **Todo a `workspace/`.** Nunca dejes archivos sueltos en la raíz del kit.
