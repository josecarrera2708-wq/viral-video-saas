# Canal "Todos Lo Vieron": contexto (7-oct-2026)

## Decisiones del usuario
- **Canal:** Todos Lo Vieron (@TodosLoVieron, libre a 7-oct-2026). Público de más de 40 años. Eslogan: "Todos lo vieron. Lo que nadie te contó."
- **Formato:** un caso viral completo por vídeo, sin cara. "Lo que nadie te contó" va en los títulos, no en el nombre.
- **Vídeo 1:** Andrew Dawson, el hombre que grabó a un "gigante" en Canadá y desapareció. Murió: tratarlo con respeto, sin morbo y sin presentar teorías como hechos.
- **Duración:** 40–45 min REALES. Unas 6.000–6.600 palabras de guion; medir el audio antes de montar.
- **Voz:** latina neutra, grave y cruda (estilo narrador de misterio). Probar voces de Cartesia en español (Andres, Alonso, Rodrigo, Mateo… y clonadas o de la biblioteca si hace falta) con una muestra corta antes de generar todo.
- **Imagen:**
  - opción A: imágenes fijas con movimiento de cámara y paralaje (ffmpeg);
  - el usuario pidió además el precio de clips cortos animados con IA (pendiente de que decida).
- **Material real SOLO sin copyright:** dominio público (Wikimedia Commons, archivos de gobiernos y organismos de EE. UU. y Canadá, NASA…) o Creative Commons con uso comercial; capturas breves de titulares como cita. **Nada** de telediarios, fotos de prensa ni el TikTok original: se recrea con IA. A Dawson nunca se le representa de forma fotorrealista (siluetas o ilustración).
- **Pendiente de investigar:** el caso completo con fuentes; canales de misterio que funcionan (estilo de animación, tipografía, miniaturas, ritmo, música CC0); guion largo; plan de escenas.
- **Reglas:** avisar del coste antes de usar APIs de pago; máximo 2 reintentos por imagen; parar tras 2 fallos seguidos; música solo CC0; commit y push al terminar cada turno que cree archivos.

## Guion del vídeo 1 (7-oct-2026)
- `guiones/dawson-guion-01.md`: 23 secciones y 7.283 palabras. Da unos 40,5 min a 180 palabras/min y unos 44 min a 165.
- Las fuentes están en `guiones/dawson-fuentes-01.md`.
- Estilo: documental de televisión. Intro de 40 s, apertura con lugar y fecha, narración en presente, 5 actos con un adelanto al final de cada uno y 6 zonas de retención.
- **Corrección del caso:** los vídeos fueron ficción, según el propio Andrew (6-may) y su pareja (21-oct-2022). Murió el 1-jul-2022 y su pareja contó que llevaba tiempo luchando contra la depresión. No se dan más detalles sobre su muerte. Al final del vídeo aparece la línea de ayuda 024 (España) y las de otros países van en la descripción.
- **Lección de La Ciencia de la Salud:** 3.471 palabras dieron 19:17 min (unas 180 palabras/min con speed 1.05). Hay que medir la voz real antes de montar.
- Siguiente paso: muestras de voz latina grave de unos 20 s cada una, avisando antes del coste.

## Guion v2 y voz (7-oct-2026)
- `guiones/dawson-guion-01.md` v2: conversacional, hablando de "tú", frases completas y vocabulario latino ("video", "celular", "auto"). Tiene 24 secciones y 8.245 palabras, unos 44 min a 187 palabras/min.
- Secciones nuevas: 16, "La foto que alguien robó" (Lillooet, 1894), y la visita del investigador a la autopista (en la 18).
- Voz elegida: **Alejandro** 3a35daa1-ba81-451c-9b21-59332e9db2f3, velocidad 1.0. El usuario la quiere fluida y no demasiado grave.
- Descartadas: Manuel, Jorge, Andrés, Agustín, Damon, Carl, Darius y Alejandro con el tono bajado.
- Muestras de la intro: sonic-3 (189 palabras/min) y sonic-3.5 (178 palabras/min). Falta elegir el modelo.
- Norma de escritura para TTS: nada de frases sueltas sin verbo ("Una montaña. Un edificio."), porque suenan robóticas.

## Decisiones oficiales (7-oct-2026)
- **Lema oficial: "Todos Lo Vieron: la historia real detrás del misterio."** Sustituye a "lo que nadie te contó" como eslogan; esa frase solo puede aparecer suelta dentro de la narración.
- **Voz oficial del canal: Alejandro** (3a35daa1-ba81-451c-9b21-59332e9db2f3) con **sonic-3.5**. Generación: speed 1.0, PAUSA 0.55, PAUSA_MAX 0.6 y PAUSA_SECCION 0.6.
  Comando: `MODEL=sonic-3.5 VOICE_ID=... GUION=... OUT_DIR=... VOZ_TMP=... python3 herramientas/gen_voz.py`.
  Para regenerar bloques: `regen_bloques.py` con `MODEL=sonic-3.5 SPEEDS=1.0,0.98,1.02`.
- Guion v3: la intro no desvela el final y va seguida de su vida (Campbell River y el valle). Son 8.526 palabras, unos 46 min, y el usuario aprobó esa duración.
- Herramientas de voz copiadas de La Ciencia de la Salud a `herramientas/`. Añaden `MODEL`, `PAUSA_SECCION` y generación en paralelo.

## Voz final del vídeo 1 (7-oct-2026)
- `video/dawson-01/voz-final.mp3` dura 46:25. Se generó con Alejandro y sonic-3.5 (PAUSA 0.4, PAUSA_SECCION 0.6) y después se aceleró con atempo 1.07. Tiempos en `tiempos-final.json`.
- Whisper: se corrigieron las mayúsculas, que se deletreaban (en el guion las citas van siempre en minúscula), y "Jasper", que sonaba "Hásper" (va a `herramientas/pronuncia.json` como "Yásper").
- Cierre nuevo: "suscríbete a este canal, porque aquí vas a conocer las verdaderas historias detrás de los grandes misterios del mundo".
- **Norma de mezcla:** la música sigue 3–4 s después de la última palabra con un fundido de salida. No se corta de golpe.
