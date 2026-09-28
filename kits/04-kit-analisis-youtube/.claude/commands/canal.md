---
description: Analiza un canal de YouTube completo desde su enlace y genera el informe HTML
---

Lanza un análisis de canal nuevo usando la skill `analisis-canal-youtube`.

Antes de extraer nada:

1. Si el usuario ha escrito un enlace o un `@` junto al comando, dalo por recibido y
   no lo vuelvas a preguntar. Vale cualquier forma: `youtube.com/@handle`,
   `youtube.com/c/nombre`, `youtube.com/channel/UC...` o el enlace de un vídeo suyo
   (de ahí sacas el canal).
2. Si no ha escrito nada, pídele el enlace del canal. Una sola pregunta.
3. Comprueba que existe `.claude/setup-completado.json` y lee de él la ruta de
   `yt-dlp` (campo `ytdlp`) y la firma. Si no existe, dile que escriba `/setup`
   primero: sin el lector instalado no hay datos.
4. Pregunta **en un solo mensaje** las tres cosas de contexto del Paso 1 de la skill:
   de quién es el canal (suyo, de un cliente, de un competidor), qué vende o qué
   quiere conseguir con el canal, y si tiene las capturas de YouTube Studio. Mira
   también qué hay en `entrada/`: si ya hay capturas, dilo y úsalas.
5. **No te quedes esperando las capturas.** Empieza la extracción mientras las hace
   y dile exactamente eso, para que no sienta que está bloqueando el trabajo.

Después ejecuta la skill completa: extraer el canal y la muestra de vídeos, descargar
y **mirar** las miniaturas, leer títulos, descripciones, hashtags, etiquetas,
capítulos y duraciones, calcular la mediana y los multiplicadores para encontrar los
outliers, leer los ganchos de la transcripción, mirar la curva de momentos más
vistos, puntuar las 16 dimensiones con evidencia, localizar la fuga, escribir el
packaging reescrito y los próximos 10 vídeos, generar el informe HTML en `workspace/`
y presentarlo.

Narra cada fase en una línea mientras avanzas ("Sacando el listado del canal…",
"Descargando las miniaturas…", "Leyendo el gancho del vídeo más visto…"). Un análisis
es largo: que el usuario no se quede mirando una pantalla quieta.

Si el usuario quiere probar el kit sin gastar en un caso real, dile que escriba
*"analiza el canal de ejemplo"*: el canal de huerto urbano ficticio de
`ejemplos/canal-de-practica/`, que se analiza sin internet (Paso 0 de la skill).
