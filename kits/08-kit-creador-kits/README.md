# Kit 08 · Creador de kits

Le cuentas a Claude qué herramienta te gustaría tener y te la construye: un **kit de
Claude Code** completo, con su asistente de instalación, su cerebro, su ejemplo de
práctica y su carpeta de resultados. Probado delante de ti antes de dártelo, y listo
para usarlo tú o para vendérselo a un cliente.

Entra una idea en lenguaje normal → sale una carpeta en `mis-kits/` que funciona.

---

## Qué es un kit, en una línea

Una carpeta que convierte Claude Code en un especialista de **una** tarea concreta.
Dentro lleva las instrucciones de ese especialista (su *skill*), un asistente que lo
instala sin que toques una terminal, un ejemplo para probarlo sin arriesgar tus datos, y
una carpeta donde aparecen los resultados. Se abre en VS Code y se le habla.

Ejemplos de kits que puedes pedirle a este:

- Uno que revise los contratos que te manda tu gestor y marque las cláusulas de riesgo.
- Uno que audite la web de un cliente potencial y te saque la propuesta comercial.
- Uno que convierta tus notas de voz en fichas de producto para tu tienda.
- Uno que prepare tus presupuestos a partir de cuatro datos y te los deje en PDF.
- Uno que revise las facturas de tus proveedores y te avise de las subidas de precio.

---

## Cómo construye un kit: los nueve pasos

Este es el método. La forma del kit es libre —analizar, generar, transformar, dejar algo
funcionando—, pero **el proceso no se negocia**, porque es lo que separa un kit de una
carpeta con archivos bonitos.

| Paso | Qué pasa |
|---|---|
| **0** | ¿Kit nuevo o uno a medias? Si tenías uno sin terminar, lo retoma por donde iba |
| **1** | **La entrevista.** Cuatro preguntas, y de ahí sale la promesa de una frase: entra X → sale Y. Sin esa frase confirmada no se avanza |
| **2** | **El contrato.** Se escribe lo que va a hacer el kit, lo que **no** va a hacer, y los nombres de los archivos de salida. Te lo enseña y espera tu visto bueno |
| **3** | **Comprobar antes de escribir una línea.** Prueba de verdad que esa web se lee, que ese programa se instala, que ese PDF se abre. Si algo no funciona, se cambia la promesa |
| **4** | **El criterio.** Si tu kit puntúa: las dimensiones, los pesos y qué es un 20, un 50 y un 80. Si genera o ejecuta: qué es un resultado bueno y cómo lo comprueba solo |
| **5** | **Construir**: la estructura, el cerebro, la skill, el asistente de instalación y los tres documentos |
| **6** | **El ejemplo de práctica**: un caso ficticio con 10-16 errores metidos a propósito y un par de huecos, para probar el kit sin datos reales y sin conexión |
| **7** | **Correr tu kit contra ese ejemplo**, como lo haría el que lo acaba de descargar. Cada defecto que sale se arregla ahí mismo |
| **8** | **La lista de calidad**: nueve puntos, y dejar el kit en estado de recién descargado |
| **9** | **Entregar**: cómo abrirlo, y el ZIP si va para un cliente |

Los pasos **3** y **7** son los importantes, y son los dos que apetece saltarse:

- **El 3** existe por una lección concreta: en otro kit de esta colección se descubrió,
  probándolo, que la página de un canal de YouTube **no se puede leer** con las
  herramientas normales (devuelve solo el pie de página). Si no se hubiera probado
  antes, el kit entero se habría construido sobre una vía de datos que no existe. Ahora
  eso se comprueba siempre, antes de escribir nada.
- **El 7** existe porque un kit que nadie ha ejecutado no está terminado. En los kits de
  esta colección, correrlos contra su propio ejemplo destapó entre tres y siete defectos
  cada vez: exactamente los que habrían aparecido delante de un cliente.

Si tienes prisa, se recorta el **alcance** del kit (menos dimensiones, un solo
entregable). Nunca esos dos pasos.

