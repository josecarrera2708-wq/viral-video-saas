# Ejemplos

## `negocio-de-practica/` — Estudio Lúa (peluquería ficticia, Vigo)

Un negocio inventado de arriba abajo para que hagas tu primera auditoría sin
gastar en un caso real y sin depender de internet. Está auditado **por las dos
caras**: tienes lo que enseña al mundo y lo que su dueña cuenta de cómo funciona
por dentro. Así la práctica incluye el **cruce**, que es la parte más valiosa del
informe.

Tiene **errores metidos a propósito por los dos lados**:

- **Por fuera**: incoherencias de precios entre sus anuncios y su web, una oferta
  que anuncia en Instagram y no aparece en ningún otro sitio, horarios que no
  cuadran con su ficha de Google, redes con muchos seguidores y cero interacción,
  reseñas negativas sin responder y ningún post-venta.
- **Por dentro**: la agenda en papel, suscripciones que se pagan y no se usan, sin
  copia de seguridad, un acceso abierto para alguien que ya no trabaja allí y tres
  tareas manuales con las horas contadas.
- **Y los cruces**: el WhatsApp de sus anuncios es un móvil guardado en un cajón,
  y la reseña de una estrella que dice que nadie coge el teléfono tiene su causa
  exacta en el formulario.

Si la auditoría los encuentra todos, el sistema funciona.

Para lanzarla, dile a Claude Code:

```
audita el negocio de ejemplo
```

### Qué hay dentro

| Archivo | Qué es |
|---|---|
| `web/index.html` | Su web, tal como está publicada. Se abre en el navegador |
| `datos-publicos.md` | Lo que se ve de este negocio desde fuera: su Instagram, su TikTok, su ficha de Google con reseñas, sus anuncios activos en Meta y un competidor |
| `ficha-cliente.md` | Las respuestas que dio la dueña en la llamada previa (los dos bloques de preguntas del kit) |
| `formulario-relleno.md` | El formulario de 36 preguntas de la mitad de dentro, contestado por la dueña con sus palabras. **Dos preguntas están en blanco a propósito**: el informe tiene que marcarlas como "sin datos" |

**Todo es ficticio.** Los datos públicos están en archivos a propósito: en una
auditoría real Claude los lee de internet, y aquí los lee de aquí. El formulario
llega igual que llegaría de verdad, con el desorden y los "no lo sé" de quien lo
rellena entre clientas. Lo que nunca hace, ni en práctica ni de verdad, es
inventarse lo que falta.

Ningún negocio real se llama así, y cualquier parecido con una peluquería que
conozcas es casualidad (o que estos errores son muy comunes).
