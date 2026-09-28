---
name: analisis-marca-personal
description: "Analiza una marca personal completa a partir del enlace de un perfil y de capturas de pantalla: nombre y bio, contenido y parrilla, ganchos, autoridad y prueba social, oferta visible, camino hasta la contratación y estadísticas reales. Puntúa cuatro fases del embudo (te encuentran, te entienden, te creen, te contratan) con evidencia, localiza la fuga, reescribe la bio y los ganchos y genera un informe HTML con plan de 30 días. Usa esta skill cuando el usuario quiera analizar una marca personal, revisar su perfil de Instagram, TikTok o LinkedIn, saber por qué su contenido no le trae clientes, mejorar su bio, mejorar su posicionamiento personal o preparar un diagnóstico de marca personal para un cliente. Triggers: 'analiza esta marca personal', 'analiza mi marca personal', 'analiza mi Instagram', 'revisa mi perfil', 'revisa mi LinkedIn', 'auditoría de marca personal', 'por qué no consigo clientes con mis redes', 'mi contenido no funciona', 'mejórame la bio', 'analiza la marca de ejemplo'."
---

# Análisis de Marca Personal

Le das el enlace de un perfil y unas capturas, y analizas el recorrido completo de
un desconocido hasta cliente: si la encuentran, si la entienden, si la creen y si
la contratan. La salida es un informe HTML con la nota de cada fase, **dónde está
la fuga**, la bio y los ganchos reescritos, tres pilares de contenido, diez ideas
concretas y un plan de 30 días.

**Regla fundamental: cero invención.** Cada afirmación se apoya en algo que has
leído de verdad — una captura, una URL, una frase literal. Si no lo has podido
comprobar, se marca "sin datos" y no puntúa. Un solo dato inventado destruye la
credibilidad del informe entero (y la venta).

**Segunda regla: se juzga el perfil, nunca la persona.** El contenido, la bio, la
oferta y el recorrido, sí. Su aspecto, su cuerpo, su voz, su acento o su vida
privada, no — ni aunque el usuario lo pida.

---

## Paso 0 — ¿Análisis real o de práctica?

Si el usuario dice "analiza la marca de ejemplo", "la de práctica" o similar,
entra en **modo práctica**:

- La marca es **Iria Loureiro** (`@irialoureiro.nutri`), nutricionista ficticia de
  Santiago de Compostela.
- No uses internet. Todo el material está en `ejemplos/marca-de-practica/`:
  - `perfil-instagram.md` — su perfil transcrito tal como se ve en la captura
    (nombre, bio, enlace, seguidores, destacados y los 12 últimos posts)
  - `estadisticas-30-dias.md` — su pantalla de Estadísticas
  - `otras-redes.md` — su TikTok, su LinkedIn y su web
  - `ficha-cliente.md` — sus respuestas a las preguntas de contexto del Paso 1
- Sáltate el Paso 1 (las respuestas ya están en `ficha-cliente.md`) y haz el resto
  **exactamente igual** que en un análisis real: leer, puntuar, localizar la fuga,
  reescribir, generar el HTML y presentarlo.
- Dilo al empezar en una línea: es una marca ficticia con errores metidos a
  propósito, y sirve para ver el sistema entero de principio a fin.
- El `[handle]` para los nombres de archivo es `irialoureiro-nutri`.
- Al presentar el informe, recuérdale que puede borrar los archivos de
  `workspace/` cuando quiera: son de práctica.

En cualquier otro caso es un análisis real: sigue en el Paso 1.

---

## Paso 1 — Recoger el material

### 1A · Lo que necesitas del usuario

Agrupa en **2 mensajes**, no de una pregunta en una.

**Mensaje 1 — el perfil y las capturas**

- **El enlace del perfil principal** y de las demás redes que tenga (Instagram,
  TikTok, LinkedIn, YouTube, X). Con @ o con URL.
