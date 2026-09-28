# Kit 01 · Cazador de Webs — para Claude Code

> ¿Primera vez? Abre **[`EMPIEZA-AQUI.md`](EMPIEZA-AQUI.md)**: 3 pasos y a cazar.

Convierte Claude Code en una máquina de rehacer webs de negocios locales: le pasas una URL,
analiza la web entera (portada, cartas, historia, eventos), extrae el branding real del
cliente (logo, colores, fotos, precios) y la reconstruye como una **película 3D inmersiva**
— el scroll vuela a través del negocio — lista para enseñársela al cliente y vender.

Funciona con el modelo que ya tienes en tu Claude Code — no hay que configurar
ningún modelo ni ninguna API externa.

## Qué hay en el kit

| Pieza | Qué es |
|---|---|
| `EMPIEZA-AQUI.md` | Los 3 pasos para dejarlo funcionando (empieza por aquí) |
| `.claude/commands/setup.md` | El asistente `/setup`: revisa tu equipo y te propone la primera caza |
| `.claude/skills/cazador-de-webs/` | La skill: el sistema completo de caza (esto es lo que garantiza el resultado) |
| `motion-kit/` | Librería de patrones de animación que usa la skill (película 3D, reveals, contadores) |
| `ejemplos/web-de-practica/` | La web de un restaurante ficticio, para tu primera caza de práctica |
| `plantilla-propuesta.md` | La propuesta comercial que se rellena sola con cada caza |
| `despliegue.md` | Cómo publicarla: preview gratis (Netlify Drop) + publicación real (Hostinger, todo por panel) |

## Instalación (5 minutos)

1. **Descomprime el ZIP** que has descargado (en Windows: clic derecho →
   "Extraer todo" — no trabajes desde dentro del ZIP sin extraer) y mueve la
   carpeta donde quieras: p. ej. una carpeta `cazador-webs` en tu Escritorio o
   en Documentos.
2. Sigue los 3 pasos de `EMPIEZA-AQUI.md`: instalar VS Code y Claude Code →
   abrir esta carpeta → escribir `/setup`.
3. Tu primera caza, de práctica: dile a Claude **"caza la web de ejemplo"**
   (el restaurante ficticio incluido en `ejemplos/`) y mira cómo trabaja de
   principio a fin.
4. Cuando quieras cazar de verdad:

```
Caza esta web: [la URL de un negocio de tu zona]
```

La skill se activa sola. Al terminar tendrás en `cazas/[dominio]/`:
- `index.html` — la película 3D del negocio: su logo, sus fotos, su carta con
  precios reales, su historia… todo en un vuelo que se recorre con el scroll
- `assets/` — su logo y sus fotos, con las rutas ya listas para publicar
- `branding.json` — colores, tipografías y TODO el contenido extraído
- `diagnostico.md` — los 5 problemas concretos de su web actual
- `propuesta.md` — la propuesta comercial lista para enviar
- `web-lista.zip` — la web empaquetada para publicar (ver `despliegue.md`)

## Si usas Windows

- Claude Code necesita **Git para Windows** (git-scm.com/download/win): es quien
  le da a Claude la terminal que usa por dentro. Se instala dándole a
  "siguiente" hasta el final.
- Los comandos los ejecuta Claude por ti — tú no abres ninguna terminal.
- Cuando este kit muestra rutas de ejemplo, la tuya será del estilo
  `C:\Users\tu-nombre\Escritorio\cazador-webs`.

## Seguridad

- Trabaja con **webs públicas de negocios**: información que ya está en
  internet. No metas en las cazas datos privados de clientes ni información
  interna de ningún negocio.
- Anthropic no entrena sus modelos con el tráfico de API ni con tu uso de
  Claude Code.

## Si la caza se corta a mitad

Una sesión larga puede interrumpirse (la conexión, el límite de uso de tu
plan…). **No pierdes nada**: Claude Code recuerda la sesión y la skill escribe
cada entregable en cuanto lo termina.

- Abre de nuevo la conversación y di *"continúa la caza donde la dejaste"*.
- La caza retoma por el primer entregable que falte (lo ya creado no se repite
  ni se vuelve a pagar).

## Cuánto cuesta cada caza

El kit usa el modelo que ya tienes en Claude Code, así que el coste es el de tu
cuenta de Claude:

- **Con suscripción (Pro o superior)**: la caza consume el uso incluido en tu
  plan — no pagas nada aparte. Una caza completa es una sesión larga; si tu
  plan es justo, lánzala cuando no necesites Claude para otra cosa.
- **Con cuenta API**: pagas por uso. Una caza completa suele salir por unos
  pocos euros.

Se cobra desde 800 € — haz las cuentas.
