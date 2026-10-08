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

#
#
 
V
Í
D
E
O
 
3
:
 
E
S
T
A
D
O
 
F
I
N
A
L
 
(
8
 
o
c
t
 
2
0
2
6
)
 
—
 
L
I
S
T
O
 
P
A
R
A
 
S
U
B
I
R
,
 
f
a
l
t
a
 
q
u
e
 
e
l
 
u
s
u
a
r
i
o
 
l
o
 
s
u
b
a


T
e
m
a
:
 
f
r
e
c
u
e
n
c
i
a
 
d
e
 
e
n
t
r
e
n
a
m
i
e
n
t
o
 
(
3
,
 
4
 
o
 
6
 
d
í
a
s
)
.
 
T
o
d
o
 
e
n
 
v
i
d
e
o
/
f
r
e
c
u
e
n
c
i
a
-
0
1
/
 
y
 
g
u
i
o
n
e
s
/
.


-
 
G
u
i
o
n
 
a
p
r
o
b
a
d
o
:
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
g
u
i
o
n
-
0
1
.
m
d
 
(
n
o
 
t
o
c
a
r
)
.
 
V
o
z
 
v
1
 
A
l
e
j
a
n
d
r
o
 
s
o
n
i
c
-
3
.
5
 
s
i
n
 
f
i
l
t
r
o
s
 
(
v
o
z
.
m
p
3
 
+
 
t
i
e
m
p
o
s
.
j
s
o
n
)
.
 
M
ú
s
i
c
a
 
e
l
e
g
i
d
a
 
p
o
r
 
e
l
 
u
s
u
a
r
i
o
:
 
"
M
o
t
i
v
a
t
i
o
n
 
T
o
 
W
a
k
e
 
U
p
"
 
(
C
C
0
,
 
O
p
e
n
G
a
m
e
A
r
t
)
,
 
b
a
j
i
t
a
 
d
e
 
f
o
n
d
o
,
 
m
e
z
c
l
a
 
c
o
n
 
h
e
r
r
a
m
i
e
n
t
a
s
/
m
e
z
c
l
a
_
f
o
n
d
o
.
p
y
 
-
>
 
a
u
d
i
o
_
f
i
n
a
l
_
m
u
s
i
c
a
.
m
p
3
.


-
 
4
0
 
e
s
c
e
n
a
s
 
(
3
9
 
c
o
n
 
g
p
t
-
i
m
a
g
e
-
2
 
m
e
d
i
u
m
 
c
o
n
 
i
m
a
g
e
n
 
d
e
 
r
e
f
e
r
e
n
c
i
a
 
+
 
l
a
 
4
0
 
=
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
)
 
c
o
n
 
h
e
r
r
a
m
i
e
n
t
a
s
/
g
e
n
_
e
s
c
e
n
a
s
_
v
2
.
p
y
;
 
p
r
o
m
p
t
s
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
e
s
c
e
n
a
s
-
0
1
.
m
d
;
 
p
l
a
n
o
 
d
e
 
c
á
m
a
r
a
 
p
o
r
 
e
s
c
e
n
a
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
p
l
a
n
o
-
c
a
m
a
r
a
.
j
s
o
n
;
 
m
a
p
a
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
m
a
p
a
-
e
s
c
e
n
a
s
.
j
s
o
n
.


-
 
M
o
n
t
a
j
e
:
 
h
e
r
r
a
m
i
e
n
t
a
s
/
m
o
n
t
a
r
_
v
i
d
e
o
_
v
4
.
p
y
 
(
m
u
e
v
e
 
l
a
 
i
m
a
g
e
n
 
c
o
n
 
c
v
2
.
w
a
r
p
A
f
f
i
n
e
 
s
u
b
-
p
í
x
e
l
 
+
 
e
a
s
i
n
g
;
 
s
i
n
 
t
e
m
b
l
o
r
;
 
v
i
ñ
e
t
a
;
 
s
u
b
t
í
t
u
l
o
s
 
s
i
n
 
t
a
p
a
r
 
l
a
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
)
.
 
S
a
l
i
d
a
:
 
v
i
d
e
o
/
f
r
e
c
u
e
n
c
i
a
-
0
1
/
f
r
e
c
u
e
n
c
i
a
-
0
1
.
m
p
4
 
(
1
6
:
4
9
,
 
1
0
8
0
p
,
 
1
1
0
 
M
B
,
 
g
i
t
i
g
n
o
r
e
d
)
.
 
E
l
 
u
s
u
a
r
i
o
 
y
a
 
l
o
 
