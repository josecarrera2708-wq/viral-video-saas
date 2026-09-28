# Kit 03 · Auditoría de Negocio — para Claude Code

> ¿Primera vez? Abre **[`EMPIEZA-AQUI.md`](EMPIEZA-AQUI.md)**: 3 pasos y a auditar.

Audita un negocio **por las dos caras** y devuelve **un solo informe HTML**:

- **Por fuera** — todo lo que el negocio enseña al mundo: su web, sus redes, lo
  que vende y a qué precio, cómo lo cuenta, sus anuncios activos en Meta, su ficha
  de Google, sus reseñas y su competencia. Se lee de internet, sin preguntarle nada.
- **Por dentro** — cómo funciona el día a día: por dónde le entran los clientes,
  dónde apunta las citas, cómo cobra, qué hace después de la venta, qué programas
  paga y cuántas horas se le van a mano. Sale de un formulario de 36 preguntas que
  el propio negocio rellena en 10 minutos.

Y lo que de verdad hace que valga: **cruza las dos mitades**. Ahí aparece lo que
no puede ver nadie que mire solo una — el anuncio que lleva a un WhatsApp que
nadie mira, la reseña de una estrella cuya causa está en la pregunta 12 del
formulario, la promesa que el proceso no puede cumplir.

Funciona con el modelo que ya tienes en tu Claude Code — no hay que configurar
ningún modelo ni ninguna API externa.

Sirve para dos cosas: **auditar tu propio negocio** (y arreglarlo) o **auditar el
de un cliente potencial** y enseñarle el informe. Un diagnóstico con sus frases,
sus números y sus contradicciones vende mucho mejor que una llamada a puerta fría.

## Las dos cifras del informe

No hay una nota única, hay dos, y **no se promedian**: miden cosas distintas.

**Nota digital (0-100)** — lo que el negocio enseña. Once dimensiones ponderadas:

| # | Dimensión | Qué mira | Peso |
|---|---|---|---|
| 1 | **Web y UX** | Primera impresión, propuesta de valor, CTAs, precios visibles, captación de emails, medición, velocidad | 15 |
| 2 | **Oferta y precios** | Qué vende exactamente, si el precio encaja con el posicionamiento, ofertas confusas, fricción de compra | 15 |
| 3 | **Copy y comunicación** | ¿Habla para el cliente o para sí mismo? CTAs genéricos, objeciones sin responder, tono entre canales | 12 |
| 4 | **Recorrido del cliente** | Del descubrimiento a la decisión, y el rastro visible de lo que pasa después | 12 |
| 5 | **Redes sociales** | Bio, link en bio, tipo de contenido, frecuencia, interacción real vs. seguidores | 10 |
| 6 | **Anuncios (Meta Ads)** | Qué tiene activo en la Biblioteca de Anuncios de Meta, desde cuándo, con qué mensaje y hacia dónde lleva | 8 |
| 7 | **Google Business / Maps** | Ficha reclamada, fotos, horarios, puntuación, si responde a las reseñas negativas | 8 |
| 8 | **Reputación** | Reseñas, testimonios, prueba social, patrones de queja repetidos | 6 |
| 9 | **Coherencia de marca** | Si cuenta la misma historia en web, redes y anuncios | 6 |
| 10 | **SEO básico** | Meta tags, encabezados, contenido indexable | 4 |
| 11 | **Contenido** | Blog o canal: si existe, si está vivo, si sirve para vender | 4 |
| — | **Competencia** | Comparativa lado a lado con 1-2 competidores que le des | No puntúa (es contexto) |

Anclajes fijos, no "a ojo": **0-20** no existe · **21-40** existe pero está mal o
abandonado · **41-60** cumple lo mínimo sin diferenciación · **61-80** bien hecho
con fallos concretos · **81-100** referencia del sector. Bandas de la nota global:
**0-39 crítico · 40-59 flojo · 60-74 aceptable · 75-89 bueno · 90-100 referencia**.

**Madurez tecnológica (1-5)** — cómo trabaja por dentro. Ocho áreas:

