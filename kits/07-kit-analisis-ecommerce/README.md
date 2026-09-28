# Kit 07 · Análisis de Ecommerce — para Claude Code

> ¿Primera vez? Abre **[`EMPIEZA-AQUI.md`](EMPIEZA-AQUI.md)**: 3 pasos y a analizar.

Le pasas la URL de una tienda online y Claude Code la recorre como la recorrería
un comprador —home, categoría, ficha de producto, carrito, checkout hasta el
último paso antes de pagar— mira de dónde le viene el tráfico (redes, anuncios
activos, reseñas) y te devuelve **un informe en HTML** con nota global, las fugas
por las que se le escapan las ventas, el mapa del embudo de compra con los puntos
donde la gente se cae, y un plan priorizado.

Y algo más tangible: **la ficha de su producto estrella reescrita entera**, lista
para copiar y pegar, con título, bullets, descripción, tabla de medidas, textos de
envío y devolución, preguntas frecuentes y los datos estructurados para que salga
con precio en Google.

Funciona con el modelo que ya tienes en tu Claude Code — no hay que configurar
ningún modelo ni ninguna API externa.

Sirve para dos cosas: **arreglar tu propia tienda** o **analizar la de un cliente
potencial** y enseñarle el informe. Un diagnóstico con sus precios, sus textos y
sus cifras vende mucho mejor que una llamada a puerta fría.

## Las 13 dimensiones que analiza

Agrupadas en tres bloques: la tienda, el tráfico que llega y lo que pasa después
de la primera compra.

### La tienda (66 puntos de la nota)

| # | Dimensión | Qué mira | Peso |
|---|---|---|---|
| 1 | **Ficha de producto** | Fotos, título, descripción, variantes, stock, plazo de entrega, devolución visible, reseñas, productos relacionados | 14 |
| 2 | **Carrito y checkout** | Cuántos pasos y cuántos campos hasta pagar, si se puede comprar sin registrarse, costes que aparecen al final, métodos de pago | 14 |
| 3 | **Confianza y transparencia** | Envíos y devoluciones claros, páginas legales, datos de contacto reales, sellos y pasarelas de pago reconocibles | 10 |
| 4 | **Catálogo y navegación** | Categorías, filtros, orden, buscador interno, cuántos clics hay del inicio al producto | 8 |
| 5 | **Precio y ticket medio** | IVA claro, umbral de envío gratis, packs, venta cruzada, opciones de cantidad | 8 |
| 6 | **Móvil y velocidad** | Peso real de las imágenes (medido, no estimado), formatos, carga diferida, primera impresión en móvil | 8 |
| 7 | **SEO de tienda** | Títulos y descripciones de producto y categoría, datos estructurados, sitemap, categorías indexables | 4 |

### El tráfico (22 puntos)

| # | Dimensión | Qué mira | Peso |
|---|---|---|---|
| 8 | **Captación y recuperación** | Email y SMS, recuperación de carrito abandonado, qué pide el pop-up y qué manda después | 8 |
| 9 | **Anuncios (Meta Ads)** | Qué anuncia en la Biblioteca de Anuncios de Meta, desde cuándo, con qué oferta y dónde aterriza el que hace clic | 6 |
| 10 | **Redes como canal de venta** | Link en bio, contenido que lleva a producto, tienda etiquetada, si los precios coinciden con la web | 5 |
| 11 | **Medición** | Analítica, píxeles, eventos de compra, aviso de cookies | 3 |

### La retención (12 puntos)

| # | Dimensión | Qué mira | Peso |
|---|---|---|---|
| 12 | **Retención y recompra** | Qué pasa después de comprar: seguimiento, petición de reseñas, recurrencia, fidelización, clientes dormidos | 7 |
| 13 | **Reputación y reseñas** | Reseñas de producto y externas, patrones de queja (envíos, devoluciones, atención) y si alguien responde | 5 |

La **competencia** se analiza aparte y no puntúa: es contexto para saber dónde
está la tienda frente a quien le compite.

## Cómo puntúa (para que la nota signifique algo)

Cada dimensión se puntúa de 0 a 100 con anclajes fijos, no "a ojo":

| Nota | Qué significa |
|---|---|
| 0-20 | No existe |
| 21-40 | Existe pero está mal o abandonado |
| 41-60 | Cumple lo mínimo, sin nada que le diferencie |
| 61-80 | Bien hecho, con fallos concretos identificados |
| 81-100 | Referencia del sector |

