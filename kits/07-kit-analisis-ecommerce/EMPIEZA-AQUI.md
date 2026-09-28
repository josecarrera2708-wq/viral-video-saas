# Kit 07 · Empieza aquí — 5 minutos y a analizar

Este kit convierte Claude Code en un analista de tiendas online: le pasas la URL
de una tienda y te devuelve un informe con nota, las fugas por las que se le
escapan las ventas, la ficha de su producto estrella reescrita lista para pegar y
el plan para arreglarlo. Usa el modelo que ya tienes en tu Claude Code: no hay
nada que configurar. 3 pasos.

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

El asistente comprueba que puede leer tiendas, prepara el kit y te propone el
análisis de práctica (una tienda de ropa de lino ficticia incluida en
`ejemplos/`, con errores reales metidos a propósito). Después, analizar de verdad
es una frase:

```
analiza esta tienda: [URL de la tienda]
```

Claude te hará unas preguntas de contexto (qué vende, cuál es su producto
estrella, competidores) y te pedirá — **esto es opcional** — cuatro números de su
panel: visitas al mes, tasa de conversión, ticket medio y pedidos al mes. Con
esos números, cada oportunidad del informe sale con los euros al lado y la cuenta
a la vista. Sin ellos, el análisis se hace igual y se prioriza por impacto.

Al terminar tendrás en `workspace/` el informe, la ficha de producto reescrita y
el cuaderno de hallazgos. El informe se abre solo en tu navegador.

## Dos cosas que este kit no hace nunca

- **No compra nada.** Recorre el camino de compra hasta el último paso antes de
  pagar y ahí para. No mete datos de tarjeta, no completa pedidos y no crea
  cuentas en ninguna tienda.
- **No entra en el panel de nadie.** Solo lee lo que la tienda enseña
  públicamente. Los números de ventas los pones tú, si quieres.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad de un análisis, al volver di "continúa el análisis donde lo dejaste" |
| "No puedo leer el carrito de la tienda" | Los carritos se montan con JavaScript | No es un fallo: Claude te pedirá que recorras tú el checkout y le cuentes los pasos, o lo hará con un navegador si lo tienes |
| "No puedo leer su Instagram" | Las redes bloquean la lectura automática | Claude te pedirá que pegues la bio o una captura, o marcará esa parte como "sin datos" |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué mira el kit, cómo puntúa, cómo calcula los
euros sin inventar nada y qué cuesta usarlo.
