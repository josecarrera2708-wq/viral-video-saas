---
name: [[nombre-de-la-skill]]
description: "[[Qué hace, concreto y con el entregable dentro]]. Usa esta skill cuando el usuario quiera [[situación 1]], [[situación 2]], [[situación 3]] o probar el ejemplo de práctica. Triggers: '[[frase exacta 1]]', '[[frase 2]]', '[[frase 3]]', '[[frase 4]]', '[[frase 5]]', '[[frase 6]]'."
---

# [[Nombre del especialista]]

[[2-4 líneas: qué produce esta skill, con qué entra, y dónde deja el resultado.]]

Narra en una línea lo que estás haciendo en cada fase ("[[…]]", "[[…]]"). El usuario
tiene que ver que avanzas.

---

## Paso 0 — ¿Caso real o de práctica?

- Si el usuario ha pedido el **ejemplo de práctica**: la entrada sale de
  `ejemplos/[[carpeta]]/`, avisa en una línea de que es un caso ficticio, y el resultado
  se guarda como `workspace/practica-[[…]]` para no confundirlo con un trabajo real.
- Si es un **caso real**: sigue al Paso 1.
- Si no está claro, pregúntalo en una línea.

## Paso 1 — Reunir lo que hace falta

[[Qué necesitas antes de empezar y cómo lo consigues.]]

- [[dato o archivo 1]] — [[de dónde sale; si el usuario tiene que darlo, la frase exacta
  con la que se le pide]]
- [[dato o archivo 2]] — [[…]]

**Qué hacer si algo falta**: [[preguntar / marcarlo "sin datos" / parar]]. Nunca
rellenarlo por tu cuenta.

## Paso 2 — [[La primera parte del trabajo]]

[[Instrucciones, no descripciones. Qué abres, qué buscas, qué apuntas.]]

```bash
[[el comando exacto, el que se comprobó de verdad]]
```

[[Qué se apunta y dónde. Si el trabajo es largo, aquí se va escribiendo el cuaderno
`workspace/[[caso]]-hallazgos.md` a medida que avanzas, no al final: si la sesión se
corta, no se pierde nada.]]

## Paso 3 — [[La segunda parte del trabajo]]

[[…]]

## Paso [[N]] — Producir el entregable

- **Nombre y sitio**: `workspace/[[nombre-con-fecha]]`. Siempre en `workspace/`.
- **Qué lleva dentro**, en este orden: [[las secciones]].
- [[Si es un informe HTML: autocontenido, sin depender de internet, imprimible.]]
- Ábrelo al terminar (`open` en Mac, `start` en Windows) y di la ruta en el chat.

## Paso [[N+1]] — Comprobar el entregable antes de decir "listo"

Nada se declara terminado sin esto:

- [ ] El archivo existe en `workspace/` y no está vacío.
- [ ] Están todas las secciones prometidas y **ninguna en blanco**.
- [ ] [[la comprobación propia de este kit: los pesos suman 100 / el vídeo dura lo que
      debía / el CSV tiene las columnas esperadas]]
- [ ] Lo que no se pudo comprobar aparece como **"sin datos"**, no estimado.
- [ ] No quedan marcadores de plantilla sin sustituir.

Y cierra con la siguiente acción concreta para el usuario.

---

## Reglas

- **No inventes datos.** [[Ni …, ni …]]. Lo que no se pudo comprobar se marca "sin datos".
- [[La regla dura propia de este kit]].
- Cada [[nota / afirmación / hallazgo]] va acompañada de su prueba: [[la cita literal, la
  URL, el dato medido]].
- Los resultados van siempre a `workspace/`.
- Nunca pidas al usuario que abra una terminal.
- Español sin jerga: cada término técnico se traduce la primera vez.