- **Su web propia**, si tiene.
- **Las capturas.** Explícale que Instagram y TikTok no se pueden leer desde aquí
  — no es un fallo del kit, esas redes lo bloquean — y que con cinco capturas que
  hace en un minuto tú ves más de lo que vería cualquier raspador, porque la
  pantalla de Estadísticas solo la tiene el dueño de la cuenta. Pásale el guion:

  | # | Captura | Obligatoria |
  |---|---|---|
  | 1 | **Perfil completo**: foto, nombre, bio, enlace, botones, seguidores, destacados | Sí |
  | 2 | **La parrilla**: los últimos 9-12 posts en cuadrícula | Sí |
  | 3 | **Un post abierto** con su pie de foto y sus comentarios | Recomendada |
  | 4 | **Estadísticas → Últimos 30 días**: alcance, visitas al perfil, clics en el enlace, seguidores/no seguidores | La más valiosa |
  | 5 | **Su mejor post**, el que más funcionó, con sus números | Recomendada |

  Las guarda en la carpeta `entrada/` (arrastrar y soltar) y te avisa. El detalle
  completo, con las reglas de privacidad, está en `entrada/LEEME.md`.

**Mensaje 2 — el contexto**

- **¿A quién quiere llegar?** — su cliente ideal, con el máximo detalle que sepa.
- **¿Qué vende exactamente y a qué precio?** — servicio, sesión, programa,
  formación, y si tiene tarifas o rangos.
- **¿Cuál es su objetivo ahora?** — más clientes, subir precios, cambiar de
  público, que le inviten a hablar, vender un lanzamiento…
- **¿De dónde le vienen hoy los clientes?** — recomendación, redes, web, contactos
  antiguos. Si le vienen todos por recomendación y ninguno por sus redes, ya
  tienes el hallazgo más importante antes de empezar.
- **¿Hay 1-2 referentes de su sector** que le gusten? Sirven de contraste, no para
  copiarlos.
- **¿Qué cree que no funciona?** — a veces ya sabe dónde le duele.

Pregunta también, si no lo sabes por `.claude/setup-completado.json`, si analiza
**su propia marca** o la de **un cliente**: cambia el tono del informe.

> Guarda estas respuestas: en el Paso 4, comparar **lo que dice que hace** con
> **lo que enseña su perfil** es la fuente de los hallazgos más valiosos.

### 1B · Empezar sin esperar

Si todavía no tiene las capturas, **no te quedes parado**: adelanta lo que sí se
puede leer sin ellas (Paso 2A) y vuelve a por el resto cuando avise. Dile
exactamente eso, para que no sienta que está bloqueando el trabajo.

Si no piensa aportar capturas (por ejemplo, analiza a un cliente potencial que no
las va a dar): el análisis se hace igual con lo público, y las dimensiones que
dependan de las estadísticas quedan **"sin datos"**. Adviértele antes de empezar
para que no espere una nota que no vas a poder dar.

---

## Paso 2 — Leer y comprobar

**Abre el cuaderno de hallazgos antes de empezar.** Crea
`workspace/[handle]-hallazgos.md` y ve escribiendo cada dimensión en cuanto la
cierres: la evidencia literal, la nota y por qué. Dos razones: si la sesión se
corta no se pierde el trabajo (con "continúa el análisis" se retoma por la
primera dimensión que falte), y al montar el HTML no tendrás que recordar de
dónde salía cada cosa.

