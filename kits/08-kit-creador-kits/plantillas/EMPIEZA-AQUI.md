# [[Kit NN]] · Empieza aquí — 5 minutos y a [[la tarea]]

[[Qué hace este kit, en 4-5 líneas y en lenguaje de espectador: qué le das, qué te
devuelve y para qué te sirve. La primera frase es la promesa: entra X → sale Y.]] Usa el
modelo que ya tienes en tu Claude Code: no hay nada que configurar. 3 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code" →
   Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con suscripción (Pro
   o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo "siguiente") —
   Claude Code lo necesita para funcionar.
4. [[Si el kit necesita algo más, dilo aquí — y aclara que el asistente lo instala por
   ti, que no hay que hacer nada a mano.]]

## Paso 2 · Abre la carpeta

- Antes de nada: si aún ves el kit dentro del ZIP, descomprímelo (en Windows: clic
  derecho sobre el ZIP → "Extraer todo") y trabaja siempre con la carpeta extraída —
  nunca desde dentro del ZIP.
- En VS Code: `Archivo → Abrir carpeta...` y elige esta carpeta del kit.
- Abre Claude Code desde el panel lateral. La primera vez te preguntará en inglés *"Do
  you trust the files in this folder?"* — elige **Yes, proceed** (es un aviso estándar de
  seguridad). Mientras trabaja también te pedirá algún permiso en inglés (botones "Allow"
  o "Yes"): es normal, acéptalos.

## Paso 3 · Escribe /setup

El asistente [[qué comprueba e instala]] y te propone el [[ejemplo de práctica: qué es,
en media línea]]. Después, [[la tarea real]] es una frase:

```
[[la frase exacta que escribe el usuario, con el hueco entre corchetes]]
```

[[Qué te va a pedir Claude y qué es opcional. Si el usuario tiene que dejar archivos en
`entrada/`, dilo aquí con el nombre de la carpeta.]]

Al terminar tendrás en `workspace/` [[el entregable y lo que lo acompañe]].
[[Si es un HTML: se abre solo en tu navegador.]]

## [[Dos]] cosas que este kit no hace nunca

- **[[…]]** [[por qué, en una línea de tranquilidad]]
- **[[…]]** [[…]]

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad, al volver di "[[continúa …]]" |
| [[el fallo típico de la vía de datos de este kit]] | [[qué significa, sin alarmar]] | [[qué hará Claude: la vía alternativa o marcarlo "sin datos"]] |
| [[el fallo típico de su dependencia]] | [[…]] | [[…]] |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta [[qué mira el kit, cómo puntúa o qué genera, y qué
cuesta usarlo]].