| Área | Qué mira |
|---|---|
| Captación y primer contacto | Por dónde entran los clientes y quién los atiende de verdad |
| Agenda y citas | Dónde se apunta, quién lo ve, si el cliente puede reservar solo |
| Cobro y facturación | Presupuestos, cobro, facturas, impagos |
| Comunicación y seguimiento | Recordatorios, confirmaciones, reseñas |
| Datos y medición | Dónde vive la información y qué números se miran |
| Retención y reactivación | Quién debería volver y a quién se le avisa |
| Seguridad, copias y RGPD | Copias, accesos, datos de clientes |
| IA y automatización actual | Qué se ha probado y qué pasó |

Los cinco niveles: **1** artesanal (papel y cabeza) · **2** herramientas sueltas
(WhatsApp y Excel sin conectar) · **3** digitalizado manual (hay herramienta, pero
la mueve una persona) · **4** conectado (las herramientas se hablan) · **5**
automatizado y medido. La mayoría de negocios locales están entre **1,5 y 2,5**.

Reglas que hacen que las cifras signifiquen algo:

- Cada nota de fuera va con **al menos dos evidencias**: una frase literal, una
  URL, una fecha, un número.
- Cada nivel de dentro va con **la cita literal del formulario y su número de
  pregunta**. Sin cita no hay nivel.
- Lo que **no aplica** a ese negocio no puntúa y su peso se reparte. Lo que
  aplica pero **no se pudo leer o no se contestó** sale como **"sin datos"**, con
  el motivo. Nunca se rellena con una estimación.

## Lo que sale del informe

Un único HTML autocontenido (se abre en cualquier navegador, se ve en el móvil, se
imprime a PDF) con 14 secciones. Las que más se miran:

- **Las dos cifras juntas** en la cabecera, cada una con su banda.
- **Lo que no cuadra** — las incoherencias, con **los cruces primero**: cada uno
  con su cita de fuera y su cita de dentro, una al lado de la otra.
- **Horas al mes recuperables y su coste**, calculado **solo** con las horas y el
  coste/hora que declaró el negocio, y con la operación a la vista para que la
  pueda comprobar.
- **Dos mapas del recorrido del cliente**: cómo funciona hoy (pasos manuales en
  naranja, fugas en rojo) y cómo funcionaría (lo automatizado en azul). El mismo
  recorrido, de cuando descubre el negocio a si vuelve o no. Salen también en
  `.excalidraw`, así que se pueden editar y exportar para una presentación.
- **Un solo plan de acción**, ordenado por retorno, con una columna que dice si
  cada línea viene de fuera, de dentro o **del cruce**.
- **Lo que NO conviene automatizar todavía** — con su motivo. Es lo que convierte
  la auditoría en un consejo y no en un catálogo.

## Qué hay en el kit

| Pieza | Qué es |
|---|---|
| `EMPIEZA-AQUI.md` | Los 3 pasos para dejarlo funcionando (empieza por aquí) |
| `.claude/commands/setup.md` | El asistente `/setup`: comprueba qué puede leer, prueba el generador de mapas, te entrega el formulario y te propone la auditoría de práctica |
| `.claude/commands/auditoria.md` | El comando `/auditoria`: lanza una auditoría nueva preguntándote el contexto |
| `.claude/skills/auditoria-negocio/` | La skill: el sistema completo de las dos mitades, el cruce y el informe (esto es lo que garantiza el resultado) |
| `formulario/` | El formulario de 36 preguntas que le mandas al negocio para la mitad de dentro |
| `entrada/` | Donde dejas los formularios que te devuelven. **No sale de tu ordenador** |
| `ejemplos/negocio-de-practica/` | Una peluquería ficticia con errores metidos a propósito, por fuera y por dentro, para tu primera auditoría sin gastar en un negocio real |
| `scripts/` | El dibujante de los mapas (Python de librería estándar, no instala nada) |
| `workspace/` | Donde aparecen tus informes y tus mapas |

## Cómo se usa

