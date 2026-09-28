# Kit 08 · Empieza aquí — 5 minutos y a construir

Este kit convierte Claude Code en un constructor de kits: le cuentas con tus palabras
qué herramienta te gustaría tener y te la construye entera —su asistente de
instalación, su cerebro, su ejemplo de práctica y su carpeta de resultados—, la prueba
delante de ti y te la deja lista para usar o para vendérsela a un cliente. Usa el
modelo que ya tienes en tu Claude Code: no hay nada que configurar. 3 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code" →
   Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con suscripción (Pro
   o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo "siguiente") —
   Claude Code lo necesita para funcionar.

## Paso 2 · Abre la carpeta

- Antes de nada: si aún ves el kit dentro del ZIP, descomprímelo (en Windows: clic
  derecho sobre el ZIP → "Extraer todo") y trabaja siempre con la carpeta extraída —
  nunca desde dentro del ZIP.
- En VS Code: `Archivo → Abrir carpeta...` y elige esta carpeta del kit.
- Abre Claude Code desde el panel lateral. La primera vez te preguntará en inglés *"Do
  you trust the files in this folder?"* — elige **Yes, proceed** (es un aviso estándar
  de seguridad). Mientras trabaja también te pedirá algún permiso en inglés (botones
  "Allow" o "Yes"): es normal, acéptalos.

## Paso 3 · Escribe /setup

El asistente comprueba en un minuto que todo funciona y te explica qué va a pasar.
Después, pedir un kit es una frase. Por ejemplo:

```
quiero un kit que revise los contratos que me manda mi gestor y me diga qué
cláusulas son un problema
```

No hace falta que sepas nada técnico ni que lo tengas claro del todo: Claude te hará
cuatro preguntas, te enseñará **la promesa de tu kit en una frase** (entra esto → sale
esto) y no construirá nada hasta que le des el visto bueno. Si no sabes qué pedir, di
"dame ideas" y verás `ideas-de-kits.md`.

Construir un kit tarda un rato largo, no dos minutos. Si se corta la sesión o se agota
tu límite de uso, no se pierde nada: vuelve y escribe **"continúa el kit"**.

## Cuando tu kit esté listo

Aparecerá en la carpeta `mis-kits/`. Y ojo con esto, que es lo único que despista:

**tu kit se usa abriéndolo en otra ventana de VS Code** (`Archivo → Abrir carpeta...` →
eliges la carpeta de tu kit → escribes `/setup`). Cada kit es su propio proyecto. En
esta ventana se construyen kits; en la del kit se trabaja con él.

Si vas a dárselo a un cliente, escribe **"empaquétalo"** y tendrás un ZIP comprobado,
sin tus datos dentro si lo quieres con marca blanca.

## Dos cosas que este kit hace siempre, y que son la diferencia

- **Comprueba antes de prometer.** Antes de escribir una línea de tu kit, prueba de
  verdad que lo que promete se puede hacer (que esa web se puede leer, que ese programa
  se puede instalar, que ese PDF se puede abrir). Si no se puede, te lo dice y se
  cambia la promesa. Nunca te construye un kit encima de una suposición.
- **Prueba tu kit antes de dártelo.** Le hace un caso de práctica con errores metidos a
  propósito, ejecuta tu kit contra él y arregla lo que salga. Es normal que salgan tres
  o cuatro defectos: para eso está el paso, y por eso tu kit no falla el día que lo
  usas con un cliente delante.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Al volver, escribe "continúa el kit": el contrato de construcción guarda por dónde iba |
| La construcción se corta a la mitad | Nada se ha perdido | Escribe "continúa el kit" y retoma por el paso que faltaba |
| Tu kit nuevo no responde en esta ventana | Cada kit es su propio proyecto | Ábrelo en otra ventana de VS Code (`Archivo → Abrir carpeta...`) y escribe `/setup` allí |
| "Esa web no se puede leer" al construir | Comprobación honesta, no un fallo | Claude te propondrá otra vía (normalmente unas capturas o un archivo que descargas tú) o recortará la promesa del kit. Es mejor saberlo ahora que delante de un cliente |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta cómo se construye un kit paso a paso, qué **no** hace
este kit, y qué se puede cobrar por un kit hecho a medida.
