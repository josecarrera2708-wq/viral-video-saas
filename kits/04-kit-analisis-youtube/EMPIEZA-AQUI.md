# Kit 04 · Empieza aquí — 5 minutos y a analizar

Este kit convierte Claude Code en un analista de canales de YouTube. Le pasas **el
enlace de un canal y nada más**, y te devuelve un informe completo: sus miniaturas
vistas una por una, sus títulos, sus duraciones, sus descripciones, sus hashtags,
su ritmo de publicación, sus vídeos que reventaron y por qué, dónde se le cae la
gente y los próximos 10 vídeos ya escritos. 3 pasos.

## Paso 1 · Lo que necesitas instalado

1. **VS Code** — gratis, en code.visualstudio.com (instalar dándole a "siguiente").
2. La extensión **Claude Code** — en VS Code: Extensiones → busca "Claude Code" →
   Instalar. Necesitarás tu cuenta de Claude: Claude Code funciona con suscripción
   (Pro o superior) o con cuenta API de Anthropic.
3. Solo en Windows: **Git para Windows** (git-scm.com/download/win, todo
   "siguiente") — Claude Code lo necesita para funcionar.

No hace falta ninguna clave de API de YouTube, ni cuenta de Google, ni darse de
alta en nada. El kit lee lo que es público.

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

El asistente instala la única herramienta que hace falta (**yt-dlp**, el lector de
datos públicos de YouTube), comprueba que funciona de verdad y te propone el
análisis de práctica: un canal de huerto urbano ficticio, incluido en `ejemplos/`,
con 16 errores metidos a propósito. Se analiza sin internet y ves el sistema entero
en unos minutos.

Después, analizar de verdad es una frase:

```
analiza este canal: https://www.youtube.com/@elcanalquesea
```

## Lo que este kit ve y lo que no

**Del enlace sale casi todo**: los títulos, las duraciones, las visitas, los me
gusta, los comentarios, las fechas de subida, las etiquetas, los capítulos, las
descripciones completas, los hashtags, los suscriptores, los Shorts, **las
miniaturas como imágenes** (Claude las mira de verdad), la curva pública de
"momentos más vistos" y la transcripción automática para leer el gancho palabra por
palabra.

**Lo único que no está en el enlace** son los datos privados que solo ve el dueño
del canal: el CTR (cuánta gente hace clic al ver la miniatura), las impresiones, la
retención y las fuentes de tráfico. Si el canal es tuyo, con **4 capturas de
YouTube Studio** que haces en un minuto el informe pasa de bueno a demoledor,
porque la fuga se localiza con tus propios números. El guion exacto está en
**`entrada/LEEME.md`**.

Y si no las tienes —por ejemplo, porque estás analizando el canal de un
competidor— el análisis se hace igual: esas partes salen marcadas como "sin datos"
y nunca se rellenan con suposiciones.

## Si algo falla al arrancar

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| Claude Code no arranca (Windows) | Falta Git para Windows | Instálalo (git-scm.com/download/win) y reinicia VS Code |
| La extensión pide iniciar sesión | Normal la primera vez | Inicia sesión con tu cuenta de Claude (suscripción o API) |
| `yt-dlp: command not found` | La herramienta de lectura no está instalada o quedó en la carpeta `bin/` del kit | Escribe `/setup`: lo instala y lo comprueba |
| "Sign in to confirm you're not a bot" al leer el canal | La herramienta está desactualizada: YouTube cambia cosas a menudo | Dile a Claude "actualiza yt-dlp"; lo hace él en un comando |
| "Has alcanzado tu límite de uso" | Límite temporal de tu plan de Claude | Espera a que se restablezca (unas horas) o mejora el plan. Si te pasó a mitad de un análisis, al volver di "continúa el análisis donde lo dejaste" |
| El informe se abre sin las miniaturas | Moviste el HTML sin su carpeta `miniaturas-...` al lado | Vuelve a ponerlos juntos, o ábrelo con internet: tiene copia de seguridad remota |
| Nada de esto funciona | — | Pregunta en la comunidad donde conseguiste el kit, pegando el error tal cual |

¿Más detalle? `README.md` cuenta qué mide el kit, cómo puntúa y qué cuesta usarlo.
