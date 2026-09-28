# Kit 03 · Empieza aquí — 5 minutos y a auditar

Este kit convierte Claude Code en un auditor de negocios. Audita **por fuera**
(web, redes, anuncios, precios, reseñas) y **por dentro** (cómo llegan los
clientes, dónde se apuntan las citas, cuántas horas se van a mano), cruza las dos
mitades y te devuelve un informe con nota, mapas y un plan. Usa el modelo que ya
tienes en tu Claude Code: no hay nada que configurar. 3 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code"
   → Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con
   suscripción (Pro o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo
   "siguiente") — Claude Code lo necesita para funcionar, y de paso trae el Python
   con el que se dibujan los mapas.

En Mac no hace falta instalar nada más: Python ya viene puesto.

## Paso 2 · Abre la carpeta

- Antes de nada: si aún ves el kit dentro del ZIP, descomprímelo (en Windows:
  clic derecho sobre el ZIP → "Extraer todo") y trabaja siempre con la carpeta
  extraída — nunca desde dentro del ZIP.
- En VS Code: `Archivo → Abrir carpeta...` y elige esta carpeta del kit.
- Abre Claude Code desde el panel lateral. La primera vez te preguntará en
  inglés *"Do you trust the files in this folder?"* — elige **Yes, proceed**
  (es un aviso estándar de seguridad). Mientras trabaja también te pedirá algún
  permiso en inglés (botones "Allow" o "Yes"): es normal, acéptalos.

## Paso 3 · Escribe /setup

El asistente comprueba que puede leer webs, prueba el dibujante de mapas, te deja
a mano el formulario para tus clientes y te propone la **auditoría de práctica**:
una peluquería ficticia incluida en `ejemplos/`, con su web, sus redes, sus
reseñas y su formulario relleno, con errores metidos a propósito. Es la mejor
forma de ver el sistema entero antes de tocar un negocio real.

## Después: las dos formas de auditar

**Por fuera** (no necesitas nada del negocio, solo su dirección de internet):

```
audita este negocio: [URL de un negocio de tu zona]
```

Claude te hará unas preguntas de contexto (qué vende, a quién, qué objetivo tiene,
competidores) y se pondrá a investigar.

**Por dentro** (necesitas que el negocio conteste el formulario):

1. Le mandas el formulario de `formulario/` — 36 preguntas, 10 minutos, y no hace
   falta ningún dato de sus clientes. Hay dos versiones: el `.md` para pegarlo en
   un email o un WhatsApp, y el `.html` para mandarlo como archivo (se rellena en
   el navegador y trae un botón que copia las respuestas listas para devolvértelas).
2. Guardas lo que te devuelva en `entrada/`.
3. Escribes: `audita este formulario`

**Las dos a la vez es donde está el valor**: pon el formulario en `entrada/` y
lanza `audita este negocio: [URL]`. Claude cruzará lo que el negocio promete por
fuera con lo que puede cumplir por dentro, y ahí salen los hallazgos que no puede
ver nadie que mire solo una mitad.

Si tienes al cliente al teléfono, también vale: *"hazme la auditoría en modo
entrevista"* y Claude te va preguntando por bloques mientras hablas.

El informe aparece en `workspace/` y se abre solo en tu navegador.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad de una auditoría, al volver di "continúa la auditoría donde la dejaste" |
| "No puedo leer su Instagram" | Las redes bloquean la lectura automática | No es un fallo: Claude te pedirá que pegues la bio o una captura, o marcará esa parte como "sin datos" |
| "python3: command not found" | Falta Python (raro) | En Windows lo trae Git for Windows. Si no lo tienes, la auditoría se hace igual: Claude dibuja los mapas a mano |
| El formulario vuelve medio vacío | El cliente no supo algunas respuestas | Normal: lo que falta sale como "sin datos" en el informe. Claude te ofrece completarlo preguntándotelo a ti |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué mira el kit por las dos caras, cómo puntúa,
qué privacidad respeta y qué cuesta usarlo.
