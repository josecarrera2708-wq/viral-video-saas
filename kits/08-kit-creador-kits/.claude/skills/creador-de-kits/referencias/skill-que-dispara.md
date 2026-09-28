# La skill: que se active y que garantice el resultado

La skill es el cerebro del kit. Y tiene un problema propio: **si su descripción es
floja, no se activa nunca**. El usuario escribe lo que quiere, Claude contesta de
memoria en vez de seguir el sistema, y el resultado es mediocre sin que nadie sepa por
qué. El kit parece funcionar y no está funcionando.

Este archivo trata las dos mitades: la cabecera (que se dispare) y el cuerpo (que
garantice el resultado).

---

## Dónde vive

```
.claude/skills/<nombre-de-la-skill>/SKILL.md
```

Una carpeta por skill, y dentro el `SKILL.md`. Si la skill necesita material de apoyo
—tablas largas, plantillas, listas de comprobación— va en una subcarpeta
`referencias/` al lado, y el `SKILL.md` la cita por su ruta. Eso mantiene el `SKILL.md`
legible y permite que lo largo se lea solo cuando hace falta.

Nombre de la skill: en minúsculas y con guiones, describiendo **la tarea**, no el
producto: `analisis-ecommerce`, `auditoria-negocio`, `creador-de-kits`. No
`mi-skill-1` ni `skill-principal`.

---

## La cabecera

```markdown
---
name: nombre-de-la-skill
description: "Qué hace, con qué entra y qué produce. Usa esta skill cuando […]. Triggers: 'frase 1', 'frase 2', 'frase 3'."
---
```

Solo dos campos, y el que decide si el kit funciona es el segundo.

### Las tres partes de una buena descripción

1. **Qué hace**, concreto y con el entregable dentro. No "analiza webs", sino "analiza
   la web de un negocio local y produce un informe HTML puntuado de 0 a 100 con las 3
   acciones prioritarias".
2. **Cuándo usarla**: "Usa esta skill cuando el usuario quiera…", enumerando las
   situaciones. Esta parte es la que hace el trabajo de decidir.
3. **Los triggers**: las frases **exactas que diría el usuario**, entre comillas. En sus
   palabras, no en las tuyas.

### Cómo se sacan los triggers

De la entrevista, literalmente. Cuando el usuario describió lo que quería, usó unas
palabras concretas: **esas** son los triggers. Añade además:

- la forma corta ("analiza esta web"),
- la forma con archivo ("mira este PDF"),
- la forma de duda ("¿esto está bien?"),
- la forma de práctica ("prueba con el ejemplo"),
- y la forma de continuar ("sigue con lo de ayer").

Entre 6 y 12 triggers. Menos se queda corto; más es ruido.

### Comparación

Descripción que no se dispara:

> `description: "Analiza negocios."`

Descripción que se dispara:

> `description: "Audita un negocio local a partir de su web y sus reseñas públicas y
> produce un informe HTML con nota de 0 a 100 por 9 dimensiones, las pruebas de cada
> nota y las 3 acciones prioritarias. Usa esta skill cuando el usuario quiera saber
> qué falla en un negocio, preparar una propuesta comercial para un cliente potencial,
> comparar dos competidores o probar el ejemplo de práctica. Triggers: 'analiza este
> negocio', 'audita esta web', 'qué le falla a', 'quiero una propuesta para', 'mira
> este cliente', 'compara estos dos', 'analiza el ejemplo'."`

Regla práctica: **la descripción larga no molesta y la corta cuesta el kit**. Si dudas,
alarga.

---

## El cuerpo: pasos numerados

El cuerpo es el sistema. No es una explicación de lo que hace el kit: son
**instrucciones para ejecutarlo**, en orden, que otra persona (u otra sesión) pueda
seguir sin haber estado presente.

Esqueleto que funciona:

```
# [Nombre del especialista]

[2-4 líneas: qué produce esta skill y dónde lo deja.]

## Paso 0 — ¿Caso real o de práctica?
## Paso 1 — Reunir lo que hace falta
## Paso 2 — [El trabajo, partido en los pasos que sean]
## Paso N — Producir el entregable
## Paso N+1 — Comprobar el entregable antes de decir "listo"
## Reglas
```

Y las reglas de escritura, que son las que separan una skill que funciona de una que
suena bien:

- **Un paso, una acción comprobable.** Si un paso dice "analiza el negocio", no es un
  paso: es el kit entero.
- **Instrucciones, no descripciones.** "Abre cada archivo de `entrada/` y apunta X",
  no "el kit tiene en cuenta los archivos del usuario".
- **Los comandos exactos**, con sus rutas, en bloques de código. Los que se
  comprobaron en el Paso 3, no los que parecen razonables.
- **Qué hacer cuando algo falta.** Cada paso que depende de un dato dice qué pasa si
  ese dato no está: preguntar, o marcarlo "sin datos". Nunca rellenar.
- **Dónde va cada cosa**: nombre de archivo y carpeta, escritos.
- **Cómo se cuenta al usuario.** Una línea por fase, en cristiano, y la siguiente
  acción concreta al final.
- **El último paso siempre comprueba el resultado.** Existe, está completo, cuadra.
- **Sin emojis** en los pasos; ✓ y ✗ en confirmaciones.

Longitud razonable: de 150 a 400 líneas. Por debajo de 100 suele faltar el sistema
—será una skill que "explica" en vez de hacer—; por encima de 600, parte lo largo a
`referencias/`.

---

## Varias skills en un kit

Solo cuando son **tareas distintas de verdad**, no fases de la misma. Analizar y
generar el informe son la misma skill; analizar un negocio y editar sus vídeos, no.

Si hay dos o más:

- Descripciones que **no se solapen**. Dos skills que podrían activarse con la misma
  frase acaban activando la que no toca.
- Numera las carpetas por orden de uso (`01-analisis/`, `02-informe/`) si el orden
  importa.
- Y el `CLAUDE.md` dice en su tabla de decisión **cuál se usa con cada frase**. Es el
  árbitro.

---

## Comandos de barra: finos

Un comando (`.claude/commands/analiza.md`) es un atajo, no un duplicado de la skill:
presenta, pide lo que falte y **delega en la skill**. Si el comando repite los pasos,
al primer cambio los dos documentos se contradicen y el kit empieza a hacer cosas
distintas según cómo se le llame.

Uno por acción principal, con nombre de verbo: `/analiza`, `/informe`, `/empaqueta`.

---

## Cómo se comprueba que la skill dispara

En el Paso 7, sin trampas: escribe **una de las frases que diría el usuario** —no el
nombre de la skill— y mira si se activa.

- Si se activa, ✓.
- Si no, la descripción es floja: añade los triggers que falten con las palabras del
  usuario y vuelve a probar.
- Y ojo con el falso positivo: si se activa porque tú acabas de escribirla y la tienes
  fresca, no cuenta. La prueba de verdad la hace el usuario en su ventana, con su
  frase. Por eso los triggers salen de la entrevista.