v
i
o
:
 
"
y
a
 
n
o
 
t
i
e
m
b
l
a
"
.


-
 
P
a
n
t
a
l
l
a
 
f
i
n
a
l
 
(
ú
l
t
i
m
o
s
 
2
0
 
s
,
 
d
e
s
d
e
 
1
6
:
2
9
)
:
 
L
I
M
P
I
A
,
 
s
i
n
 
c
u
a
d
r
o
s
 
n
i
 
c
í
r
c
u
l
o
 
(
e
l
 
u
s
u
a
r
i
o
 
r
e
c
h
a
z
ó
 
l
o
s
 
h
u
e
c
o
s
 
p
i
n
t
a
d
o
s
 
p
o
r
q
u
e
 
n
o
 
c
o
i
n
c
i
d
e
n
 
c
o
n
 
l
o
s
 
e
l
e
m
e
n
t
o
s
 
d
e
 
Y
o
u
T
u
b
e
)
.
 
H
e
c
h
a
 
c
o
n
 
`
p
y
t
h
o
n
3
 
h
e
r
r
a
m
i
e
n
t
a
s
/
p
a
n
t
a
l
l
a
_
f
i
n
a
l
.
p
y
 
m
a
r
c
a
/
p
a
n
t
a
l
l
a
_
f
i
n
a
l
_
f
o
n
d
o
.
p
n
g
 
m
a
r
c
a
/
p
a
n
t
a
l
l
a
_
f
i
n
a
l
_
1
9
2
0
x
1
0
8
0
.
p
n
g
 
-
-
l
i
m
p
i
a
`
 
(
p
e
r
s
o
n
a
j
e
 
a
 
l
a
 
d
e
r
e
c
h
a
,
 
S
U
S
C
R
Í
B
E
T
E
,
 
S
I
G
U
E
 
V
I
E
N
D
O
 
a
 
l
a
 
i
z
q
u
i
e
r
d
a
)
.
 
L
o
s
 
e
l
e
m
e
n
t
o
s
 
l
o
s
 
c
o
l
o
c
a
 
e
l
 
u
s
u
a
r
i
o
 
e
n
 
S
t
u
d
i
o
.


-
 
Ú
l
t
i
m
o
 
e
n
l
a
c
e
 
g
o
f
i
l
e
 
(
p
ú
b
l
i
c
o
 
y
 
t
e
m
p
o
r
a
l
)
:
 
h
t
t
p
s
:
/
/
g
o
f
i
l
e
.
i
o
/
d
/
g
K
H
5
w
u
r
s
 
(
c
a
d
u
c
a
;
 
s
i
 
n
o
 
a
b
r
e
,
 
v
o
l
v
e
r
 
a
 
s
u
b
i
r
 
c
o
n
 
c
u
r
l
 
a
 
u
p
l
o
a
d
.
g
o
f
i
l
e
.
i
o
,
 
e
l
 
u
s
u
a
r
i
o
 
y
a
 
a
u
t
o
r
i
z
ó
 
g
o
f
i
l
e
 
p
a
r
a
 
e
s
t
e
 
v
í
d
e
o
)
.


-
 
P
a
q
u
e
t
e
 
Y
o
u
T
u
b
e
 
F
I
N
A
L
 
e
n
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
y
o
u
t
u
b
e
-
0
1
.
m
d
:
 
t
í
t
u
l
o
 
"
N
O
 
d
e
c
i
d
a
s
 
c
u
á
n
t
o
s
 
d
í
a
s
 
e
n
t
r
e
n
a
r
 
s
i
n
 
v
e
r
 
e
s
t
o
 
(
s
e
g
ú
n
 
l
a
 
c
i
e
n
c
i
a
)
"
 
(
e
l
e
g
i
d
o
 
p
o
r
 
e
l
 
u
s
u
a
r
i
o
 
t
r
a
s
 
l
a
 
i
n
v
e
s
t
i
g
a
c
i
ó
n
 
d
e
 
n
i
c
h
o
)
,
 
d
e
s
c
r
i
p
c
i
ó
n
 
c
o
r
t
a
 
d
e
 
1
.
1
2
5
 
c
a
r
a
c
t
e
r
e
s
 
(
s
i
n
 
f
u
e
n
t
e
s
 
n
i
 
n
o
t
a
 
d
e
 
I
A
 
a
 
p
e
t
i
c
i
ó
n
 
d
e
l
 
u
s
u
a
r
i
o
;
 
s
o
l
o
 
a
v
i
s
o
 
m
é
d
i
c
o
 
y
 
3
 
h
a
s
h
t
a
g
s
)
,
 
