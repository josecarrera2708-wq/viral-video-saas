# Ejemplos · la tienda de práctica

Aquí dentro hay una tienda online **inventada** para que puedas probar el kit
entero sin gastar un análisis real y sin necesidad de internet.

## Cómo se usa

Abre esta carpeta con Claude Code y escribe:

```
analiza la tienda de ejemplo
```

Ya está. Claude detecta que es el modo práctica, lee los archivos de esta carpeta
en lugar de salir a internet, y hace exactamente lo mismo que haría con una tienda
de verdad: detecta la plataforma, recorre la tienda como un comprador, puntúa las
13 dimensiones con evidencia, calcula los euros y te deja en `workspace/`:

- `analisis-ecommerce-mare-example.html` — el informe
- `mare-example-ficha-camisa-ria-reescrita.md` — la ficha reescrita
- `mare-example-hallazgos.md` — el cuaderno de trabajo

## Qué es Maré

Una tienda de ropa de lino de Pontevedra, montada en WooCommerce, con 40 productos
y una dueña llamada Icía que cose ella misma. Tiene 6.400 visitas al mes y solo 45
pedidos: entra gente y no compra. Ese es el caso.

Es un caso realista a propósito: **no es una tienda desastrosa**. Las fotos son
bonitas, la marca tiene historia, el producto es bueno y la atención en la tienda
física es excelente (4,6 sobre 5 en Google). Lo que está roto es el camino desde
que alguien ve la camisa hasta que la paga. Que es justo lo que le pasa a la
mayoría de las tiendas pequeñas.

Espera una nota global **baja** — está en la banda crítica. Eso es correcto: la
tienda tiene 16 problemas metidos a propósito, y varios de ellos son de los que
hacen que un carrito se abandone entero.

## Qué hay en la carpeta

```
tienda-de-practica/
├── web/
│   ├── index.html                    ← la portada
│   ├── coleccion-lino.html           ← la categoría, con los 40 productos
│   ├── producto-camisa-lino.html     ← la ficha del producto estrella
│   ├── carrito.html                  ← el carrito y el checkout
│   └── envios-y-devoluciones.html    ← envíos, devoluciones y preguntas frecuentes
├── datos-publicos.md                 ← redes, ficha de Google, reseñas, anuncios activos,
│                                       una competidora y el peso real de las imágenes
└── ficha-tienda.md                   ← lo que cuenta Icía, con sus números reales
```

Los archivos `.md` existen porque hay cosas que en una tienda real no están en el
HTML: sus reseñas de Google, sus anuncios de Meta, el peso de sus fotos medido con
una petición de cabeceras, y los números de su panel. En un análisis real todo eso
lo consigues buscando y preguntando; aquí va escrito para que la práctica se cierre
sin conexión.

Puedes abrir los cinco HTML en tu navegador (doble clic) para ver la tienda como
la vería una clienta. Las imágenes no existen como archivos — verás los huecos, y
su peso real está anotado en `datos-publicos.md`.

## Para qué sirve la práctica

1. **Ver el sistema entero** antes de gastarlo en una tienda que te importa.
2. **Comprobar si te fías del informe.** Como los errores están metidos a
   propósito, puedes verificar si Claude los encuentra todos y si lo que dice está
   apoyado en algo real.
3. **Ver cómo se calculan los euros.** Icía tiene sus números, así que el informe
   de práctica sale con las cuentas a la vista — es la parte del kit que más
   cuesta entender leyéndola y que se entiende sola viéndola.
4. **Practicar la presentación.** Si vas a vender análisis a tiendas, este informe
   te sirve de muestra sin usar datos de nadie.

---

## Los 16 errores (no lo leas antes de la práctica)

<details>
<summary>Ábrelo solo cuando ya tengas el informe delante, para comprobar el trabajo</summary>

1. El banner de la portada dice "ENVÍO GRATIS" sin condiciones. En realidad es
   gratis a partir de 80 €, y por debajo cuesta 5,90 € — que aparecen de sorpresa
   en el carrito.
2. La ficha del producto estrella **no tiene guía de tallas**, y vende de la S a
   la XL. Dice "las medidas son aproximadas" y no hay ninguna medida.
3. La ficha no dice **ni cuándo llega** ni **si se puede devolver**.
4. **Cero reseñas de producto** en toda la tienda, teniendo 4,6 sobre 5 en Google.
5. El checkout **obliga a crear cuenta** (no se puede comprar como invitado), tiene
   **14 campos** y el **NIF es obligatorio**.
6. El plazo de devolución se contradice tres veces: el pie de página dice
   **30 días**, la página de envíos dice **14 días**, y las preguntas frecuentes
   dicen que los artículos rebajados no se devuelven.
7. **No hay buscador** en toda la tienda, y la categoría tiene los 40 productos en
   una sola página sin filtros ni forma de ordenar.
8. Imágenes **JPG de casi 3 MB** (la portada, 3,8 MB) sin `loading="lazy"`, una
   sola foto por producto y sin zoom. La categoría pesa unos 112 MB en imágenes,
   con un 68 % de visitas desde el móvil.
9. **Sin datos estructurados** (`Product`, `Offer`): Google no sabe que eso es un
   producto con precio.
10. Un **pop-up a los 2 segundos** pidiendo el correo con un 10 % de descuento…
    que no manda nada: no hay ninguna herramienta de correo instalada. Cero
    recuperación de carrito abandonado.
11. Un **anuncio activo de "-20 % en toda la colección"** que lleva a la portada, y
    el -20 % **no existe** en ninguna parte de la web (el código no está creado).
12. **Instagram anuncia la camisa a 39 €** y la web la vende a 49 €. El enlace de
    la biografía va a la portada, y ninguna publicación enlaza a la ficha.
13. Reseñas externas sin responder que dicen **"tardó 12 días"** y **"no contestan
    al correo"**, mientras la web promete **24-48 horas**.
14. Los precios llevan **"IVA no incluido"** en letra pequeña en una tienda que
    vende a particulares: la camisa de 49 € se convierte en 65,19 € en el carrito.
15. Tiene **Google Analytics instalado pero no tiene el píxel de Meta**, y está
    pagando 180 € al mes en anuncios de Instagram.
16. **Cero post-venta**: no pide reseñas, no vuelve a escribir a quien ya le
    compró, no avisa de la colección nueva. Los correos del pop-up nunca se han
    usado.

Si el informe encuentra 13 o más y cada hallazgo viene con su cita o su cifra al
lado, el kit está funcionando.

</details>
