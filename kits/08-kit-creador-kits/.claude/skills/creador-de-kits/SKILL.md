---
name: creador-de-kits
description: "Construye kits de Claude Code completos y funcionales a partir de una idea descrita en lenguaje normal: entrevista al usuario, escribe un contrato de construcción, comprueba de verdad que la vía de datos funciona antes de escribir una línea, define el criterio de calidad o el sistema de puntuación, genera los documentos (EMPIEZA-AQUI, README, CLAUDE.md), el asistente de instalación /setup, la skill principal y un ejemplo de práctica con errores plantados, ejecuta el kit recién hecho contra ese ejemplo para destapar defectos, pasa la lista de calidad de espectador y lo deja listo para usar o empaquetar en ZIP. Usa esta skill cuando el usuario quiera crear un kit, una herramienta o un asistente propio para Claude Code, automatizar una tarea que repite, convertir su forma de trabajar en algo reutilizable, o preparar un kit para entregar o vender a un cliente. Triggers: 'quiero un kit que', 'necesito algo que', 'créame un kit', 'crea un kit de', 'hazme una herramienta que', 'quiero automatizar', 'monta un asistente para', 'kit nuevo', 'continúa el kit', 'quiero vender un kit', 'dame ideas de kits'."
---

# Creador de kits

Le construyes al usuario un kit de Claude Code a partir de una frase suya. El
resultado vive en `mis-kits/NN-nombre-del-kit/` y es un kit de verdad: se abre en
VS Code, arranca con su asistente de instalación, hace su trabajo y deja el
resultado en su `workspace/`.

Nueve pasos, en orden. Los pasos **3** (comprobar antes de escribir) y **7**
(correr el kit contra su ejemplo) son los que hacen que el kit funcione en manos de
otra persona. No se saltan nunca, ni con prisa.

Narra en una línea lo que estás haciendo en cada fase ("Escribiendo el contrato…",
"Comprobando si esa página se puede leer…", "Corriendo tu kit contra su ejemplo…").
El usuario tiene que ver que avanzas, no una pantalla en blanco durante diez minutos.

---

## Paso 0 — ¿Kit nuevo o uno a medias?

1. Mira `mis-kits/`. Si hay carpetas con `_CONTRATO.md`, lee el apartado **Estado**
   de cada uno.
2. Si alguno está sin terminar, dilo antes de nada: "Tienes el kit *[nombre]* a
   medias, se quedó en el paso *[N]*. ¿Lo terminamos o empezamos otro?".
3. Si retoma: sigue por el primer paso sin marcar. **Lo ya hecho no se repite** —
   ni la entrevista, ni las comprobaciones que ya salieron ✓.
4. Si es nuevo: sigue al Paso 1.

Si el usuario no sabe qué kit quiere, no le hagas pensar en abstracto. Enséñale
`ideas-de-kits.md` y hazle **una** pregunta: ¿qué tarea repites más veces al mes y
cuánto tiempo te come cada vez? El mejor kit sale de esa respuesta.

---

## Paso 1 — La entrevista

Dos tandas cortas. Nunca un interrogatorio de doce preguntas seguidas: se responde
en dos mensajes y se avanza. Lee `referencias/entrevista.md` para el detalle de qué
dispara cada respuesta.

### Tanda 1 — Qué y para quién (4 preguntas, en un solo mensaje)

