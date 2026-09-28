---
description: Convierte un vídeo en bruto en vertical con subtítulos, cortes y efectos
---

Edita un vídeo de principio a fin con la skill `editor-vertical`.

Argumento (opcional): la ruta del vídeo, o parte de su nombre. Sin argumento, mira
qué hay en `entrada/` y en el escritorio del usuario, y si hay más de un candidato
pregunta cuál con una lista numerada.

Antes de empezar:

- Si no existe `.claude/setup-completado.json`, el kit no está instalado en este
  ordenador. Dilo en una línea y manda a `/setup`; no intentes editar.
- Comprueba que el archivo existe y es un vídeo. Si el usuario ha pegado una ruta
  con comillas o con espacios, límpiala y úsala tal cual entre comillas.

Después sigue la skill `editor-vertical` sin saltarte el paso del encuadre: es el
único donde el usuario tiene que mirar y decidir, y hacerlo mal arruina el vídeo
entero (caras cortadas). Narra cada fase en una línea ("Transcribiendo, unos 40
segundos…", "Cortando 14 silencios…") y termina abriendo el vídeo terminado.