Narra al usuario cada fase en una línea mientras avanzas ("Buscando tu nombre en
Google…", "Leyendo la captura de la parrilla…"). Un análisis es largo: que no se
quede mirando una pantalla quieta.

### 2A · Lo que sí es público (el enlace)

- **Búscala por su nombre** (`WebSearch`): nombre solo, nombre + ciudad, nombre +
  profesión, y el @ del perfil. Apunta **qué aparece en los primeros resultados y
  en qué orden**: sus perfiles, su web, menciones, entrevistas, un podcast… o
  nada. Que no aparezca nadie con su nombre es un hallazgo grave de la fase 1, no
  un fallo del buscador: compruébalo con las tres variantes antes de afirmarlo.
- **LinkedIn sí se lee** desde el enlace público: `WebFetch` sobre
  `linkedin.com/in/[perfil]` devuelve titular, "acerca de" y experiencia.
  Aprovéchalo — es la red donde más se nota una marca personal abandonada.
- **Su web propia**: qué promete el inicio, si se entiende a quién ayuda, si hay
  una página de servicios con precios, si hay forma de contactar en un clic, si
  captura correos. Si devuelve 403 o vacío, prueba `curl` con user-agent de
  navegador antes de rendirte.
- **YouTube y X**: intenta el enlace; si no devuelve nada útil, búscalos por el
  buscador (los títulos de sus vídeos suelen aparecer indexados).
- **Instagram, TikTok y Facebook**: **no lo intentes más de una vez.** Están
  bloqueadas por diseño. Una comprobación y a las capturas.

### 2B · Las capturas (el núcleo del análisis)

Lista `entrada/` y lee cada imagen que haya. De cada una saca **lo que se ve
literalmente**, y escríbelo en el cuaderno tal cual, porque de ahí saldrán las
citas del informe:

**De la captura 1 (perfil):**
- El campo **Nombre** exacto (no el @): ¿lleva la palabra que busca su cliente o
  es solo su nombre de pila con un adorno?
- La **bio, palabra por palabra.** Cuenta los caracteres útiles: cuántos van a
  emojis y separadores y cuántos a decir algo.
- El **enlace**: a dónde lleva. Ábrelo y compruébalo — que el destino exista y sea
  el correcto es media fase 4.
- **Seguidores, seguidos y número de publicaciones.**
- Los **destacados** (highlights): sus nombres. ¿Hacen de menú de sus servicios o
  son "viajes", "gatos", "random"?
- **Botones**: contacto, correo, WhatsApp, tienda.

**De la captura 2 (parrilla):**
- **Los temas** de los 9-12 últimos posts. Agrúpalos: ¿cuántos temas distintos
  hay? Si no puedes agrupar en 3-4, no tiene pilares.
- **Los formatos**: vídeo corto, carrusel, foto suelta.
- **Legibilidad de las portadas en miniatura**: si el texto de las portadas no se
  lee a ese tamaño en tu propia lectura de la captura, no se lee en el móvil de
  nadie. Es una evidencia directa, no una opinión.
- **Coherencia visual**: si se reconoce que las publicaciones son de la misma
  persona sin mirar el nombre.

**De la captura 3 (post con comentarios):**
- La **primera línea del pie de foto**, literal. Es su gancho real.
- Si el pie **lleva a algún sitio** o se queda en el aire.
- **Interacción real**: número de comentarios, y de ellos cuántos son de personas
  preguntando algo. **¿Responde?** ¿Cuánto tiempo llevan sin respuesta?
- Una **pregunta comercial sin contestar** ("¿haces consulta online?", "¿precio?")
  es una venta perdida documentada: el hallazgo más contundente que puede llevar
  un informe. Cítala por su contenido, **nunca con el nombre de quien la escribe**.

**De la captura 4 (estadísticas) — la que enseña la fuga:**
- **Alcance** de 30 días y **% de cuentas que no la siguen** (si aparece).
- **Visitas al perfil** y **clics en el enlace**.
- **Seguidores nuevos**.
- Y ahora la lectura, que es lo que vale: compara los tres números en cadena.
  Mucho alcance con pocas visitas al perfil = la ven pero no les interesa lo
  suficiente para saber quién es (fase 2). Muchas visitas con casi ningún clic en
  el enlace = llegan al perfil y no encuentran motivo ni camino (fases 2 y 4).
  Pon la operación a la vista: "18.400 alcanzadas → 260 visitas al perfil (1,4 %)
  → 4 clics (1,5 % de las visitas)".
- **No inventes las tasas del sector.** Compara sus propios números entre sí, que
  es lo que de verdad demuestra algo, y no contra una media que no puedes probar.

**De la captura 5 (su mejor post):**
- **Qué formato, qué tema y qué gancho** tenía. Y si lo ha vuelto a repetir. Casi
  nadie lo repite: ahí está el primer punto del plan.

**Si una captura falta**, no la supongas: apunta qué dimensiones quedan sin datos
por eso y pídesela una vez más al terminar, ya con motivo concreto ("me falta
Estadísticas para poder decirte si la fuga está en la fase 2 o en la 4").

**Privacidad al leer capturas:**
- Si en una imagen ves teléfonos, correos, direcciones o datos de terceros:
  avisa al usuario y **no los incorpores** al informe ni al cuaderno.
- Nunca pidas capturas de mensajes privados. Si el usuario te manda una, no la
  analices y recuérdale la regla.
- En el informe, ninguna persona que comenta aparece con nombre.

### 2C · Las otras redes

Para cada red que tenga, aunque sea la secundaria:

- **¿Está viva o abandonada?** Fecha de lo último publicado. Un perfil abandonado
  es **peor que no tenerlo**: quien lo encuentra piensa que lo dejó.
- **¿Dice lo mismo que el principal?** Titular, foto, descripción. Una foto de
  hace ocho años o un titular obsoleto ("estudiante de…" llevando diez años
  ejerciendo) destruye la credibilidad justo donde están sus mejores clientes.
- **¿Hay algo enterrado que funcionó?** Un vídeo antiguo con muchas más
  visualizaciones que su media es una pista de oro para el plan.
- **LinkedIn**, si su cliente es empresa: es probable que sea su red más
  importante y la que tiene más descuidada. Míralo en serio.

### 2D · El cruce (donde salen los hallazgos que nadie ve)

Compara sistemáticamente y apunta cada choque:

- **Lo que dijo que vende** (Paso 1) **vs. lo que se entiende en su perfil.** Si
  dijo que lo suyo es X y en su bio y su parrilla X no aparece, ese es
  probablemente el hallazgo principal del informe.
- **Lo que dice ser vs. de qué habla.** "Especialista en X" y sus últimos diez
  posts son de Y.
- **A quién dice dirigirse vs. cómo escribe.** Si su cliente es un particular y
  escribe con la jerga de su carrera, no le está hablando a él.
- **La promesa vs. la prueba.** "+10 años de experiencia" sin un solo caso,
  testimonio o cifra que lo respalde. Muy común y muy caro.
- **Entre redes.** Bio, titular, foto y oferta distintas sin motivo.
- **Los destacados vs. la realidad.** Ofertas y precios antiguos que siguen ahí.
- **El enlace vs. su destino.** Que el enlace de la bio lleve a una web "en
  construcción", a una home genérica o a un 404 es fase 4 en el suelo.
- **Sus números entre sí** (captura 4), como en 2B.

---

## Paso 3 — Puntuar las 12 dimensiones y localizar la fuga

Cada dimensión de **0 a 100** con estos anclajes fijos, no a ojo:

| Nota | Significado |
|---|---|
| 0-20 | No existe |
| 21-40 | Existe pero está mal o abandonado |
| 41-60 | Cumple lo mínimo, sin nada que le diferencie |
| 61-80 | Bien hecho, con fallos concretos identificados |
| 81-100 | Referencia de su sector |

### Fase 1 · ¿Te encuentran? (25 puntos)

**1 · Perfil buscable.** ¿El campo Nombre lleva la palabra por la que su cliente
buscaría (profesión, especialidad, ciudad) o es solo su nombre de pila? ¿El @ es
el mismo en todas las redes y es escribible al oído? Al buscar su nombre en
Google, ¿aparece ella en los primeros resultados y con qué? *Nota baja: nombre sin
palabra clave y nada suyo en Google. Nota alta: la encuentras por nombre, por
profesión y por especialidad, y lo primero que sale es suyo y está actualizado.*

**2 · Formatos y distribución.** ¿Publica en los formatos que la red reparte hoy
(vídeo corto, carrusel) o solo fotos sueltas? ¿Qué porcentaje de su alcance viene
de gente que no la sigue (captura 4)? ¿Colabora con otras cuentas, sale en
podcasts, escribe donde ya hay audiencia? *Un alto porcentaje de no seguidores con
poca conversión a perfil es señal de que esta fase funciona y el problema está
más abajo: dilo, porque cambia todo el plan.*

**3 · Ganchos.** La primera línea de sus pies de foto y los primeros segundos de
sus vídeos: ¿abren con algo que hace parar o con "Buenos días, familia"? ¿Las
portadas se leen en miniatura? ¿Los titulares prometen algo concreto? *Cita tres
ganchos suyos literales como evidencia.*

### Fase 2 · ¿Te entienden? (25 puntos)

**4 · La prueba de los 5 segundos.** Leyendo **solo** foto, nombre y bio: ¿se
sabe **a quién ayuda**, **con qué** y **para conseguir qué**? Las tres, o no está
completa. *Nota baja: una bio de eslóganes y emojis que sirve para cualquiera de
su profesión. Nota alta: alguien de su público se ve retratado en la primera
línea.*

**5 · Nicho y diferencia.** ¿Se dirige a alguien concreto o a "todo el mundo"?
¿Tiene una forma propia de ver su trabajo, algo que defiende y que otros de su
sector no dirían, o repite lo que dice todo el mundo? ¿Se puede resumir su
posición en una frase? *"Para todos" es "para nadie": bájalo sin miedo.*

**6 · Pilares de contenido.** Agrupa sus 9-12 últimos posts por tema. ¿Salen 3-4
pilares reconocibles o siete temas sin relación? ¿Los temas sostienen lo que dice
ser y lo que vende, o son lo que se le ocurrió ese día? ¿Y hay algo de su vida
personal que aporta cercanía o solo relleno?

### Fase 3 · ¿Te creen? (25 puntos)

**7 · Prueba y resultados.** Casos reales, antes/después, cifras propias,
testimonios, trabajos publicados, clientes reconocibles, medios donde ha salido,
formación acreditada cuando importa en su sector. *Nota baja: afirmaciones sobre
sí misma sin nada detrás. Nota alta: puedes señalar tres pruebas verificables sin
buscar. Si no encuentras ninguna, dilo tal cual: no hay prueba pública.*

**8 · Criterio propio.** ¿Aporta un punto de vista o son consejos genéricos que
podrían firmar mil cuentas? ¿Cuenta procesos, decisiones y errores propios —lo
que nadie puede copiar— o solo resultados y frases? ¿Se moja en los debates de su
sector? ¿Se le ve trabajando?

**9 · Constancia y presencia.** Ritmo real de publicación y huecos (deduce las
fechas de lo que se vea en las capturas y en las otras redes). Perfiles
abandonados. Actividad reciente. *Un mes sin publicar en la red principal es un
hallazgo; un año en una secundaria abierta, otro.*

### Fase 4 · ¿Te contratan? (25 puntos)

**10 · Oferta visible.** ¿Se sabe **qué vende** sin preguntar? ¿Qué incluye? ¿A
qué precio o en qué rango? ¿Está a la vista desde el perfil, o hay que escribir
un mensaje privado para enterarse de todo? *En marca personal, "escríbeme por
privado para info" es la fuga más cara y más común: multiplica el esfuerzo por
cada interesado y filtra justo a quien no se atreve a preguntar.*

**11 · Camino sin fricción.** Cuenta los pasos desde "me interesa" hasta "he
hablado con ella o he pagado". ¿El enlace de la bio lleva al sitio correcto, y ese
sitio existe y funciona? ¿Los destacados hacen de menú (servicios, precios,
testimonios, cómo empezar) o son un cajón? ¿Responde comentarios y preguntas? ¿En
cuánto tiempo, por lo que se ve en la captura? *Cada paso de más es gente que se
cae. Y una pregunta comercial sin responder es una venta perdida que puedes
señalar con el dedo.*

**12 · Captación propia.** ¿Lleva a la gente a algo **suyo** — lista de correo,
web, comunidad, canal de difusión — o toda su audiencia está alquilada a una red
que puede cambiar el reparto mañana? ¿Tiene algún recurso propio que justifique
dejar un correo? *Sin nada propio, un cambio de algoritmo o un cierre de cuenta se
lleva su negocio entero: dilo con esas palabras.*

### El cálculo

- **Nota de cada fase** = media de sus 3 dimensiones, llevada a 25:
  `(media / 100) × 25`, con un decimal. Pon la operación a la vista en el informe.
- **Nota global** = suma de las cuatro fases, redondeada. 0-100.
- Bandas de la global: **0-39 crítico · 40-59 flojo · 60-74 aceptable · 75-89
  bueno · 90-100 referencia**.

Reglas de puntuación:

- Cada nota va con **al menos una evidencia literal** (la bio, un pie de foto, un
  número de una captura, una URL). **Sin evidencia no hay nota.**
- **Sin datos**: si no pudiste comprobar una dimensión, no entra en la media de su
  fase y el informe explica por qué. Nunca pongas una nota "prudente" para
  rellenar.
- Si una fase entera queda sin datos, no puntúa: la global se reescala sobre las
  fases que sí puntúan — `suma / (25 × nº de fases con nota) × 100` — y se dice en
  el informe.
- **Si lo que falta es un trozo de una dimensión, no la dimensión entera**, no la
  dejes sin datos: sería tirar evidencia buena. Puntúa con lo que sí está probado,
  marca el hueco a la vista dentro de esa dimensión y di qué cambiaría si se
  aportara. Dos ejemplos de lo que sale en el caso de práctica: no hay estadísticas
  de TikTok, pero sí lo público de TikTok (seguidores, nº de vídeos, fecha del
  último, reproducciones), así que la dimensión puntúa y el rendimiento actual de
  esa red queda marcado "sin datos"; y no consta si contesta los mensajes privados,
  así que se **pregunta al usuario** y, mientras no responda, la nota se pone con
  lo demás y la pregunta queda escrita en el informe como pendiente. Preguntar no
  bloquea el análisis: se sigue y se recoge la respuesta cuando llegue.
- Sé exigente. La mayoría de marcas personales pequeñas están entre **30 y 55**, y
  decirlo claro es el servicio que estás vendiendo. Un 80 es alguien que ya vive
  de su marca.

### La fuga

La fuga es **el eslabón del embudo donde se le cae la mayoría de la gente**. Se
localiza con la mejor prueba que tengas, en este orden:

**1) Si tienes la captura de Estadísticas, mandan sus números.** Cuenta cuánta
gente se pierde en cada salto y pon la cuenta a la vista:

    alcance  →  visitas al perfil  →  clics en el enlace (o mensajes)

La fuga es el salto donde se pierde **más gente en números absolutos**, y a cada
salto le corresponde una fase:

| El salto que se derrumba | La fase que lo explica |
|---|---|
| Alcance bajo, o casi todo el alcance viene de sus propios seguidores | Fase 1 · Te encuentran |
| Mucho alcance → pocas visitas al perfil | Fase 2 · Te entienden |
| Muchas visitas al perfil → casi ningún clic en el enlace ni mensajes | Fase 4 · Te contratan |

La fase 3 no aparece en esa pantalla: se lee del contenido y es lo que explica por
qué el salto de la 2 a la 4 no se completa. Si la fase 3 está en el suelo, dilo al
hablar de la fuga aunque la fuga esté en otra fase.

No compares sus porcentajes con medias del sector: **no las tienes** y no te las
puedes inventar. Compara sus propios números entre sí, que sí es demostrable.

**2) Si no hay estadísticas**, la fuga es la **primera fase, en orden del embudo,
que baja de 15/25**. Si ninguna baja de 15, la más baja; si hay empate, la más
temprana.