La **nota global** es la media ponderada con los pesos de las tablas de arriba.

- Si una dimensión **no aplica** (una tienda de productos digitales sin envíos,
  una tienda que no hace publicidad), no puntúa y su peso se reparte entre las
  demás. Se dice en el informe.
- Si una dimensión **aplica pero no se pudo leer** (un checkout que exige cuenta,
  un Instagram tras login), queda como *sin datos*: tampoco puntúa, y el informe
  explica por qué.
- Cada nota va con **evidencia**: una frase literal de la ficha, una URL, un
  precio, el peso en MB de una foto. Sin evidencia no hay nota.

Bandas de la nota global: **0-39 crítico · 40-59 flojo · 60-74 aceptable ·
75-89 bueno · 90-100 referencia**.

## Los euros: cómo se calculan sin inventar nada

Aquí está la diferencia entre un informe que se lee y uno que se compra. El kit
puede poner una cifra al lado de cada oportunidad, pero **solo con tus números
reales** y siempre con tres capas separadas a la vista:

1. **Tus números (reales).** Visitas al mes, tasa de conversión, ticket medio,
   pedidos al mes, margen. Los saca el dueño de su panel en dos minutos:
   *Shopify → Analytics · WooCommerce → Estadísticas · Google Analytics 4*.
2. **La mejora (hipótesis).** Cuánto puede subir esa palanca. Va **siempre**
   etiquetada como *escenario*, con el rango de referencia del sector y el
   razonamiento al lado. Nunca como promesa.
3. **La cuenta (a la vista).** La operación escrita en el informe:

   > `6.400 visitas × (0,7 % → 1,0 %) = +19 pedidos/mes × 46 € de ticket medio =`
   > **`+874 €/mes`** — *escenario, no previsión*

**Sin esos números no aparece ni un euro en el informe.** No se estima el tráfico
por el tamaño de la tienda, ni la conversión por "la media del sector", ni el
ticket medio por los precios del catálogo. El análisis se hace igual y las
oportunidades se ordenan por impacto y esfuerzo.

Si consigues los números más tarde, se recalculan los euros sin repetir el
análisis: el cuaderno de hallazgos ya está escrito.

## Qué hay en el kit

| Pieza | Qué es |
|---|---|
| `EMPIEZA-AQUI.md` | Los 3 pasos para dejarlo funcionando (empieza por aquí) |
| `.claude/commands/setup.md` | El asistente `/setup`: comprueba qué puede leer y te propone el análisis de práctica |
| `.claude/commands/analiza.md` | El comando `/analiza`: lanza un análisis nuevo preguntándote el contexto |
| `.claude/skills/analisis-ecommerce/` | La skill: el sistema completo de análisis (esto es lo que garantiza el resultado) |
| `ejemplos/tienda-de-practica/` | Una tienda de ropa de lino ficticia con 16 errores metidos a propósito, para tu primer análisis sin gastar en una tienda real y sin internet |
| `workspace/` | Donde aparecen tus informes |

## Cómo se usa

Después de `/setup`, una frase:

```
analiza esta tienda: [URL]
```

Claude te preguntará el contexto en dos bloques (qué vende, producto estrella,
competidores · y los cuatro números opcionales de su panel), recorrerá la tienda
narrando lo que encuentra, y al terminar tendrás en `workspace/`:

- **`analisis-ecommerce-[tienda].html`** — el informe completo: nota global y por
  área, resumen en 3 párrafos, las fugas ordenadas por lo que cuestan, el mapa
  del embudo de compra con los puntos de caída, diagnóstico de las 13
  dimensiones con evidencia, palancas de ticket medio con su cuenta, comparativa
  con la competencia, plan priorizado y quick wins de esta semana.
- **`[tienda]-ficha-[producto]-reescrita.md`** — la ficha de su producto estrella
  reescrita entera y lista para pegar: título, 5 bullets de venta, descripción
  larga, tabla de medidas, bloque de envío y devolución con sus plazos reales, 5
  preguntas frecuentes sacadas de sus objeciones reales, y el bloque de datos
  estructurados para que el producto salga con precio y valoración en Google.
- **`[tienda]-hallazgos.md`** — el cuaderno de trabajo: cada dimensión con la
  evidencia literal de la que salió su nota. Es la trazabilidad del informe.

El informe es un archivo autocontenido: se abre en cualquier navegador, se ve
bien en el móvil y se imprime a PDF para mandarlo.

