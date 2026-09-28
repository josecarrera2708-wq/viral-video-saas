# Kit 06 · Empieza aquí — 5 minutos y a analizar

Este kit convierte Claude Code en un analista de marca personal: le pasas un
perfil y te dice qué entiende de esa persona alguien que llega por primera vez,
**en qué punto se le escapa la gente** y qué hacer los próximos 30 días. Usa el
modelo que ya tienes en tu Claude Code: no hay nada que configurar. 3 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code" →
   Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con suscripción
   (Pro o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo
   "siguiente") — Claude Code lo necesita para funcionar.

## Paso 2 · Abre la carpeta

- Antes de nada: si aún ves el kit dentro del ZIP, descomprímelo (en Windows: clic
  derecho sobre el ZIP → "Extraer todo") y trabaja siempre con la carpeta extraída
  — nunca desde dentro del ZIP.
- En VS Code: `Archivo → Abrir carpeta...` y elige esta carpeta del kit.
- Abre Claude Code desde el panel lateral. La primera vez te preguntará en inglés
  *"Do you trust the files in this folder?"* — elige **Yes, proceed** (es un aviso
  estándar de seguridad). Mientras trabaja también te pedirá algún permiso en
  inglés (botones "Allow" o "Yes"): es normal, acéptalos.

## Paso 3 · Escribe /setup

El asistente comprueba que todo funciona, te explica las capturas y te propone el
análisis de práctica (una nutricionista ficticia incluida en `ejemplos/`, con
errores reales metidos a propósito). Después, analizar de verdad es una frase:

```
analiza esta marca personal: [enlace de tu perfil]
```

## Lo único que tienes que saber antes de empezar

**Instagram y TikTok no se pueden leer con un enlace.** Bloquean la lectura
automática: eso le pasa a cualquier herramienta, no es un fallo de este kit.

Así que el kit trabaja con **el enlace + 5 capturas de pantalla** que haces en un
minuto desde el móvil y sueltas en la carpeta `entrada/`. Y sale ganando: una de
esas capturas es la pantalla de **Estadísticas** de tu propia aplicación, con el
alcance real, las visitas al perfil y los clics en tu enlace. Esos datos solo los
ve el dueño de la cuenta, y son justo los que revelan dónde estás perdiendo a la
gente.

El guion exacto de las cinco capturas está en **`entrada/LEEME.md`**. LinkedIn y tu
web sí se leen del enlace: de esas no necesitas nada.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Please wait" o una página vacía al leer un Instagram | Esa red bloquea la lectura automática | No es un fallo: para eso están las capturas de `entrada/` |
| "No puedo leer la imagen" | Es una foto `.heic` de iPhone | Dile a Claude que la convierta; lo hace él |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad de un análisis, al volver di "continúa el análisis donde lo dejaste" |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué mide el kit, cómo puntúa y qué cuesta usarlo.