**En los dos casos**: si hay varias fases por debajo de 15/25 —lo normal en una
marca que no funciona—, dilo. Hay más de un agujero: se nombran todos y se tapan
**en orden de embudo**, porque arreglar el de abajo sin arreglar el de arriba no
cambia nada.

Y cuidado con la trampa: **una nota baja no es automáticamente la fuga.** Si sus
estadísticas dicen que la encuentran (mucho alcance, mucha gente que no la sigue),
la fase 1 **no es** la fuga aunque su perfil buscable y sus ganchos tengan mala
nota. Ahí esas notas bajas son margen de mejora, no la causa del problema. El dato
medido manda sobre el juicio del mecanismo.

El embudo es secuencial: un agujero arriba estropea todo lo de abajo. Da igual lo
buena que sea su oferta si nadie entiende a quién ayuda. **Todo el informe se
ordena alrededor de la fuga y el plan de 30 días empieza por ahí.**

Resúmela en una frase que el usuario pueda repetir de memoria. Por ejemplo: "te ve
mucha gente y casi nadie entiende a quién ayudas".

---

## Paso 4 — Escribir la prueba de los 5 segundos y los hallazgos

### La prueba de los 5 segundos

Escríbela **en primera persona**, como la diría alguien que acaba de llegar a su
perfil desde un vídeo y le ha dado tiempo a mirar cinco segundos:

> "Veo a una persona que habla de nutrición. Creo que es nutricionista, pero no
> sabría decir si trabaja con deportistas, con embarazadas o con quien quiere
> perder peso. No sé si puedo contratarla ni cuánto cuesta. Hay un enlace; no sé a
> dónde va."

Sale **solo** de la captura 1 y de lo que se ve sin pinchar. No añadas nada que
hayas averiguado después. Es la sección que más duele y más convence, y es
completamente honesta porque es exactamente lo que le pasa a su cliente.

### Los hallazgos

Para cada uno: **qué pasa · la evidencia literal · por qué le cuesta clientes ·
cómo se corrige · prioridad (alta / media / baja)**. Un problema sin solución al
lado es una queja, no un análisis.

Errores frecuentes que debes buscar activamente:

- Bio que sirve para cualquiera de su profesión
- Campo Nombre sin la palabra que busca su cliente
- Enlace de la bio a una home genérica, a una web "en construcción" o a un 404
- Parrilla sin pilares: cada post de un tema distinto
- Ganchos que empiezan saludando en lugar de decir algo
- Portadas con texto ilegible en miniatura
- Cero prueba: ni un caso, ni un testimonio, ni una cifra
- Consejos genéricos que podría firmar cualquiera
- Preguntas comerciales en comentarios sin responder
- Oferta y precio invisibles: "info por privado"
- Destacados que no hacen de menú
- Perfiles abandonados en otras redes
- Titular o foto obsoletos en LinkedIn
- Toda la audiencia alquilada: nada propio, ninguna lista de correo
- Un formato que le funcionó muy por encima de su media y que no ha repetido