Después de `/setup`, una frase:

```
audita este negocio: [URL]
```

Claude te pregunta el contexto en dos bloques (qué vende y a quién · objetivo,
competidores, canales y qué cree que no funciona), investiga narrando lo que va
encontrando y, si además le has dado el formulario relleno, cruza las dos mitades.

Las tres formas de arrancar:

| Tienes | Escribes | Qué sale |
|---|---|---|
| La URL del negocio | `audita este negocio: [URL]` | La mitad de fuera completa; la de dentro, "sin datos" |
| El formulario relleno en `entrada/` | `audita este formulario` | La mitad de dentro completa; la de fuera, "sin datos" |
| Las dos cosas | `audita este negocio: [URL]` (con el formulario ya en `entrada/`) | **Auditoría completa, con el cruce** |

Y si tienes al cliente al teléfono: *"hazme la auditoría en modo entrevista"* y
Claude te va preguntando por bloques mientras hablas.

Al terminar, en `workspace/`:

- `auditoria-[negocio].html` — el informe completo.
- `auditoria-[negocio]-mapa-1.svg` y `-mapa-2.svg` — los dos mapas.
- `auditoria-[negocio].excalidraw` — los mapas editables.
- `[negocio]-hallazgos.md` — el cuaderno con la evidencia de cada afirmación.

Si quieres profundizar después: *"profundiza en el copy"*, *"profundiza en la
competencia"* o *"profundiza en la seguridad"* amplía solo esa parte y actualiza
el mismo informe.

## El formulario de la mitad de dentro

Está en [`formulario/`](formulario/). Son 36 preguntas en 7 bloques, escritas para
que las entienda cualquiera: nada de "stack tecnológico" ni "CRM". Se rellena en
unos 10 minutos.

Vienen dos versiones con las mismas preguntas numeradas (P1 a P36):
`formulario-cliente.md` para pegarlo en un email o un WhatsApp, y
`formulario-cliente.html` para mandarlo como archivo — se abre con doble clic, se
rellena en el navegador, se va guardando solo mientras el cliente escribe y trae
un botón "Copiar mis respuestas" que devuelve el texto listo para pegar, con las
preguntas sin contestar marcadas como tales. Esa numeración importa: el informe
cita las respuestas por su número, así que si editas el formulario, quita
preguntas pero **no las renumeres**.

Dos cosas que conviene decirle al negocio al mandarlo:

- **No hace falta ningún dato de sus clientes.** Solo se pregunta por
  herramientas y procesos: dónde apunta las citas, quién coge el teléfono, qué
  programas paga.
- **Con respuestas aproximadas vale.** Es mejor "unas 3 horas a la semana" que
  dejarlo en blanco. Lo que se queda en blanco sale en el informe como "sin
  datos", que también es información.

Lo que devuelva se guarda en [`entrada/`](entrada/), que está en `.gitignore`: no
sale de tu ordenador.

## Privacidad: lo que NO entra en una auditoría

La mitad de dentro es la única parte que escribe un tercero, así que se revisa
antes de auditar nada. Si en `entrada/` aparece un listado de clientes, fichas,
historiales, facturas, una exportación de base de datos, contraseñas o accesos a
programas, **Claude se para**, te avisa, te pide que lo quites y no lo incorpora
al informe.

El nombre de un empleado sí puede aparecer (el formulario los usa para explicar
quién hace qué); en el informe se cita por su rol cuando ayuda.

Y queda dicho en el propio informe: **no se ha accedido a ningún sistema del
negocio**. La auditoría se hace sobre lo que es público y lo que el negocio
cuenta. Eso, además de ser lo correcto, es lo que hace que un negocio te deje
auditarlo sin firmar nada.

## Lo que este kit NO hace

Ser honesto con esto evita decepciones:

- **No entra en nada privado ni en ningún sistema.** No ve su Google Analytics,
  ni su facturación, ni su programa de gestión, ni sus conversiones reales. Todo
  lo de dentro sale de lo que el negocio cuenta, no de mirar sus paneles.