1
9
 
e
t
i
q
u
e
t
a
s
 
(
4
9
9
/
5
0
0
)
,
 
c
o
m
e
n
t
a
r
i
o
 
f
i
j
a
d
o
 
(
j
u
e
g
o
 
V
/
F
)
,
 
t
a
r
j
e
t
a
 
1
 
a
 
2
:
1
9
 
-
>
 
v
í
d
e
o
 
1
,
 
t
a
r
j
e
t
a
 
2
 
a
 
5
:
5
5
 
-
>
 
v
í
d
e
o
 
2
,
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
 
d
e
s
d
e
 
1
6
:
2
9
,
 
m
a
r
c
a
r
 
"
c
o
n
t
e
n
i
d
o
 
s
i
n
t
é
t
i
c
o
:
 
S
í
"
.
 
F
a
l
t
a
n
 
d
o
s
 
e
n
l
a
c
e
s
 
[
E
N
L
A
C
E
 
V
Í
D
E
O
 
1
/
2
]
 
e
n
 
l
a
 
d
e
s
c
r
i
p
c
i
ó
n
 
(
l
o
s
 
p
o
n
e
 
e
l
 
u
s
u
a
r
i
o
)
.


-
 
M
i
n
i
a
t
u
r
a
:
 
v
i
d
e
o
/
f
r
e
c
u
e
n
c
i
a
-
0
1
/
m
a
r
c
a
/
m
i
n
i
a
t
u
r
a
_
f
r
e
c
u
e
n
c
i
a
_
1
2
8
0
x
7
2
0
.
j
p
g
 
(
"
¿
C
U
Á
N
T
O
S
 
D
Í
A
S
 
D
E
B
O
 
E
N
T
R
E
N
A
R
?
"
,
 
e
s
c
e
n
a
 
1
8
,
 
h
e
r
r
a
m
i
e
n
t
a
s
/
m
i
n
i
_
f
r
e
c
u
e
n
c
i
a
.
p
y
)
.
 
S
e
 
e
n
v
i
ó
 
a
l
 
u
s
u
a
r
i
o
;
 
s
i
n
 
r
e
s
p
u
e
s
t
a
 
d
e
 
c
a
m
b
i
o
s
.


-
 
I
n
v
e
s
t
i
g
a
c
i
ó
n
 
d
e
 
n
i
c
h
o
 
(
d
a
t
o
s
 
r
e
a
l
e
s
,
 
6
8
 
v
í
d
e
o
s
 
e
n
 
e
s
p
a
ñ
o
l
)
:
 
g
u
i
o
n
e
s
/
f
r
e
c
u
e
n
c
i
a
-
i
n
v
e
s
t
i
g
a
c
i
o
n
-
n
i
c
h
o
.
m
d
.
 
L
o
 
q
u
e
 
d
i
s
t
i
n
g
u
e
 
a
 
l
o
s
 
m
á
s
 
v
i
s
t
o
s
:
 
"
(
s
e
g
ú
n
 
l
a
 
c
i
e
n
c
i
a
)
"
,
 
p
a
r
é
n
t
e
s
i
s
,
 
p
o
c
o
s
 
e
m
o
j
i
s
,
 
~
6
2
 
c
a
r
a
c
t
e
r
e
s
;
 
d
í
g
i
t
o
s
 
y
 
m
a
y
ú
s
c
u
l
a
s
 
n
o
 
i
m
p
o
r
t
a
n
.
 
P
r
i
m
e
r
a
 
l
í
n
e
a
 
d
e
 
d
e
s
c
r
i
p
c
i
ó
n
 
=
 
p
r
e
g
u
n
t
a
 
c
o
n
 
l
a
 
p
a
l
a
b
r
a
 
c
l
a
v
e
.
 
L
i
m
i
t
a
c
i
o
n
e
s
:
 
s
i
n
 
f
e
c
h
a
s
 
n
i
 
s
u
s
c
r
i
p
t
o
r
e
s
,
 
s
e
s
g
o
 
p
o
r
 
t
a
m
a
ñ
o
 
d
e
 
c
a
n
a
l
.
 
N
O
 
h
a
y
 
d
a
t
o
s
 
d
e
 
t
a
r
j
e
t
a
s
:
 
l
a
s
 
p
o
s
i
c
i
o
n
e
s
 
s
a
l
e
n
 
d
e
l
 
g
u
i
o
n
 
y
 
d
e
 
l
a
 
d
u
r
a
c
i
ó
n
 
m
e
d
i
a
 
