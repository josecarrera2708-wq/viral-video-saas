# Ejemplos

## `marca-de-practica/` — Iria Loureiro, nutricionista (ficticia, Santiago)

Una marca personal inventada de arriba abajo para que hagas tu primer análisis sin
usar el perfil de nadie real, sin hacer capturas y sin depender de internet.

Tiene **errores metidos a propósito**, de los que se ven todos los días: una bio
que no dice a quién ayuda, un enlace que no lleva a ninguna parte, una parrilla que
es un cajón de sastre, primeras líneas que no engancha nadie, cero pruebas de que
sea buena en lo suyo, preguntas de clientes sin responder, un perfil abandonado con
un vídeo que se vio muchísimo, y unas estadísticas que enseñan exactamente en qué
punto se le escapa la gente.

Si el análisis los encuentra y además señala **lo que ya hace bien y no debe
cambiar**, el sistema funciona.

Para lanzarlo, dile a Claude Code:

```
analiza la marca de ejemplo
```

### Qué hay dentro

| Archivo | Qué es |
|---|---|
| `perfil-instagram.md` | Su Instagram transcrito tal como se ve: el perfil, la parrilla de 12 publicaciones, una publicación abierta con sus comentarios y su mejor publicación con los números |
| `estadisticas-30-dias.md` | La pantalla de Estadísticas → Últimos 30 días: alcance, seguidores y no seguidores, visitas al perfil, clics en el enlace |
| `otras-redes.md` | Su TikTok, su LinkedIn, su web y qué sale al buscar su nombre |
| `ficha-cliente.md` | Sus respuestas a las preguntas de contexto: a quién quiere llegar, qué vende, a qué precio y qué objetivo tiene |

**El material está en archivos de texto a propósito.** En un análisis real Claude
lee tus capturas de pantalla de `entrada/`; en la práctica lee estos archivos. Lo
que no hace nunca, ni en práctica ni de verdad, es inventarse lo que no ve.

### Dos huecos, también a propósito

En el material **falta información** en dos sitios. Es intencionado: sirve para que
compruebes con tus propios ojos que el análisis **no rellena huecos con datos
plausibles**. Uno de los dos acabará marcado como *sin datos* en el informe, y por
el otro Claude te va a preguntar. Si en vez de eso te sale un número redondo salido
de la nada, algo va mal.

### Los nombres de los comentarios

En la publicación abierta hay comentarios con nombres de usuario. Son inventados y
están ahí porque un análisis real también los ve: sirven para saber si hay preguntas
sin responder y cuánto llevan así. **Ninguno de esos nombres debe aparecer en el
informe.** Es otra cosa que puedes comprobar cuando lo abras.

---

Ninguna nutricionista real se llama así, y cualquier parecido con un perfil que
conozcas es casualidad (o que estos errores son muy comunes).