---

## Paso 5 — Construir el plan (esta es la parte que se paga)

Todo lo de este paso son **propuestas**, y en el informe van marcadas como tales.
Se construyen con **sus** palabras, **sus** temas y **su** oferta: nada genérico.

### La bio reescrita

Su bio literal actual, y **2 alternativas** con la fórmula a la vista:

```
[A quién ayudo] + [con qué] + [para conseguir qué]
[Prueba en una línea]
[Siguiente paso concreto]
```

Que quepan en el límite de la red y que respeten su tono: si escribe cercano, la
propuesta va cercana. Explica en una línea qué cambia cada versión y por qué.

### Tres ganchos reescritos

Coge tres de **sus** primeras líneas o títulos reales y pon la versión mejorada al
lado, con una frase de por qué funciona mejor. Antes / después, con sus palabras.

### Los tres pilares de contenido

Deducidos de lo que ya le funciona (captura 5), de lo que vende y de a quién
quiere llegar. Para cada pilar: **nombre, qué entra ahí, qué formato le va mejor y
qué fase del embudo arregla.** Tres, no cinco: el objetivo es que se reconozcan.

### Diez ideas de contenido

Concretas y listas para grabar o escribir. Cada una con:

- su **titular o gancho** ya redactado,
- el **pilar** al que pertenece,
- la **fase** del embudo que arregla,
- y el **formato** sugerido.

