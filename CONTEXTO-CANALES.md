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

## Vídeo 3 en marcha (8 oct 2026): frecuencia de entrenamiento (3, 4 o 6 días)
- Idea sugerida por la IA de YouTube Studio. Guion: guiones/frecuencia-guion-01.md (11 secciones, 99 bloques, ~17 min estimados), diseñado para retención: apuesta Mateo contra Diego, juego de verdadero o falso con respuestas repartidas, giro 2016 -> 2019 hacia el minuto 4, el error prometido a mitad del vídeo y "tu semana ideal" al final.
- Ideas de miniatura de YouTube (4) guardadas en video/frecuencia-01/marca/idea_youtube_1..4.webp. Ojo: la 4 (3 días fuerte, 6 días agotado) y el título "el grave error de entrenar 6 días" prometen algo que la evidencia no dice; la 2 (escalera con "LA VERDAD") es la más honesta.
- Siguiente: aprobar guion -> voz (gen_voz.py + revisar_voz.py) -> 40 escenas en calidad media -> montaje -> título, descripción y miniatura. Poner tarjeta al vídeo 1 cuando el guion lo nombra (sec 3) y los últimos 20 s con fondo limpio para la pantalla final.

## Voz estándar nueva (8 oct 2026, desde el vídeo 3; copiada del canal de misterio, rama claude/optimistic-franklin-15ldfx)
- Voz **Alejandro** 3a35daa1-ba81-451c-9b21-59332e9db2f3 con **sonic-3.5** (más humana, mejores acentos). Ojo: sonic-3.5 ignora `speed`; la energía se da acelerando toda la voz con `ATEMPO` (1.07 en el misterio, 1.08 en el vídeo 3). Ramon/sonic-3 quedó para los vídeos 1 y 2 y el Short A.
- Comando: `MODEL=sonic-3.5 VOICE_ID=3a35daa1-ba81-451c-9b21-59332e9db2f3 PAUSA=0.4 PAUSA_MAX=0.6 PAUSA_SECCION=0.6 ATEMPO=1.08 GUION=... OUT_DIR=... VOZ_TMP=... python3 herramientas/gen_voz.py`. Los tiempos.json ya salen reescalados por el atempo. Cambiar ATEMPO no cuesta nada (los bloques quedan en caché en VOZ_TMP).
- Acento latino solo en la voz (los subtítulos no cambian): `herramientas/pronuncia.json` ("vídeo" -> "video", "cualificado" -> "calificado", "Jasper" -> "Yásper"). Norma de escritura: frases completas con verbo, citas y palabras en minúscula (las mayúsculas se deletrean).
- Revisión: `revisar_voz.py` (whisper por bloque; ya arreglado el fallo que puntuaba mal los .orig) y `regen_bloques.py` con `MODEL=sonic-3.5 SPEEDS=1.0,0.98,1.02`. Ojo: whisper a veces "pierde" una "a" por elisión ("gana a un"); no es fallo de la voz.
- Vídeo 3: voz hecha, 16:45 (video/frecuencia-01/voz.mp3 + tiempos.json), 99 bloques revisados. Pantalla final 1920x1080 hecha con `herramientas/pantalla_final.py` (fondo con el personaje + SUSCRÍBETE + 2 huecos de vídeo + círculo de suscripción; guía rotulada aparte). Va en los últimos 20 s del vídeo 3 al montar. Siguiente: aprobar voz -> mezcla (música 441150 + efectos) -> 40 escenas en calidad media -> montaje.

## Vídeo 3: voz y música (8 oct 2026) — RECHAZADO v2, se usa la voz v1
- El usuario RECHAZÓ la voz v2 y la mezcla ("se escucha sucio, la música es tormentosa"): el cambio de tono con rubberband + EQ fuerte ensucia, y OMW/Sunday Storm/Party Sector eran música de videojuego en tono menor (OMW = La menor). No repetir.
- Decisión del usuario: usa la voz anterior (v1: Alejandro sonic-3.5, ATEMPO, sin cambio de tono ni EQ). Restaurada en video/frecuencia-01/voz.mp3 + tiempos.json (commit 975f72f). 16:45.
- ELEGIDA: la 5, Motivation To Wake Up (CC0), bajita de fondo/relleno. Audio: video/frecuencia-01/audio_final_musica.mp3 (voz v1 + música, herramientas/mezcla_fondo.py). Pendiente: visto bueno del audio -> 40 escenas.
- Candidatas que se ofrecieron:  CC0 en tono mayor (OpenGameArt): Specular City, Space Cadet Training Montage, Electronic Outlaw, Aerobics Synth Wave, Motivation To Wake Up. Esperando su elección; luego mezclar con herramientas/mezcla_gym.py (plan en video/frecuencia-01/mezcla-plan.json, hay que cambiar pistas/BPM) sin tocar la voz.
- Voces alternativas medidas (sin filtros): Diego "Hype Guy" es la más brillante y con más variación de tono; muestras enviadas, no elegidas.
- Freesound sigue bloqueado (403) en este entorno.

## Vídeo 3: escenas (8 oct 2026)
- 39 de 40 escenas generadas (gpt-image-2 medium, 1536x864) en video/frecuencia-01/escenas con `herramientas/gen_escenas_v2.py` (usa /images/edits con imagen de referencia: protagonista = marca/pantalla_final_fondo.png; Mateo y Diego = escena 01). Prompts: guiones/frecuencia-escenas-01.md (cada escena con Ref, Plano e Imagen), mapa guiones/frecuencia-mapa-escenas.json. La escena 40 es la pantalla final (marca/pantalla_final_1920x1080.png, últimos 20 s).
- FALTA la escena 7 (fábrica dentro del músculo): 502 del servidor en 4 intentos. Pedir permiso antes de reintentar.
- Montaje preparado y sin ejecutar: `herramientas/montar_video_v4.py` (2-3 planos por escena con push/pull/pan/temblor suave, fundido a negro entre secciones, viñeta, subtítulos, sin subtítulos sobre la pantalla final). Falta plano_camara.json (movimientos por escena) y la aprobación del usuario sobre las escenas. Audio: video/frecuencia-01/audio_final_musica.mp3.
- El usuario también recibió idea de vídeo 4 (quemar grasa con fuerza en casa, de YouTube Studio); la hará en otra sesión.
- Montaje del vídeo 3 HECHO (8 oct): video/frecuencia-01/frecuencia-01.mp4 (16:49, 1080p, ~110 MB, gitignored). Lección: `zoompan` de ffmpeg vibra (mueve en píxeles enteros) y el temblor simulado empeoraba; montar_video_v4.py ahora mueve con cv2.warpAffine (sub-píxel, bicúbico, con aceleración suave) y la vibración medida bajó 5-20 veces. Entrega: SendUserFile solo admite 30 MiB; el mp4 completo va por gofile (upload.gofile.io, enlace público) y hay que pedir permiso al usuario ("sube a gofile"); copia ligera 480p para ver en el chat.
