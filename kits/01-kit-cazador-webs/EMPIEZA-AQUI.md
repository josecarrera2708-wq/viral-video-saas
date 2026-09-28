# Kit 01 · Empieza aquí — 5 minutos y a cazar

Este kit convierte Claude Code en tu cazador de webs, usando el modelo que ya
tienes en tu Claude Code. No hay nada que configurar: 3 pasos y a cazar.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code"
   → Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con
   suscripción (Pro o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo
   "siguiente") — Claude Code lo necesita para funcionar.

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

El asistente comprueba tu equipo, prepara el kit y te propone la primera caza
de práctica (un restaurante ficticio incluido en `ejemplos/`). Después, cazar
de verdad es una frase:

```
caza esta web: [URL de un negocio de tu zona]
```

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad de una caza, al volver di "continúa la caza donde la dejaste" |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué hace el kit y qué cuesta usarlo.