Que al menos cuatro ataquen directamente la fuga. Si un tema suyo ya funcionó,
una de las ideas debe ser repetir ese formato con otro contenido.

### El plan de 30 días

Cuatro semanas, **empezando por la fuga**. Cada semana con 2-4 acciones concretas
y comprobables (no "mejorar el posicionamiento", sino "cambiar el campo Nombre a
X" o "grabar los tres vídeos del pilar 1"). La semana 1 es siempre lo que se
arregla una vez y queda arreglado: perfil, bio, enlace, destacados, oferta
visible.

Y **la primera acción de hoy**: una sola, que se haga en diez minutos.

---

## Paso 6 — Generar el informe HTML

Informe visual y ejecutivo. Libertad creativa en el diseño, contenido obligatorio.

### Secciones, en este orden

1. **Cabecera** — nombre y @ de la persona, redes analizadas, fecha y quién firma
   (nombre o agencia de `.claude/setup-completado.json`). Si ese archivo no existe
   todavía, no inventes una firma: en modo práctica pon "Análisis de práctica", y
   en un análisis real pregunta con qué nombre firmarlo.
2. **Titulares** — nota global /100 con su banda, las 4 fases con su X/25 en
   barras, y **la fuga señalada** con su frase.
3. **La prueba de los 5 segundos** — en primera persona, destacada.
4. **Resumen ejecutivo** — 3 párrafos: cómo se te ve hoy · qué te está costando ·
   qué cambia si arreglas la fuga.
5. **El embudo dibujado** — las cuatro fases en HTML y CSS, estrechándose de
   arriba abajo, con su nota y la fuga marcada. Sin imágenes ni dependencias
   externas.
6. **Fase por fase** — las 12 dimensiones: nota, evidencia literal, qué está bien,
   qué falla, qué hacer. Las "sin datos" marcadas como tales, nunca con un 0.
7. **Tu bio, reescrita** — la actual y las 2 alternativas, marcadas como propuesta.
8. **Tus ganchos, reescritos** — tres antes/después.
9. **Tus tres pilares de contenido.**
10. **Diez ideas de contenido** — tabla con titular, pilar, fase y formato.
11. **Plan de 30 días** — las cuatro semanas y la primera acción de hoy.
12. **Lo que NO debes cambiar** — lo que ya le funciona. Obligatoria.
13. **Nota metodológica** — qué se leyó y cuándo (enlaces y capturas, con fecha),
    qué quedó sin datos y por qué, y que no se ha accedido a ninguna cuenta ni a
    ningún dato privado más allá de las capturas que aportó el usuario.

### Requisitos del informe

- **Autocontenido**: CSS inline, sin dependencias, sin fuentes externas, sin
  imágenes remotas. Un archivo que se abre en cualquier navegador sin internet.
- **No incrustes las capturas** en el HTML: son del usuario y pueden llevar datos
  de terceros. Cítalas ("captura de Estadísticas, 30 días").
- **Responsive**: se lee bien en móvil, que es donde lo van a abrir.
- **Imprimible**: `@media print` sin secciones cortadas ni colores perdidos.
- **Navegación interna** entre secciones.
- **Cero emojis decorativos.** Tono profesional y directo.
- Que no parezca un informe genérico: cada afirmación con su evidencia al lado.

---

## Paso 7 — Guardar y presentar

Guarda en `workspace/`:

- `marca-personal-[handle].html` — el informe.
- `[handle]-plan-30-dias.md` — el mismo plan del punto 11, en Markdown y **con
  casillas** `- [ ]` para ir marcando. Es el archivo con el que va a trabajar.
- `[handle]-hallazgos.md` — el cuaderno: la trazabilidad del informe.

`[handle]` = el @ sin arroba, en minúsculas, sin tildes, con puntos y guiones
bajos convertidos en guiones: `@irialoureiro.nutri` → `irialoureiro-nutri`. Si no
hay @, el nombre de la persona: `iria-loureiro`.

Abre el informe en el navegador.

Presenta al usuario, en este orden y corto:

1. La **nota global** y su banda.
2. **Dónde está la fuga**, en la frase de memoria.
3. La **primera acción de hoy** (diez minutos).
4. Los dos caminos: profundizar en algo ("profundiza en la fase 2", "dame diez
   ideas más", "reescríbeme la bio con otro tono") o ponerse con el plan.

Si el análisis era de un cliente, recuérdale en una línea el orden con el que se
presenta en una llamada: la prueba de los 5 segundos primero, la fuga después, y
el plan al final.

---

## Reglas de la skill

- **Cero invención.** Ni seguidores, ni alcance, ni engagement, ni menciones, ni
  testimonios, ni medias del sector. Todo con evidencia o marcado "sin datos".
- **Se juzga el perfil, nunca la persona.** Nada sobre su aspecto, su cuerpo, su
  voz, su acento o su vida privada, ni aunque el usuario lo pida. Sí puedes decir
  si su foto cumple su función (se le reconoce en miniatura, encaja con su sector).
- **Honesto sin ser cruel.** Cada problema con su solución al lado. La sección "lo
  que NO debes cambiar" es obligatoria, y no es un adorno: si alguien ya hace algo
  bien y se lo cambias, le empeoras el resultado.
- **Propuesta y dato no se mezclan.** Bios, ganchos e ideas van marcados como
  propuestas.
- **Privacidad**: cero capturas de mensajes privados; ningún nombre de tercero que
  comente en el informe; si hay datos personales en una captura, avisar y no
  incorporarlos. Las capturas no se incrustan en el HTML.
- **El informe se le puede enseñar a la persona analizada.** Dentro no van las
  tarifas del usuario ni consejos de cómo venderle. Los precios que sí pueden ir
  son **los de la persona analizada**, cuando el hallazgo es sobre ellos (que no
  se ven, que no encajan con su posicionamiento).
- **Todo a `workspace/`.** Nunca dejes archivos sueltos en la raíz del kit.