1. **Qué tarea hace el kit.** En sus palabras. Si dice algo vago ("mejorar mi
   marketing"), pídele el ejemplo concreto de la última vez que lo hizo a mano.
2. **Qué tiene delante cuando empieza** esa tarea: una web, un PDF, unas fotos, una
   hoja de cálculo, un vídeo, nada.
3. **Qué querría tener al terminar**, y en qué forma: un informe para enseñar, unos
   textos para pegar, unos archivos ya procesados, algo funcionando.
4. **Para quién es el kit**: para él, o para dárselo a un cliente. Si es para un
   cliente, ¿lleva su nombre o va en blanco?

### Tanda 2 — Solo lo que falte

Según lo que haya contestado, pregunta **solo** lo que no puedas deducir:

- Si los datos vienen de internet: ¿de qué páginas exactamente? Pide una URL real
  de ejemplo. La necesitas en el Paso 3.
- Si vienen de sus archivos: ¿qué formato y de dónde los saca? Pide uno de muestra
  si lo tiene (aunque sea con los datos cambiados).
- Si hay que puntuar o valorar algo: ¿qué es "bien" y qué es "mal" para él? Dos
  ejemplos reales, uno bueno y uno malo, valen más que una hora de teoría.
- Si el kit tiene que ejecutar algo (convertir, redimensionar, transcribir): ¿lo ha
  hecho antes con algún programa concreto?

### La promesa de una frase

Cierra el paso escribiendo la promesa y **haz que te la confirme**:

> **Entra** [qué le da el usuario] → **sale** [qué recibe, con nombre de archivo].

Ejemplo: *"Entra el PDF de un contrato de alquiler → sale un informe HTML con las
cláusulas marcadas por riesgo y un correo de respuesta al casero listo para enviar."*

**Sin esa frase confirmada no se avanza.** Es lo que después se convierte en el
título del README y en la primera línea del `EMPIEZA-AQUI.md`. Si no cabe en una
frase, el kit hace demasiadas cosas: recorta a la tarea que más repite.

### El nombre y la carpeta

Propón nombre de carpeta con la convención del proyecto: `NN-kit-nombre-corto`,
números en orden dentro de `mis-kits/` (el primero es `01-`). Sin preposiciones,
sin acentos, sin espacios, todo en minúsculas. Confírmalo con él y créala.

---

## Paso 2 — El contrato de construcción

Copia `plantillas/_CONTRATO.md` a `mis-kits/NN-kit-nombre/_CONTRATO.md` y rellénalo:

- La promesa de una frase.
- Los cuatro ejes (qué entra · qué sale · qué hay que instalar · para quién).
- El árbol de archivos que vas a crear.
- Los nombres exactos de los archivos de salida.
- El criterio de calidad o el sistema de puntuación (se rellena en el Paso 4).
- Las reglas duras propias del kit (lo que **nunca** hará).
- **Qué queda fuera**: la lista de lo que el usuario mencionó y no va a estar. Esta
  lista evita el 90 % de las decepciones.
- El apartado **Estado**, con los nueve pasos en casillas.

Enséñale un resumen en pantalla (no el archivo entero: la promesa, qué entra, qué
sale, qué queda fuera) y **pide confirmación explícita antes de construir**. Es
mucho más barato cambiar el contrato que reescribir un kit.

Explícale de paso, en una línea, para qué sirve el contrato: es la memoria de la
construcción, permite continuar otro día y permite ampliar el kit dentro de un mes
sin volver a decidir todo.

---

## Paso 3 — Comprobar antes de escribir una línea

**El paso más importante de la skill.** Aquí se descubre si la promesa es real. Se
ejecutan de verdad las vías de datos y las dependencias que el contrato necesita.
Todo el detalle, con los comandos concretos y la lista de lo que ya se sabe que no
funciona, está en `referencias/comprobaciones.md` — lee ese archivo antes de empezar.

Cómo se hace:

1. Del contrato salen las cosas que hay que comprobar. Nunca son más de tres o
   cuatro.
2. Cada una se prueba con un comando real, y se apunta el resultado con ✓ o ✗ **en
   el contrato**, con la fecha y lo que devolvió.
3. Se comprueba con **el caso real del usuario**, no con un ejemplo cómodo. Si el
   kit va a leer la web de su gestoría, se prueba esa web, no `example.com`.

Lo que se comprueba según el eje de entrada:

| Si el kit… | Compruebas |
|---|---|
| lee páginas web | `WebFetch` sobre la URL real que dio el usuario. ¿Devuelve el contenido o una página de login/vacía? Si falla, `curl -sIL` para ver el código de respuesta |
| busca información | una `WebSearch` corta con un término suyo real |
| lee archivos del usuario | que puedes abrir ese formato de verdad: PDF, imagen, hoja de cálculo, `.docx`. Pídele uno de muestra y ábrelo |
| lee capturas de pantalla | que ves imágenes: abre una imagen cualquiera y descríbela |
| usa un programa externo | `which`/`where` del programa; si no está, prueba **la instalación completa** ahora, no en el kit del usuario |
| usa una API con clave | una llamada de prueba mínima con su clave, comprobando que responde 200 |
| mide o descarga cosas | el comando exacto (`curl -sIL`, `ffprobe`, lo que sea) sobre un caso real |

**Las tres salidas posibles**, y ninguna es "seguir como si nada":

- **✓ Funciona** → apúntalo en el contrato con el comando que lo demostró y sigue.
- **✗ No funciona, hay vía alternativa** → pruébala (protocolo de fuente bloqueada
  del `CLAUDE.md`). Muchas veces la buena es cambiar cómo entran los datos: lo que
  no se puede raspar, el usuario lo tiene en dos capturas o en un archivo que baja
  de su panel — y encima con datos privados que ningún raspador consigue.
- **✗ No funciona y no hay vía** → **se cambia el contrato**. Esa parte se cae del
  kit, se apunta en "qué queda fuera" y se lo dices al usuario en el momento, sin
  adornos: "esto no se puede leer desde aquí; el kit lo hará con las capturas que me
  des, o no lo hará".

Cuenta al usuario el resultado en dos líneas, con ✓ y ✗. Este paso es el que le da
confianza en todo lo demás, y es la diferencia entre un kit y una promesa.

> La lección que justifica este paso: en el kit de análisis de YouTube de este
> proyecto se descubrió, **probándolo**, que una página de canal no se puede leer con
> `WebFetch` (devuelve solo el pie de página). Si no se hubiera probado antes, el kit
> entero se habría construido sobre una vía de datos que no existe.

---

## Paso 4 — El criterio de calidad

Un kit sin criterio da resultados distintos cada día. Según lo que salga del kit:

### Si el kit valora, puntúa o audita algo

Lee `referencias/puntuacion.md` y define en el contrato:

- **Las dimensiones**: entre 6 y 14. Menos de 6 es superficial; más de 14 no se
  sostiene en un informe.
- **El peso de cada una**, sumando 100. El peso lo decide el impacto en lo que le
  importa al usuario, no lo fácil que sea de medir.
- **Los anclajes de cada dimensión**: qué es un 20, qué es un 50, qué es un 80. Sin
  anclajes, la nota es una opinión con forma de número.
- **Las bandas** de la nota global (crítico · flojo · aceptable · bueno · excelente).
- **La regla de oro**: el dato medido manda sobre el juicio. Y lo que no se pudo
  comprobar queda **"sin datos"**: no puntúa, no se estima, y su peso se reparte.

### Si el kit genera, transforma o ejecuta algo

Define en el contrato qué es un resultado bueno, en forma de **lista comprobable**
(no de adjetivos):

- Ejemplo malo: "el texto tiene que ser atractivo".
- Ejemplo bueno: "el titular tiene menos de 60 caracteres, dice el beneficio, no
  usa 'descubre' ni 'revoluciona', y el nombre del producto aparece en la primera
  línea".

Y define **cómo se comprueba solo**: qué mira el kit al terminar para saber que el
resultado está bien (el archivo existe, pesa más de X, tiene las 8 secciones, el
vídeo dura lo que debía, el HTML abre sin errores).

---

## Paso 5 — Construir el kit

Ahora sí se escriben archivos, en este orden y no en otro (cada uno se apoya en el
anterior). Las plantillas están en `plantillas/`, con marcadores `[[así]]` que hay
que sustituir todos, y el mapa de qué plantilla va a qué archivo está en
`plantillas/LEEME.md`. Ninguna plantilla se copia tal cual: se adapta al kit.

1. **La estructura**: las carpetas, `workspace/.gitkeep`, y `entrada/` con su
   `LEEME.md` si el usuario tiene que dejar archivos ahí.
2. **`CLAUDE.md`** — el cerebro. Lleva obligatoriamente: qué es el kit en 5 líneas,
   la detección de primer arranque y el menú de reapertura, la **tabla de decisión**
   ("lo que dice el usuario → lo que haces", mínimo las 5 filas del estándar), el
   protocolo de diagnóstico con su tabla de errores, y las reglas del kit.
3. **La skill principal** en `.claude/skills/[nombre-skill]/SKILL.md`: su `name`, su
   `description` con triggers (lee `referencias/skill-que-dispara.md` — una
   descripción floja es un kit que no arranca), y los pasos numerados, empezando por
   el **Paso 0: ¿caso real o de práctica?**.
4. **El wizard `/setup`** en `.claude/commands/setup.md`: comprueba dependencias,
   valida cada paso con ✓/✗, guarda las claves en `.env.local` si hay, escribe
   `.claude/setup-completado.json` al final y ofrece el ejemplo de práctica. Nunca
   pide al usuario que abra una terminal.
5. **`README.md`**: qué hace, qué mira, cómo puntúa o qué genera, qué hay en el kit,
   cómo se usa, **qué NO hace**, Windows, seguridad, qué cuesta usarlo.
6. **`EMPIEZA-AQUI.md`**: una pantalla, 3 pasos, la promesa arriba y una tabla de
   "si algo falla al arrancar". Lo primero que lee alguien que no estuvo aquí.
7. **`.claude/settings.json`** con los permisos justos (copia `plantillas/settings.json`
   y quita lo que ese kit no use) y **`.gitignore`**.

Reglas al escribir, que son las que separan un kit del proyecto de un kit
improvisado:

- **Español sin jerga.** Cada término técnico se traduce la primera vez ("QR: el
  código que escaneas con el móvil").
- **Los tres documentos cuentan la misma historia.** El README no puede prometer
  algo que la skill no hace. Al terminar, compruébalo.
- **Cada respuesta que el kit dé al usuario acaba en la siguiente acción concreta.**
- **Sin emojis** en los pasos; solo ✓ y ✗ en confirmaciones.
- **Nada de referencias a archivos que no existen.** Si el `CLAUDE.md` cita
  `docs/errores.md`, ese archivo se crea.
- Si el kit genera un informe HTML, lee `referencias/informe-html.md`: autocontenido,
  sin depender de internet, imprimible.

---

## Paso 6 — El ejemplo de práctica (obligatorio)

Todo kit necesita un caso ficticio con el que probarse sin datos reales, sin gastar
y sin conexión. Se guarda en `ejemplos/` y su guion está en
`referencias/ejemplo-practica.md`. Lo esencial:

- **Ficticio y verosímil**: un negocio, una persona o un documento inventados, con
  nombre, ciudad y detalles que suenen reales. Nunca datos de una persona o empresa
  de verdad.
- **Con errores plantados y contados.** Entre 10 y 16, apuntados en el contrato con
  la lista de cuáles son. Sirven para saber si el kit los encuentra.
- **Con uno o dos huecos a propósito**: un dato que no está. Uno tiene que acabar
  como "sin datos" en el resultado y el otro tiene que provocar que el kit
  **pregunte**. Así se prueba que el kit no rellena huecos inventando.
- **Offline**: si el kit lee webs, el ejemplo son archivos HTML en local; si lee
  PDFs, un PDF o un `.md` que lo imite; si mira capturas, unas descripciones o
  imágenes propias.
- **Con su `LEEME.md`** que diga qué es, que es ficticio, y cómo se usa.

Añade al `CLAUDE.md` y al `SKILL.md` del kit nuevo la fila y el paso que activan el
modo práctica ("analiza el ejemplo", "prueba con el de práctica").

---

## Paso 7 — Correr el kit contra su propio ejemplo

**Un kit que nadie ha ejecutado no está terminado.** Ahora te pones en la piel del
espectador y usas el kit recién hecho, de principio a fin, sobre su ejemplo de
práctica.

Cómo se ejecuta desde aquí:

1. La skill del kit nuevo suele quedar disponible sola al trabajar dentro de su
   carpeta. Si aparece, úsala.
2. Si no aparece, **lee su `SKILL.md` y sigue sus pasos al pie de la letra**, sin
   improvisar ni arreglar por el camino: se trata de comprobar si las instrucciones
   escritas bastan. Si tienes que adivinar algo, eso es un defecto del kit.
3. Los comandos de barra del kit nuevo no se cargan en esta ventana: para probarlos,
   lee el archivo del comando y ejecuta su contenido a mano.

Qué se comprueba:

- ¿Encuentra los errores plantados? Cuenta cuántos de los que apuntaste salen. Si
  encuentra menos de la mitad, el problema está en la skill, no en el ejemplo.
- ¿Los huecos se comportan? Uno "sin datos", el otro preguntado. Si el kit se
  inventó algo, **para y arréglalo**: es el defecto más grave que existe.
- ¿El resultado sale con el nombre y en la carpeta que dice el contrato?
- ¿Hay algún paso donde tuviste que decidir por tu cuenta porque las instrucciones
  no lo cubrían?
- Si el resultado es un HTML: ¿abre bien, sin enlaces rotos ni secciones vacías?

### Se comprueba con comandos, no a ojo

Esta parte es la que de verdad encuentra defectos, y la que apetece saltarse porque el
resultado "se ve bien". Todo lo que se pueda contar, se cuenta con un comando:

| Qué | Cómo |
|---|---|
| las secciones prometidas están y ninguna vacía | busca cada título y mide lo que hay debajo |
| la aritmética de la nota | recalcúlala **aparte**, no releas la que escribió el informe |
| marcadores de plantilla (`[[`, `TODO`, `lorem`, corchetes sin rellenar) | búsqueda de texto en el entregable |
| emojis fuera de ✓/✗, CDN, `<script>`, imágenes externas | búsqueda de texto |
| **las citas literales** | **comparación literal**: saca cada cita entrecomillada del entregable y búscala como texto exacto dentro de la fuente (el cuaderno, el archivo de entrada, el volcado). La que no aparezca se ha reescrito por el camino |

La comparación de citas es la que más defectos destapa, y ninguno se ve leyendo. En la
prueba de fuego de este kit aparecieron cuatro en el mismo entregable: una palabra caída
dentro de las comillas, las mayúsculas del original pasadas a minúscula, una negrita de
markdown metida dentro de la cita, y —la peor— una cita cortada antes de la condición que
la modificaba, que convertía un permiso en una prohibición. El entregable se leía
perfectamente bien.

De ahí salen dos reglas que **todo kit que cite fuentes tiene que llevar escritas**:

1. **La cita se copia, no se reescribe.** Viaja tal cual del sitio donde se apuntó al
   entregable: sin cambiar mayúsculas, sin perder una palabra y **sin formato dentro de
   las comillas** (una negrita dentro de una cita ya no es la cita).
2. **Nunca termina antes de la condición, la excepción o la consecuencia que la
   modifica.** Si hay que acortar, se elide el medio con `[…]` y se conservan el principio
   y el final. La prueba es de una línea: *lee la cita suelta, como si no hubieras visto la
   fuente. ¿Dice lo mismo?*

**Y cuando una comprobación falle, compruébala también.** En esa misma prueba, cuatro de
los scripts de verificación daban falso positivo (uno leía la columna equivocada, otro
fallaba porque la frase partía de línea, otro borraba el `[…]` antes de usarlo como
separador). Un "✗" que resulta ser un fallo del comprobador se arregla; no se acepta ni se
ignora. Y un "✓" que sale del primer intento merece una segunda mirada.

Cada defecto se **arregla en el kit** y se apunta en el contrato, en una lista
"defectos encontrados al ejecutar". Es normal que salgan tres o cuatro: en los kits
de este proyecto salieron entre tres y siete cada vez, y son justo los que habrían
aparecido en manos del cliente.

Al terminar, cuéntale al usuario qué salió: la nota o el resultado que dio el
ejemplo, cuántos errores plantados encontró y qué defectos corregiste. Es la prueba
de que su kit funciona.

---

## Paso 8 — La lista de calidad (QA de espectador)

Nueve puntos, del estándar (`referencias/estandar.md`). Se comprueban de verdad, uno
a uno, no de memoria:

- [ ] Alguien abre la carpeta, escribe "hola" → sale el asistente de instalación (no
      el menú de kit ya configurado).
- [ ] El asistente termina la instalación sin que el usuario abra una terminal ni
      edite código.
- [ ] El ejemplo de práctica funciona de principio a fin y el resultado aparece en
      `workspace/`.
- [ ] Cerrar y reabrir → sale el menú, no el asistente.
- [ ] Una persona sin conocimientos técnicos entiende cada mensaje (cero jerga sin
      traducir).
- [ ] `EMPIEZA-AQUI.md`, `README.md` y `CLAUDE.md` cuentan la misma historia.
- [ ] No hay referencias rotas: toda ruta o comando citado existe. Compruébalo
      listando los archivos citados.
- [ ] El kit deja claro qué cuesta usarlo (claves, suscripciones) sin sorpresas.
- [ ] Funciona igual descrito en Mac y en Windows.

Y el **estado de primer arranque**, que es el fallo más típico al entregar:

- Borra `.claude/setup-completado.json` si el Paso 7 lo creó.
- Deja `workspace/` con solo `.gitkeep`: los resultados de la prueba se borran o se
  mueven fuera.
- Deja las plantillas sin personalizar y los `.env.local` sin existir.

Marca en el contrato los puntos que fallaron y qué hiciste. Si algo no se puede
cumplir, se dice en el README del kit — no se tapa.

---

## Paso 9 — Entregar

1. **Resumen para el usuario**, en 6 líneas máximo: qué kit tiene, dónde está, qué
   entra y qué sale, qué dio la prueba, y qué queda fuera.
2. **Cómo usarlo**: en VS Code, `Archivo → Abrir carpeta…` y elegir
   `mis-kits/NN-kit-nombre/`; ahí escribir `/setup`. Dile que se abre **en otra
   ventana**: cada kit es su propio proyecto.
3. **Si va para un cliente**: ofrécele `/empaqueta` (ZIP con la receta verificada y
   comprobado descomprimiendo). Pregúntale antes si va con marca blanca.
4. **Cierra el contrato**: marca los nueve pasos, apunta la fecha y deja la lista de
   defectos corregidos. El contrato se queda en la carpeta del kit — es lo que
   permite ampliarlo dentro de tres meses. Se excluye del ZIP.
5. Y la siguiente acción concreta: "¿lo probamos con un caso real tuyo?" o "¿hacemos
   el siguiente kit?".

---

## Reglas de la skill

- **Los pasos 3 y 7 no se saltan.** Si el usuario tiene prisa, se recorta el
  **alcance** del kit (menos dimensiones, un solo entregable, un solo formato de
  entrada), nunca las comprobaciones. Un kit sin probar falla en manos del cliente,
  y ahí el fallo cuesta la relación.
- **No prometas lo que no comprobaste.** Cada línea del README del kit nuevo tiene
  detrás algo que se ejecutó de verdad en el Paso 3.
- **Escribes solo dentro de `mis-kits/`.** Nada fuera de la carpeta del kit 08.
- **Un kit, una tarea.** El que hace tres las hace regular.
- **El contrato se actualiza a cada paso**, no al final. Es lo que salva la
  construcción si se corta la sesión o se acaba el límite de uso.
- **No inventes por el usuario.** Si no sabes qué considera "bien" en su oficio,
  pregúntaselo con dos ejemplos, uno bueno y uno malo.
- **Ni claves ni contraseñas por el chat.** Si el kit necesita una clave, su wizard
  la guarda en `.env.local` y la valida con una llamada de prueba.
- **Ningún kit generado menciona modelos ni asistentes externos**: funcionan con el
  modelo que el usuario ya tiene en Claude Code.
- **Nada de datos de personas reales en los ejemplos de práctica.** Ficticios
  siempre, aunque el usuario ofrezca los de un cliente suyo.
- **No construyas kits para hacer daño**: suplantar identidades, saltarse el acceso
  a un sitio, recoger datos personales sin permiso, automatizar spam. Ofrece la
  versión legítima y sigue.
