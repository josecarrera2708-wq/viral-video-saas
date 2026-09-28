# La entrevista: qué preguntar y qué dispara cada respuesta

Dos tandas cortas. El objetivo no es rellenar un formulario: es llegar a la promesa
de una frase (**entra X → sale Y**) y saber qué hay que comprobar antes de construir.

Regla de conversación: pregunta en bloque, no de una en una, y **deduce todo lo que
puedas** de lo que ya ha dicho. Si el usuario contesta a medias, sigue con lo que
tengas y pregunta lo que falte cuando haga falta de verdad.

---

## Tanda 1 — Las cuatro preguntas de siempre

1. **¿Qué tarea quieres que haga el kit?** Si la respuesta es vaga ("mejorar mi
   marketing", "organizarme"), pide el caso concreto: *cuéntame la última vez que lo
   hiciste a mano, paso a paso*. Ahí está el kit.
2. **¿Qué tienes delante cuando empiezas esa tarea?** Una web, un PDF, unas fotos,
   una hoja de cálculo, un vídeo, un correo, nada.
3. **¿Qué te gustaría tener al terminar, y en qué forma?** Un informe para enseñar a
   alguien, unos textos para pegar, unos archivos ya procesados, algo funcionando.
4. **¿El kit es para ti o para un cliente?** Y si es para un cliente: ¿lleva tu
   nombre o va en blanco (marca blanca)?

## Tanda 2 — Solo lo que no puedas deducir

- **Datos de internet** → ¿de qué páginas exactamente? **Pide una URL real**: la
  necesitas para el Paso 3.
- **Archivos suyos** → ¿qué formato, y de dónde los saca? Pide uno de muestra, aunque
  sea con los datos cambiados.
- **Hay que valorar algo** → ¿qué es "bien" y qué es "mal" en su oficio? Pide **dos
  ejemplos reales, uno bueno y uno malo**. Valen más que una hora de explicaciones y
  son los que dan los anclajes de la puntuación.
- **Hay que ejecutar algo** (convertir, redimensionar, transcribir, medir) → ¿lo ha
  hecho antes con algún programa? El nombre del programa ahorra media hora.
- **Cada cuánto lo va a usar** → una vez al mes o veinte veces al día cambia el kit:
  lo segundo pide modo por lotes y menos preguntas por caso.

---

## Los cuatro ejes

Cada respuesta de la entrevista cae en uno de estos ejes, y cada eje dispara
comprobaciones y decisiones concretas.

### Eje 1 · Qué entra

| Entrada | Qué dispara |
|---|---|
| **Web pública** | Comprobar `WebFetch` sobre la URL real. Protocolo de fuente bloqueada en el `CLAUDE.md`. Permisos: `WebFetch`, `WebSearch`, `Bash(curl:*)`. Carpeta `entrada/` no hace falta |
| **Archivos del usuario** | Carpeta `entrada/` con su `LEEME.md` (qué dejar, con qué nombre). Comprobar que ese formato se abre de verdad. El kit tiene que aguantar que la carpeta esté vacía y decirlo con cariño |
| **Capturas de pantalla** | Igual que archivos, y además el `LEEME.md` lleva **el guion de las capturas**: qué pantalla, dónde se encuentra en la app y en qué orden. Comprobar que se ven imágenes |
| **Herramienta externa** (ffmpeg, yt-dlp, pandoc…) | El wizard la instala y la comprueba. Guardar la ruta en `setup-completado.json`. Permisos concretos en `settings.json`. Tabla de errores con "no está instalado" y "está desactualizado" |
| **API con clave** | `.env.local` + `.env.example`, validación con llamada de prueba, y el README dice **qué cuesta**. La clave nunca por el chat |
| **Solo conversación** | Ni `entrada/` ni comprobaciones de datos. El peso se va al criterio de calidad: sin datos externos, lo único que garantiza el resultado es el sistema de la skill |

### Eje 2 · Qué sale

| Salida | Qué dispara |
|---|---|
| **Informe puntuado** | Sistema de puntuación completo (`puntuacion.md`) + informe HTML autocontenido (`informe-html.md`) + cuaderno incremental `workspace/[caso]-hallazgos.md` para poder continuar si se corta |
| **Textos o archivos generados** | Criterio de calidad como lista comprobable + plantilla del formato de salida + nombre de archivo fijo en el contrato |
| **Algo que queda funcionando** (bot, panel, automatización) | Wizard largo: dependencias, claves, arranque y **prueba de humo**. Documentación de errores más gorda. Es el tipo de kit más difícil: recorta el alcance antes de aceptarlo |
| **Datos estructurados** (CSV, JSON) | Definir las columnas y los tipos en el contrato, y qué pasa con los huecos (celda vacía marcada, nunca un cero inventado) |

### Eje 3 · Qué hay que instalar

| Dependencia | Qué dispara |
|---|---|
| **Nada** | Wizard corto: comprobar lo que el kit use (lectura de webs, buscador, ver imágenes) y a trabajar. Es el kit ideal: cero fricción |
| **Un binario** | Instalación con el gestor de cada sistema (`brew` en Mac, `winget` en Windows) y plan B de instalarlo dentro del kit en `bin/`. Comprobar tras instalar |
| **node + dependencias** | `package.json`, `.nvmrc`, instalación en el wizard y comprobación de que arranca. Añade mantenimiento: solo si es imprescindible |
| **Clave de API** | El README dice el coste con órdenes de magnitud, no céntimos exactos. Validación con llamada de prueba |

### Eje 4 · Para quién es

| Destino | Qué dispara |
|---|---|
| **Para él** | Tono de entrenador. El kit puede darle por sabido su contexto (su negocio, sus clientes). No hace falta ZIP |
| **Para vender el servicio** | El resultado se puede enseñar a un tercero: sin notas internas, sin tarifas dentro del informe, con firma. La tabla de decisión lleva la fila de "¿cuánto cobro?" |
| **Para entregar el kit a un cliente** | `EMPIEZA-AQUI.md` escrito para alguien que no estuvo en la construcción, marca blanca si la pidió, y `/empaqueta` al final. Nada de rutas de tu ordenador en la documentación |

---

## Señales de que hay que recortar el alcance

- El usuario enumera más de tres tareas distintas → un kit, una tarea. Elige la que
  más repite y anota el resto en "qué queda fuera".
- La promesa no cabe en una frase → todavía no está clara.
- Hace falta entrar en el panel privado de un tercero, o suplantar a alguien → no se
  construye así; se reconduce a datos públicos o a datos que él ya tiene.
- La entrada es "todo internet" → hay que cerrar la lista de fuentes.
- Tiene prisa → recorta dimensiones y entregables, **nunca** los pasos 3 y 7.