- **No mide el rendimiento de sus anuncios.** La Biblioteca de Anuncios de Meta es
  pública y enseña qué anuncios tiene activos y desde cuándo, pero no el gasto ni
  los resultados. Que un anuncio lleve meses activo es una **señal** de que le
  funciona, no una prueba.
- **Las redes sociales a veces no se pueden leer.** Instagram, TikTok y Facebook
  bloquean la lectura automática con frecuencia. Cuando pasa, Claude te pide que
  pegues la bio o una captura (30 segundos desde tu móvil) o marca esa dimensión
  como "sin datos". Nunca se la inventa.
- **No es un informe legal.** Los riesgos de datos se cuentan por sus
  consecuencias, no citando artículos ni sanciones.
- **No arregla nada.** Detecta y prioriza; ejecutar los arreglos es el trabajo que
  vas a cobrar aparte.

## Si usas Windows

- Claude Code necesita **Git para Windows** (git-scm.com/download/win): es quien
  le da a Claude la terminal que usa por dentro. Se instala dándole a "siguiente"
  hasta el final, y de paso trae el Python que dibuja los mapas.
- Los comandos los ejecuta Claude por ti — tú no abres ninguna terminal.
- Cuando este kit muestra rutas de ejemplo, la tuya será del estilo
  `C:\Users\tu-nombre\Escritorio\auditoria-negocio`.

## Seguridad

- Trabaja con **información pública** del negocio (lo que cualquiera ve entrando
  en su web, su Instagram o su ficha de Google) y con **sus procesos** (lo que te
  cuenta en el formulario). Nada más.
- No metas en las auditorías datos privados de los clientes de ese negocio,
  facturación, contraseñas ni datos personales. Si aparecen, Claude para.
- Si auditas el negocio de otra persona, recuerda que el informe es un análisis de
  lo que esa empresa publica y de lo que ella misma ha contado. Preséntalo como
  diagnóstico profesional, no como una lista de reproches.
- Anthropic no entrena sus modelos con el tráfico de API ni con tu uso de Claude
  Code.

## Si la auditoría se corta a mitad

Una sesión larga puede interrumpirse (la conexión, el límite de uso de tu plan…).
**No pierdes nada**: mientras audita, la skill va escribiendo un cuaderno de
hallazgos en `workspace/[negocio]-hallazgos.md` — cada bloque cerrado, con su
evidencia — antes de montar el HTML final.

- Abre de nuevo la conversación y di *"continúa la auditoría donde la dejaste"*.
- Retoma por lo primero que falte en el cuaderno; lo ya investigado no se repite.
- El cuaderno se queda ahí al terminar: es la trazabilidad del informe, de ahí
  sale cada afirmación del HTML.

## Cuánto cuesta cada auditoría

El kit usa el modelo que ya tienes en Claude Code, así que el coste es el de tu
cuenta de Claude:

- **Con suscripción (Pro o superior)**: la auditoría consume el uso incluido en tu
  plan — no pagas nada aparte. Una auditoría completa es una sesión larga (lee
  muchas páginas); si tu plan es justo, lánzala cuando no necesites Claude para
  otra cosa.
- **Con cuenta API**: pagas por uso. Una auditoría completa suele salir por unos
  pocos euros.

## Cómo se cobra (rangos de mercado 2026)

Para la auditoría **completa**: las dos mitades, los dos mapas y la hoja de ruta.

- **Negocio local**: 400-900 €
- **Empresa mediana**, con presentación y hoja de ruta: 1.500-3.000 €
- Si entregas **solo una mitad**: la parte baja del rango
- **Implantar** lo que detecta el informe: aparte, desde 1.200 €
- **Acompañamiento mensual**: 200-500 €/mes

La auditoría es la puerta de entrada: quien te paga el diagnóstico te contrata el
arreglo. Los precios los pones tú — estos son rangos de referencia.

---

> Cualquier duda → pregúntala en la comunidad donde conseguiste el kit. Allí te
> ayudamos a aplicarlo a tu caso real.