---

## Cómo se usa

1. `/setup` — una vez, la primera. Comprueba lo que hace falta y te explica qué va a
   pasar.
2. **Pídele el kit** con tus palabras: *"quiero un kit que…"*. O `/nuevo-kit`.
3. Contesta a las cuatro preguntas y **da el visto bueno al contrato**.
4. Cuando termine, tu kit está en `mis-kits/NN-kit-nombre/`.
5. **Ábrelo en otra ventana de VS Code** (`Archivo → Abrir carpeta...`) y escribe
   `/setup` allí. Cada kit es su propio proyecto.

Comandos:

| Comando | Para qué |
|---|---|
| `/setup` | Comprobar la instalación. Una sola vez |
| `/nuevo-kit` | Construir un kit nuevo (o escribe directamente "quiero un kit que…") |
| `/revisa [carpeta]` | Pasar la lista de calidad de 9 puntos a un kit ya hecho y ver qué falla |
| `/empaqueta [carpeta]` | ZIP verificado para entregar a un cliente, con opción de marca blanca |

Y tres frases que conviene saber:

- **"continúa el kit"** — retoma una construcción cortada por donde iba.
- **"añádele X al kit que hicimos"** — amplía un kit ya hecho (y lo vuelve a probar).
- **"dame ideas"** — te enseña `ideas-de-kits.md` si no sabes qué pedir.

---

## Qué hay dentro de este kit

```
08-kit-creador-kits/
├── EMPIEZA-AQUI.md          Arrancar en 5 minutos
├── README.md                Este archivo
├── CLAUDE.md                El cerebro: cómo se comporta Claude en este kit
├── ideas-de-kits.md         8 encargos de una línea, por si no sabes qué pedir
├── plantillas/              Los esqueletos de los archivos de un kit
├── mis-kits/                Aquí aparece cada kit que construyas
└── .claude/
    ├── commands/            /setup · /nuevo-kit · /revisa · /empaqueta
    └── skills/creador-de-kits/
        ├── SKILL.md         El método de los nueve pasos
        └── referencias/     El detalle: el estándar, la entrevista, las
                             comprobaciones, el sistema de puntuación, el
                             informe HTML, el ejemplo de práctica, la skill
                             y el empaquetado
```

Y dentro de cada kit que construyas, esta anatomía (la misma de los siete kits de la
colección):

```
mis-kits/NN-kit-nombre/
├── EMPIEZA-AQUI.md   ├── README.md      ├── CLAUDE.md
├── _CONTRATO.md      ← la memoria de la construcción (no viaja en el ZIP)
├── ejemplos/         ← el caso de práctica con errores plantados
├── workspace/        ← aquí aparecen los resultados
└── .claude/          ← settings.json · commands/setup.md · skills/…/SKILL.md
```

---

## Qué NO hace este kit

Decirlo claro ahorra decepciones:

- **No construye aplicaciones ni webs.** Construye kits para Claude Code. Si lo que
  quieres es una app con usuarios y base de datos, esto no es la herramienta.
- **No hace kits que hagan de todo.** Un kit, una tarea. El que hace tres las hace
  regular. Ampliar después es fácil, porque queda el contrato.
- **No inventa tu criterio.** Si tu kit tiene que valorar algo, te va a pedir dos
  ejemplos de tu oficio, uno bueno y uno malo. Esa parte no la puede hacer nadie por ti.
- **No promete lo que no ha comprobado.** Si la vía de datos que hace falta no funciona,
  te lo dice y recorta la promesa del kit. Preferimos un kit que promete menos y cumple.
- **No escribe fuera de `mis-kits/`.** No toca otras carpetas de tu ordenador. Si le
  pides revisar un kit de fuera, la revisión es de solo lectura.
- **No construye kits para hacer daño**: suplantar a alguien, saltarse el acceso a un
  sitio, recoger datos personales sin permiso o automatizar spam. Te ofrecerá la versión
  legítima.
