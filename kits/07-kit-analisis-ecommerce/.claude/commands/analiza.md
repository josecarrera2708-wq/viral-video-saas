---
description: Analiza una tienda online completa y genera el informe + la ficha reescrita
---

Lanza un análisis de ecommerce nuevo usando la skill `analisis-ecommerce`.

Antes de investigar nada:

1. Si el usuario ha escrito una URL junto al comando, dala por recibida y no la
   vuelvas a preguntar.
2. Si no ha escrito nada, pregunta primero qué tienda se analiza (la URL).
3. Sigue con los dos bloques de preguntas del Paso 1 de la skill (la tienda ·
   sus números), agrupados en dos mensajes, no de uno en uno. El bloque de
   números va marcado como **opcional** y con la pista de dónde encontrarlos
   (Shopify → Analytics · WooCommerce → Estadísticas · Google Analytics 4).

Después ejecuta la skill completa: detectar la plataforma, recorrer la tienda
como un comprador, puntuar con evidencia, calcular las palancas con la cuenta a
la vista, generar el informe HTML y la ficha de producto reescrita en
`workspace/`, y presentarlo.

Recuerda las dos reglas duras mientras recorres: **nunca completes una compra**
(paras en el último paso antes de pagar, sin datos de tarjeta y sin crear
cuentas) y **sin los números del dueño no aparece ningún euro** en el informe.

Si el usuario quiere probar el kit sin gastar en una tienda real, dile que escriba
*"analiza la tienda de ejemplo"*: la tienda de lino ficticia de
`ejemplos/tienda-de-practica/` (Paso 0 de la skill).
