# El estándar de un kit

Lo que todo kit tiene que cumplir para poder usarse o entregarse. Está destilado de
siete kits construidos y probados: cada regla está aquí porque su ausencia rompió
algo alguna vez.

---

## Estructura obligatoria

```
NN-kit-nombre/
├── EMPIEZA-AQUI.md            ← Lo primero que se lee. Máximo 1 pantalla, 3 pasos
├── README.md                  ← Documentación completa
├── CLAUDE.md                  ← El cerebro: primer arranque, tabla de decisión, reglas
├── .gitignore
├── .claude/
│   ├── settings.json          ← Permisos pre-aprobados (solo los que use el kit)
│   ├── commands/
│   │   └── setup.md           ← El asistente de instalación (/setup)
│   └── skills/
│       └── <skill-principal>/
│           └── SKILL.md       ← El sistema que garantiza el resultado
├── ejemplos/                  ← El caso de práctica ficticio (obligatorio)
├── entrada/                   ← Solo si el usuario deja archivos ahí (con LEEME.md)
└── workspace/                 ← Aquí van SIEMPRE los resultados (con .gitkeep)
```

Un kit puede añadir lo que necesite (`docs/`, `scripts/`, `src/`, `plantillas/`,
`assets/`), y puede ser tan pequeño como CLAUDE.md + skill + workspace. Pero
**nunca** sin `EMPIEZA-AQUI.md`, `README.md`, `CLAUDE.md`, wizard y ejemplo de
práctica.

Comandos extra: uno por acción principal (`/analiza`, `/editar`, `/informe`…). Los
comandos son finos: presentan y delegan en la skill, no repiten sus pasos.

---

## El patrón del asistente de instalación (`/setup`)

Así se comporta todo kit al abrirse con Claude Code:

1. **Detección de primer arranque.** El `CLAUDE.md` define un marcador inequívoco:
   normalmente que no exista `.claude/setup-completado.json`. Si no existe → modo
   asistente. Si existe → modo menú.
2. **Bienvenida de 6 líneas como máximo**: qué es el kit, qué va a pasar en los
   próximos minutos y **una sola acción** a realizar.
3. **Comprobación de dependencias.** Claude comprueba e instala lo que falte. Nunca
   se le pide al usuario que abra una terminal si Claude puede ejecutarlo por él.
4. **Claves y datos sensibles.** Las claves de API nunca se pegan en el chat: van a
   `.env.local` o al archivo de configuración, y se validan con una llamada de prueba.
5. **Validar antes de decir "listo".** Después de cada paso crítico, una comprobación
   mínima con ✓ o ✗. Ningún paso se declara completado sin comprobarlo.
6. **Primer uso guiado.** El asistente termina ofreciendo el ejemplo de práctica, para
   que el usuario vea un resultado en los primeros minutos.
7. **Reapertura.** Si el kit ya está configurado, el saludo es un menú corto de
   acciones posibles ("¿Qué quieres hacer hoy?"), no el asistente otra vez.

---

## Las reglas absolutas (no negociables)

- **Cross-platform.** Funciona en Mac y en Windows. Nada de comandos solo de un
  sistema cuando hay alternativa; rutas relativas o construidas con `path.join()`.
- **El usuario no toca la terminal.** Claude ejecuta, el usuario conversa y confirma.
- **Secretos nunca por chat.** Siempre a archivos de entorno o configuración.
- **Validar antes de "listo".** Sin excepciones.
- **No inventar datos.** Ni teléfonos, ni reseñas, ni métricas, ni precios. Solo lo
  real; si falta un dato, se pregunta o se marca **"sin datos"**.
- **Resultados siempre a `workspace/`** (o a la carpeta fija que defina el kit).
  Nunca sueltos en la raíz.
- **Español neutro y sin jerga.** Cada término técnico se traduce la primera vez.
  Sin emojis en los pasos; solo ✓ y ✗ en confirmaciones.
- **Cada respuesta termina con la siguiente acción concreta.**
- **Si algo falla**: no repetir el comando; pedir el error literal, consultar la tabla
  de errores del kit y, si es nuevo, añadirlo a esa tabla.
- **Atascado más de 2 intentos** → sugerir la comunidad donde consiguió el kit.
- **Ningún modelo ni asistente externo.** El kit funciona con el modelo que el usuario
  ya tiene en Claude Code.

---

## La tabla de decisión mínima del `CLAUDE.md`

Toda tabla "lo que dice el usuario → lo que haces" cubre como mínimo:

| Lo que dice el usuario | Acción |
|---|---|
| "Empieza", "hola", "qué hago" | Asistente o menú, según primer arranque |
| La frase natural de la tarea estrella | Ejecutar la skill principal |
| "Algo no funciona", "tengo un error" | Protocolo de diagnóstico del kit |
| "¿Cómo funciona esto por dentro?" | Explicación en cristiano desde el README |
| "¿Cuánto cobro por esto?" | Rangos orientativos de mercado, decisión suya |

Y las filas propias del kit: el modo práctica, continuar un trabajo cortado,
profundizar en una parte, y los límites ("esto no lo hace este kit").

---

## La lista de calidad (QA de espectador)

Se prueba simulando ser quien acaba de descargar el kit:

- [ ] Abrir la carpeta, escribir "hola" → aparece el asistente correcto.
- [ ] El asistente completa la instalación sin abrir una terminal ni editar código.
- [ ] El ejemplo de práctica funciona de principio a fin y el resultado aparece en
      `workspace/`.
- [ ] Cerrar y reabrir → aparece el menú, no el asistente.
- [ ] Una persona sin conocimientos técnicos entiende cada mensaje.
- [ ] `EMPIEZA-AQUI.md`, `README.md` y `CLAUDE.md` cuentan la misma historia.
- [ ] No hay referencias rotas (archivos citados que no existen, comandos que no
      están).
- [ ] El kit deja claro qué cuesta usarlo (claves, suscripciones) sin sorpresas.
- [ ] Funciona igual descrito en Mac y en Windows.

---

## Los tres errores que más veces han roto un kit

1. **Prometer una vía de datos sin comprobarla.** El kit se construye entero y en la
   primera prueba real resulta que esa página no se puede leer. Solución: el Paso 3.
2. **Entregar el kit ya instalado.** El usuario descomprime, escribe "hola" y le sale
   el menú de kit configurado en vez del asistente, porque viajó el
   `setup-completado.json` o los resultados de las pruebas. Solución: el estado de
   primer arranque limpio del Paso 8.
3. **Documentos que se contradicen.** El README promete algo que la skill no hace, o
   cita una carpeta que se renombró. Solución: revisar los tres documentos juntos al
   final, y comprobar que toda ruta citada existe.