- **No mantiene tus kits.** Un kit es tuyo desde que sale: si cambia la web que leía o
  el programa que usaba, hay que ajustarlo (vuelve aquí y dilo).

---

## Seguridad

- **Las claves nunca por el chat.** Si un kit que construyas necesita una clave de API,
  su asistente la guardará en un archivo `.env.local` que no viaja en los ZIP, y la
  validará con una llamada de prueba. Este kit no te pide ninguna clave.
- **Los ejemplos de práctica son siempre ficticios.** Nunca se usan datos de una persona
  o una empresa real, aunque los tengas a mano: los ejemplos viajan en los ZIP y se
  enseñan en pantalla.
- **Al empaquetar se limpia todo lo tuyo**: tus claves, tus resultados de prueba, las
  rutas de tu ordenador y —si eliges marca blanca— tu nombre.
- **Los kits que construyas heredan las reglas de la colección**: no inventan datos (lo
  que no se puede comprobar se marca "sin datos"), no entran en paneles privados, no
  completan compras y no te piden abrir una terminal.

---

## Windows

Todo funciona igual. Las diferencias las gestiona Claude por ti:

- Para comprimir usa `Compress-Archive` de PowerShell en vez de `zip`.
- Para instalar programas usa `winget` en vez de `brew`.
- Necesitas **Git para Windows** instalado para que Claude Code funcione
  (git-scm.com/download/win).

Y los kits que construyas llevan las dos variantes documentadas, así que puedes
entregárselos a un cliente que use el otro sistema.

---

## Qué cuesta usarlo

**Nada aparte de tu cuenta de Claude Code.** Este kit no necesita ninguna clave de API,
ninguna suscripción y no instala nada.

Lo que sí consume es **tiempo de uso de tu plan**: construir un kit es un trabajo largo
(la entrevista, las comprobaciones, todos los documentos y la prueba final). Si te salta
el límite a la mitad, no pierdes nada: el contrato guarda el avance y "continúa el kit"
retoma por donde iba.

Los kits que construyas pueden costar dinero, y eso te lo dirá su README: si uno
necesita una clave de API, el gasto se dice con órdenes de magnitud ("unos céntimos por
informe") antes de que lo uses.

---

## Qué se puede cobrar por un kit

Rangos orientativos de mercado en 2026, para que tengas una referencia. La decisión de
precio es tuya y depende de tu mercado:

| Qué vendes | Rango |
|---|---|
| Un kit sencillo hecho a medida (una tarea, una skill) | **300 – 900 €** |
| Un kit con varias skills, o que deja algo funcionando | **1.500 – 4.000 €** |
| El mismo kit vendido muchas veces como producto | **29 – 149 €** por licencia |
| Kit incluido dentro de un servicio mensual (con soporte y mejoras) | **200 – 600 €/mes** |

Lo que mejor funciona es el último: el kit es la puerta de entrada y lo que se cobra es
el servicio que hay detrás. Y si vendes kits sueltos, pacta por escrito si incluye
soporte y cambios, y hasta cuándo: un kit con soporte ilimitado deja de ser rentable en
la segunda semana.

---

## Si algo falla

Escribe **"tengo un error"** y pega el mensaje tal cual. Claude tiene una tabla de
errores conocidos en su `CLAUDE.md` con la causa y la solución de cada uno. Si tras dos
intentos sigue atascado, pregunta en la comunidad donde conseguiste el kit pegando el
error literal.

Lo más habitual, resuelto de antemano:

- **La construcción se corta** → "continúa el kit". No se pierde nada.
- **Tu kit nuevo no responde en esta ventana** → normal: ábrelo en otra ventana de VS
  Code. Cada kit es su propio proyecto.
- **El cliente abre el ZIP y le sale un menú en vez del asistente** → el kit viajó ya
  instalado. Escribe "empaquétalo otra vez": se limpia y se vuelve a comprobar.
