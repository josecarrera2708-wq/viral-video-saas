---
description: Construye un kit nuevo a partir de lo que le cuentes, de la entrevista al ZIP
---

Vas a construir un kit de Claude Code para el usuario. Usa la skill `creador-de-kits`
y sigue sus nueve pasos en orden, sin saltarte ninguno.

Antes de empezar:

1. Mira si existe `.claude/setup-completado.json`. Si no existe, dile en una línea que
   conviene pasar primero por `/setup` (comprueba en un minuto lo que hace falta) y
   ofrécele seguir igualmente si tiene prisa.
2. Mira `mis-kits/`. Si hay algún kit con `_CONTRATO.md` sin terminar, dilo **antes de
   nada**: "tienes el kit *[nombre]* a medias, se quedó en el paso *[N]*. ¿Lo
   terminamos o empezamos otro?".

Si el usuario ha escrito el encargo junto al comando ($ARGUMENTS), úsalo como respuesta
a la primera pregunta de la entrevista y no la repitas.

Si no ha escrito nada y no sabe qué pedir, no le hagas pensar en abstracto: enséñale
`ideas-de-kits.md` y hazle una sola pregunta — ¿qué tarea repites más veces al mes y
cuánto tiempo te come cada vez?

Recuerda mientras construyes:

- Narra cada fase en una línea ("Escribiendo el contrato…", "Comprobando si esa web se
  puede leer…", "Corriendo tu kit contra su ejemplo…"). El usuario tiene que ver que
  avanzas.
- El **Paso 3** (comprobar la vía de datos antes de escribir) y el **Paso 7** (correr el
  kit contra su propio ejemplo) no se saltan. Si el usuario tiene prisa, se recorta el
  alcance del kit, nunca esos dos pasos.
- El contrato se actualiza a cada paso, no al final: es lo que salva la construcción si
  se corta la sesión.
- Escribes solo dentro de `mis-kits/`.