Si quieres profundizar después: *"profundiza en el checkout"* o *"reescribe la
ficha de [otro producto]"* amplía solo esa parte.

## Lo que este kit NO hace

Ser honesto con esto evita decepciones:

- **No compra nada.** Recorre el camino hasta el último paso antes de pagar y
  para. Cero datos de tarjeta, cero pedidos completados, cero cuentas creadas en
  tiendas ajenas.
- **No entra en ningún panel privado.** No ve su Shopify por dentro, ni su Google
  Analytics, ni sus pedidos, ni sus márgenes reales, ni cuánto gasta en
  publicidad. Los números los aporta el dueño si quiere.
- **No mide el rendimiento de sus anuncios.** La Biblioteca de Anuncios de Meta es
  pública y enseña qué anuncios tiene activos y desde cuándo, pero no el gasto ni
  los resultados. Que un anuncio lleve meses activo es una **señal** de que le
  funciona, no una prueba.
- **No promete ventas.** Los euros del informe son escenarios calculados con los
  números del dueño y una hipótesis de mejora etiquetada como tal. Un informe que
  promete facturación es un informe que miente.
- **Los carritos y checkouts a veces no se pueden leer** (se montan con
  JavaScript, o exigen cuenta). Cuando pasa, Claude usa un navegador si lo hay, o
  te pide que lo recorras tú y le cuentes los pasos, o marca esa parte "sin
  datos". Nunca se la inventa.
- **No arregla la tienda.** Detecta, prioriza y escribe los textos; ejecutar los
  arreglos es el trabajo que vas a cobrar aparte.

## Si usas Windows

- Claude Code necesita **Git para Windows** (git-scm.com/download/win): es quien
  le da a Claude la terminal que usa por dentro. Se instala dándole a
  "siguiente" hasta el final.
- Los comandos los ejecuta Claude por ti — tú no abres ninguna terminal.
- Cuando este kit muestra rutas de ejemplo, la tuya será del estilo
  `C:\Users\tu-nombre\Escritorio\kit-analisis-ecommerce`.

## Seguridad

- Trabaja con **información pública**: lo que cualquiera ve entrando en la tienda,
  en su Instagram o en sus reseñas. No metas en los análisis datos de clientes,
  pedidos reales, exportaciones de bases de datos ni accesos al panel.
- **Nunca des a Claude las claves del panel de la tienda.** Este kit no las
  necesita para nada.
- Si analizas la tienda de otra persona, recuerda que el informe es un análisis de
  lo que esa tienda publica. Preséntalo como diagnóstico profesional, no como una
  lista de reproches.
- Anthropic no entrena sus modelos con el tráfico de API ni con tu uso de
  Claude Code.

## Si el análisis se corta a mitad

Una sesión larga puede interrumpirse (la conexión, el límite de uso de tu plan…).
**No pierdes nada**: mientras analiza, la skill va escribiendo el cuaderno
`workspace/[tienda]-hallazgos.md` — cada dimensión cerrada, con su evidencia y su
nota — antes de montar el HTML final.

- Abre de nuevo la conversación y di *"continúa el análisis donde lo dejaste"*.
- Retoma por la primera dimensión que falte en el cuaderno; lo ya investigado no
  se repite.
- El cuaderno se queda ahí al terminar: de ahí sale cada afirmación del informe.

## Cuánto cuesta cada análisis

El kit usa el modelo que ya tienes en Claude Code, así que el coste es el de tu
cuenta de Claude:

- **Con suscripción (Pro o superior)**: el análisis consume el uso incluido en tu
  plan — no pagas nada aparte. Un análisis completo es una sesión larga (recorre
  muchas páginas); si tu plan es justo, lánzalo cuando no necesites Claude para
  otra cosa.
- **Con cuenta API**: pagas por uso. Un análisis completo suele salir por unos
  pocos euros.

## Cómo se cobra (rangos de mercado 2026)

- **Análisis de una tienda pequeña**: 400-800 €
- **Análisis con presentación y hoja de ruta**, catálogo grande: 1.200-2.500 €
- **Arreglar** lo que detecta el informe: aparte, desde 900 €
- **Optimización mensual** con test A/B: 300-700 €/mes

El análisis es la puerta de entrada: quien te paga el diagnóstico te contrata el
arreglo. Los precios los pones tú — estos son rangos de referencia.

---

> Cualquier duda → pregúntala en la comunidad donde conseguiste el kit. Allí te
> ayudamos a aplicarlo a tu caso real.
