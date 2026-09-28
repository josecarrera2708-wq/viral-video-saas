# Momentos más vistos (curva pública, relativa)

*Material de práctica. En un análisis real esto sale de:*
`yt-dlp --no-warnings --print "forma=%(heatmap.::10)s | arranque=%(heatmap.:4)s" "https://www.youtube.com/watch?v=ID"`

**Esto NO es la retención.** Es la curva pública de "momentos más vistos" que YouTube
enseña en la barra del reproductor: 100 tramos normalizados, **relativos entre sí**. El
primer tramo vale siempre 1,00 porque es la referencia. Sirve para ver la forma del
vídeo, no para saber qué porcentaje se ve. Y no existe en todos los vídeos.

---

## 1 · Cómo hacer compost en casa sin que huela — `hc_compos` (18:42)

**El arranque, tramo a tramo** (cada tramo son 11 segundos):

| Tramo | Desde | Hasta | Valor |
|---|---|---|---|
| 1 | 0:00 | 0:11 | 1,00 |
| 2 | 0:11 | 0:22 | 0,71 |
| 3 | 0:22 | 0:33 | 0,63 |
| 4 | 0:33 | 0:45 | 0,58 |

**La forma, en 10 puntos repartidos por el vídeo:**

| Punto | Minuto aprox. | Valor |
|---|---|---|
| 1 | 0:00 | 1,00 |
| 2 | 2:03 | 0,52 |
| 3 | 4:07 | 0,47 |
| 4 | 6:10 | 0,44 |
| 5 | 8:14 | 0,42 |
| 6 | 10:17 | 0,40 |
| 7 | 12:21 | 0,39 |
| 8 | 14:24 | 0,41 |
| 9 | **15:10** | **0,68** |
| 10 | 18:28 | 0,35 |

---

## 2 · Por qué se te mueren los tomates en agosto — `hc_agosto` (14:20)

**El arranque** (tramos de 8,6 segundos):

| Tramo | Desde | Hasta | Valor |
|---|---|---|---|
| 1 | 0:00 | 0:09 | 1,00 |
| 2 | 0:09 | 0:17 | 0,94 |
| 3 | 0:17 | 0:26 | 0,90 |
| 4 | 0:26 | 0:34 | 0,88 |

**La forma, en 10 puntos:**

| Punto | Minuto aprox. | Valor |
|---|---|---|
| 1 | 0:00 | 1,00 |
| 2 | 1:34 | 0,86 |
| 3 | 3:09 | 0,81 |
| 4 | 4:43 | 0,79 |
| 5 | 6:18 | 0,83 |
| 6 | 7:52 | 0,77 |
| 7 | 9:27 | 0,74 |
| 8 | 11:01 | 0,72 |
| 9 | 12:36 | 0,70 |
| 10 | 14:10 | 0,61 |

---

## 3 · Tour por mi terraza en abril — `hc_tour4` (34:12)

**El arranque** (tramos de 20,5 segundos):

| Tramo | Desde | Hasta | Valor |
|---|---|---|---|
| 1 | 0:00 | 0:20 | 1,00 |
| 2 | 0:20 | 0:41 | 0,58 |
| 3 | 0:41 | 1:01 | 0,41 |
| 4 | 1:01 | 1:22 | 0,33 |

**La forma, en 10 puntos:**

| Punto | Minuto aprox. | Valor |
|---|---|---|
| 1 | 0:00 | 1,00 |
| 2 | 3:47 | 0,30 |
| 3 | 7:35 | 0,22 |
| 4 | 11:22 | 0,19 |
| 5 | 15:10 | 0,17 |
| 6 | 18:57 | 0,16 |
| 7 | 22:45 | 0,15 |
| 8 | 26:32 | 0,14 |
| 9 | 30:20 | 0,14 |
| 10 | 34:07 | 0,12 |

---

## 4 · Vlog: nos vamos con la camper a los Pirineos — `hc_camper`

```
heatmap = null
```

Este vídeo **no tiene curva pública de momentos más vistos**. Pasa con vídeos de pocas
reproducciones. No es un fallo del material: es lo que devuelve YouTube.