d
e
l
 
c
a
n
a
l
 
(
4
:
4
8
)
.


-
 
C
o
s
t
e
s
 
a
p
r
o
x
i
m
a
d
o
s
 
d
e
 
e
s
t
a
 
s
e
s
i
ó
n
 
(
n
o
 
h
a
y
 
c
i
f
r
a
 
e
x
a
c
t
a
)
:
 
~
4
1
 
l
l
a
m
a
d
a
s
 
d
e
 
i
m
a
g
e
n
 
m
e
d
i
u
m
 
(
2
-
4
 
U
S
D
 
e
s
t
i
m
a
d
o
s
)
,
 
m
u
e
s
t
r
a
s
 
d
e
 
v
o
z
 
C
a
r
t
e
s
i
a
 
(
c
e
n
t
a
v
o
s
)
,
 
w
h
i
s
p
e
r
 
(
<
1
 
c
e
n
t
a
v
o
)
.
 
M
o
n
t
a
j
e
,
 
m
i
n
i
a
t
u
r
a
,
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
 
y
 
g
o
f
i
l
e
 
=
 
g
r
a
t
i
s
.
 
V
o
z
 
c
o
m
p
l
e
t
a
 
d
e
l
 
v
í
d
e
o
 
3
 
s
e
 
h
i
z
o
 
a
n
t
e
s
.




#
#
 
P
E
N
D
I
E
N
T
E
S


-
 
E
l
 
u
s
u
a
r
i
o
 
d
i
j
o
 
"
d
o
s
 
c
o
s
a
s
"
 
y
 
s
o
l
o
 
e
x
p
l
i
c
ó
 
l
a
 
p
r
i
m
e
r
a
 
(
l
a
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
)
.
 
P
r
e
g
u
n
t
a
r
 
c
u
á
l
 
e
r
a
 
l
a
 
s
e
g
u
n
d
a
.


-
 
E
l
 
u
s
u
a
r
i
o
 
s
u
b
e
 
e
l
 
v
í
d
e
o
 
3
 
a
 
Y
o
u
T
u
b
e
 
(
s
á
b
a
d
o
 
1
0
 
a
m
 
V
e
n
e
z
u
e
l
a
 
s
u
g
e
r
i
d
o
)
.
 
S
h
o
r
t
s
 
p
a
r
a
 
e
m
p
u
j
a
r
l
o
:
 
i
d
e
a
s
 
e
n
 
e
l
 
p
a
q
u
e
t
e
.
 
1
4
 
o
c
t
:
 
p
e
d
i
r
 
c
a
p
t
u
r
a
s
 
d
e
 
r
e
t
e
n
c
i
ó
n
,
 
t
r
á
f
i
c
o
,
 
i
m
p
r
e
s
i
o
n
e
s
 
y
 
C
T
R
 
d
e
 
l
o
s
 
v
í
d
e
o
s
 
1
,
 
2
 
y
 
3
 
(
c
o
n
 
l
a
 
r
e
t
e
n
c
i
ó
n
 
s
e
 
a
f
i
n
a
n
 
l
a
s
 
t
a
r
j
e
t
a
s
)
.


-
 
V
í
d
e
o
 
4
:
 
e
l
 
u
s
u
a
r
i
o
 
h
a
r
á
 
"
q
u
e
m
a
r
 
g
r
a
s
a
 
c
o
n
 
f
u
e
r
z
a
 
e
n
 
c
a
s
a
"
 
e
n
 
o
t
r
a
 
s
e
s
i
ó
n
 
(
i
d
e
a
 
d
e
 
Y
o
u
T
u
b
e
 
S
t
u
d
i
o
:
 
t
í
t
u
l
o
 
"
G
u
í
a
 
p
a
s
o
 
a
 
p
a
s
o
 
p
a
r
a
 
q
u
e
m
a
r
 
g
r
a
s
a
 
h
a
c
i
e
n
d
o
 
e
j
e
r
c
i
c
i
o
s
 
d
e
 
f
u
e
r
z
a
 
e
n
 
c
a
s
a
"
)
.
 
N
o
 
e
m
p
e
z
a
d
o
 
a
q
u
í
.


-
 
O
p
c
i
o
n
a
l
:
 
d
e
s
c
r
i
p
c
i
ó
n
 
y
 
b
a
n
n
e
r
 
d
e
l
 
c
a
n
a
l
;
 
p
e
d
i
r
 
e
l
 
e
n
l
a
c
e
 
d
e
 
l
o
s
 
v
í
d
e
o
s
 
1
 
