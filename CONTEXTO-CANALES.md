# Contexto del proyecto de canales de YouTube (leer al empezar un chat nuevo)

## Usuario y reglas
- DJ venezolano, hispanohablante. Respuestas CONCISAS en español.
- Solo vídeos largos (20–30 min). Imágenes/animación con producción simple.
- Temas para público hispano. NO guerra, NO música de terceros (solo CC0), NO canales de India.
- No gastar en APIs de pago sin necesidad: avisar el coste antes, tope de 2 reintentos por imagen, parar tras 2 fallos seguidos.
- Nunca mostrar credenciales (OpenAI, Cartesia, Freesound los inyecta el entorno).
- No modificar un guion sin que lo pida. Avisar de que los enlaces temporales son públicos y caducan.
- Antes de terminar un turno que cree archivos: commit y push.

## Canal 1: "La Ciencia de la Salud"
- Vídeo 1 (músculo): guiones/musculo-youtube-01.md (paquete viejo, aún dice "Ciencia y Músculo").
- Vídeo 2 (lagartijas, 19:17, publicado): guiones/lagartijas-youtube-01.md (título, miniatura, descripción, capítulos, etiquetas, comentario fijado).
- Pendiente: descripción del canal; revisar CTR/retención a los 2–3 días (el usuario envía capturas); pantalla final (el vídeo recomendado solo sale en público y si hay más vídeos públicos).

## Flujo de producción (estándar aprobado)
1. Guion original en guiones/*.md con secciones `## N. TÍTULO`.
2. Voz: herramientas/gen_voz.py (Cartesia sonic-3, voz Ramon, speed 1.05, PAUSA=0.6, PAUSA_MAX=0.5) -> herramientas/revisar_voz.py (whisper-1 compara con guion) -> herramientas/regen_bloques.py para arreglar bloques.
3. Audio final: herramientas/mezcla_audio.py <carpeta> <musica.mp3> <salida.mp3>. Música CC0 "A Hectic Backpacker Trip" (video/musculo-01/musica/hectic_backpacker_441150.mp3) + efectos CC0 en video/efectos/. Licencias en video/musculo-01/musica/LICENCIAS.md.
4. Escenas: ~40 por vídeo con herramientas/gen_escenas.py (gpt-image-2, 1536x864, calidad MEDIA; la alta da 502). Prompts en guiones/*-escenas-*.md + mapa json.
5. Montaje: herramientas/montar_video_v3.py <carpeta> <mapa.json> (3 tomas por escena con zoompan, xfade, subtítulos, yuv420p).
6. Miniaturas: herramientas/gen_mini*.py + texto con fuente Anton (herramientas/Anton-Regular.ttf). Sin revelar el contenido del vídeo; usar curiosidad ("LO QUE NADIE TE DICE").
7. Entrega del mp4: gofile (store1.gofile.io/uploadFile); litterbox falla; GitHub no admite mp4 >100 MB (está en .gitignore).
8b. Shorts ya montados (subtítulos quemados): `python3 herramientas/voz_short.py <short.mp4> guiones/<guion_short>.txt <salida.mp4>` pone la voz Ramon sincronizada con los subtítulos (copia el vídeo, solo cambia el audio, comprueba con whisper). `--subs` detecta cuándo cambia cada subtítulo. Ejemplo: guiones/lagartijas-short-A.txt. Los mp4 de shorts no se suben a git.
8. Subida: contenido sintético = Sí, no es para niños, hora sábado 10 am Venezuela, comentario fijado.

## Notas de mercado
- El RPM real solo lo ve el dueño del canal. Estimación historia militar en español: 1–3 USD; salud/bienestar: 2–5 USD (estimaciones, no datos).
- Canal de referencia analizado: Science Knows Health. Canal de guerra revisado (El_Archivo_del_Tiempo): descartado por tema.

## Repo
- Rama de trabajo: claude/eager-goldberg-g9gfdy, PR borrador #3.

## Estado del canal 1 (8 oct 2026, últimos 28 días, capturas de Studio)
- 258 suscriptores (sin ganancia neta en 28 días), 77 vistas, 5,3 h, 44 espectadores únicos, 1,4 mil impresiones, CTR 3,2 %, duración media 4:48. Vídeo 1 dura 10:26 (publicado 4 oct), vídeo 2 dura 19:17 (publicado 7 oct). Vídeo 2: 22 vistas en 48 h frente a 6 del vídeo 1.
- Veredicto: arranque normal, sin señal de despegue. Cuellos de botella: distribución y suscripciones. Muestra muy pequeña: no cambiar nada por estos números.
- Plan: no tocar títulos ni miniaturas hasta el 14 oct; Short A (ya con voz Ramon) + 1 Short diario con "Vídeo relacionado" al largo; marca de agua de suscripción; pedir suscripción hacia el min 2-3; 1 largo por semana con el mismo envoltorio de intriga; temas con búsqueda real. Pendiente: descripción y banner del canal.
- Reglas para juzgar (referencias habituales, no oficiales; cada vídeo a los 7 días y con 1.000 impresiones): CTR <2 % cambiar miniatura, 2-5 % normal, >5 % muy bueno; mirar la caída en los primeros 30 s de la retención.
- El 14 oct pedir al usuario capturas: retención de cada vídeo, fuentes de tráfico, impresiones y CTR por vídeo.
- vidIQ: sin canal conectado y 10 créditos; no gastarlos en análisis.