y
 
2
 
p
a
r
a
 
p
o
n
e
r
l
o
s
 
e
n
 
l
a
 
d
e
s
c
r
i
p
c
i
ó
n
.




#
#
 
L
E
C
C
I
O
N
E
S
 
(
n
o
 
r
e
p
e
t
i
r
)


-
 
V
o
z
 
v
2
 
c
o
n
 
r
u
b
b
e
r
b
a
n
d
 
+
 
E
Q
 
f
u
e
r
t
e
 
s
o
n
ó
 
s
u
c
i
a
;
 
m
ú
s
i
c
a
 
d
e
 
v
i
d
e
o
j
u
e
g
o
 
e
n
 
t
o
n
o
 
m
e
n
o
r
 
s
o
n
ó
 
"
t
o
r
m
e
n
t
o
s
a
"
.
 
U
s
a
r
 
v
o
z
 
l
i
m
p
i
a
 
+
 
m
ú
s
i
c
a
 
C
C
0
 
e
n
 
t
o
n
o
 
m
a
y
o
r
 
y
 
b
a
j
i
t
a
;
 
o
f
r
e
c
e
r
 
5
 
m
u
e
s
t
r
a
s
 
a
n
t
e
s
 
d
e
 
m
e
z
c
l
a
r
.


-
 
z
o
o
m
p
a
n
 
d
e
 
f
f
m
p
e
g
 
v
i
b
r
a
 
(
p
í
x
e
l
e
s
 
e
n
t
e
r
o
s
)
:
 
u
s
a
r
 
c
v
2
.
w
a
r
p
A
f
f
i
n
e
.
 
N
u
n
c
a
 
a
ñ
a
d
i
r
 
t
e
m
b
l
o
r
 
s
i
m
u
l
a
d
o
.


-
 
L
a
 
p
a
n
t
a
l
l
a
 
f
i
n
a
l
 
d
e
 
Y
o
u
T
u
b
e
 
s
e
 
d
e
j
a
 
L
I
M
P
I
A
 
(
s
i
n
 
c
u
a
d
r
o
s
 
n
i
 
c
í
r
c
u
l
o
 
p
i
n
t
a
d
o
s
)
.


-
 
P
a
r
a
 
t
í
t
u
l
o
/
d
e
s
c
r
i
p
c
i
ó
n
,
 
i
n
v
e
s
t
i
g
a
r
 
d
a
t
o
s
 
r
e
a
l
e
s
 
d
e
l
 
n
i
c
h
o
 
(
y
t
-
d
l
p
 
b
ú
s
q
u
e
d
a
 
f
l
a
t
;
 
l
o
s
 
v
í
d
e
o
s
 
i
n
d
i
v
i
d
u
a
l
e
s
 
d
a
n
 
4
2
9
)
 
a
n
t
e
s
 
d
e
 
p
r
o
p
o
n
e
r
,
 
y
 
d
e
c
i
r
 
l
o
s
 
l
í
m
i
t
e
s
.


-
 
S
e
n
d
U
s
e
r
F
i
l
e
 
a
d
m
i
t
e
 
m
á
x
.
 
3
0
 
M
i
B
;
 
h
o
j
a
s
 
d
e
 
c
o
n
t
a
c
t
o
 
y
 
c
o
p
i
a
s
 
4
8
0
p
 
s
í
 
c
a
b
e
n
;
 
e
l
 
m
p
4
 
c
o
m
p
l
e
t
o
 
v
a
 
p
o
r
 
g
o
f
i
l
e
 
c
o
n
 
p
e
r
m
i
s
o
 
d
e
l
 
u
s
u
a
r
i
o
.
 
E
s
p
e
r
a
r
 
p
r
o
c
e
s
o
s
 
e
n
 
s
e
g
u
n
d
o
 
p
l
a
n
o
 
c
o
n
 
`
u
n
t
i
l
 
g
r
e
p
`
 
s
o
b
r
e
 
e
l
 
l
o
g
 
(
n
o
 
`
p
g
r
e
p
`
 
q
u
e
 
s
e
 
a
u
t
o
-
d
e
t
e
c
t
a
)
.
 
L
o
s
 
h
o
o
k
s
 
d
e
 
s
t
o
p
 
e
x
i
g
e
n
 
c
o
m
m
i
t
+
p
u
s
h
 
a
n
t
e
s
 
d
e
 
c
a
d
a
 
f
i
n
 
d
e
 
t
u
r
n
o
 
c
o
n
 
a
r
c
h
i
v
o
s
 
n
u
e
v
o
s
.

