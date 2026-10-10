# Huecos: búsquedas populares con poca o mala oferta en YouTube (7-oct-2026)

Herramienta: `herramientas/buscar_huecos.py`. Sin APIs de pago.

## Método
1. **Demanda:** recogí unas 23.000 búsquedas reales del autocompletado de Google y de YouTube en 6 mercados: España, EE. UU. en inglés, EE. UU. en español, México, Argentina y Colombia. Partí de 20 arranques por idioma ("qué pasaría si", "por qué desapareció", "why did they stop"…).
2. **Oferta:** miré en YouTube las 1.639 más fuertes (1.193 en español y 446 en inglés). De cada una saqué los 20 primeros resultados con sus vistas, duración y antigüedad.
3. **Primer filtro, automático:** descarté canciones, tráileres, tutoriales de averías y temas infantiles. Quedaron 357 posibles huecos.
4. **Revisión a mano:** comprobé los mejores resultado por resultado. **Casi todos eran falsos huecos**: la herramienta no reconocía vídeos que existen con otras palabras en el título.

**Conclusión:** las búsquedas virales sin ningún vídeo casi no existen. Lo que sí hay son búsquedas con **demanda probada** (vídeos cortos o viejos con millones de vistas) **sin un buen vídeo largo y reciente**. Ese es el hueco.

## Huecos reales confirmados

| # | Tema | Demanda probada | Oferta larga actual | Canal que encaja |
|---|---|---|---|---|
| 1 | **El hombre que grabó a un "gigante" y desapareció** (Andrew Dawson) | 2,3 M, 1,6 M y 0,8 M en vídeos de 4–9 min; Shorts de más de 1 M. Todo de hace unos 3 años | Uno de 33 min en inglés con 16.000 vistas. **Nada largo en español** | 4. El Archivo Valdés (misterio) |
| 2 | **Por qué desaparecieron los juguetes de las cajas de cereales** | 2,3 M (Short en español) y 1,26 M (3 min, inglés) en el último año | Uno de 24 min en inglés con 30.000 vistas. **Nada largo en español** | Nostalgia y empresas (o 9. El Porqué de las Máquinas) |
| 3 | **Qué pasaría si la Tierra dejara de girar** | 3,6 M y 3,0 M en vídeos de 5–8 min de hace 3–4 años | El único largo en español (47 min) es de hace 10 años | Ciencia "¿qué pasaría si…?" (tema nuevo) |
| 4 | **Qué pasaría si Júpiter no existiera** (o chocara o explotara) | 4,4 M ("si cayeras en Júpiter", 5 min) y 0,66 M (10 min); todo de hace 3–6 años | Ninguno largo y reciente | Ídem |
| 5 | **El faro de La Jument**: cómo se construyó en mitad del mar | 990.000 (7,5 min, francés traducido) y Shorts de más de 1 M | **Ninguno largo en ningún idioma** | 8. Hecho a Pulso (megaproyectos) |
| 6 | **Origen de la fiesta de los quince años** (EE. UU. hispano y México) | 4,2 M (2 min, de hace 9 años) | Uno de 24,5 min con 363.000 vistas (hace 9 meses): cubierto a medias | Cultura hispana (EE. UU. tiene RPM alto) |
| 7 | **Por qué dejaron de enseñar la letra cursiva** (EE. UU., inglés) | 1,75 M (2,4 min, de hace 11 años) | Ninguno largo y reciente | Solo en inglés |
| 8 | **El caso de Phineas Gage** (el hombre al que una barra le atravesó el cerebro) | 512.000 (12 min) y 105.000 | Ninguno largo y reciente en español | Ciencia y misterio |

## Revisados y ya cubiertos (no vale la pena)
- **Vida bajo Franco, Nueva España y judíos antes de la II Guerra Mundial:** hay vídeos largos recientes con entre 200.000 y 600.000 vistas.
- **Tutankamón, Rasputín, Zaratustra y Plutón:** hay documentales largos recientes de más de 1 M.
- **Área 51:** 2,4 M (19 min, hace 1 año).
- **Concorde:** 2,6 M (37 min, hace 1 año).
- **Acción de Gracias y penicilina:** bien cubiertos en inglés.
- **Formato "qué hacían los humanos antiguos todo el día" (en cualquier época):** saturado de clones en español.

## Límites
- El autocompletado indica que una búsqueda es popular, pero no cuánto volumen tiene. Google Trends bloquea las consultas de volumen (error 429) y sus tendencias del día son noticias sin recorrido.
- Solo se mira el top 20 de YouTube. Un hueco puede estar cubierto más abajo, pero entonces ese vídeo apenas recibe tráfico de búsqueda.

## Archivos
- `demanda.json`: todas las búsquedas con su puntuación de demanda.
- `oferta.json`: los 20 primeros resultados de YouTube de cada búsqueda revisada.
- `huecos.csv`: los 357 candidatos automáticos, sin filtrar a mano.

## Canales de referencia pequeños para "El Caso Completo" (búsqueda en 11 idiomas, 7-oct-2026)
No hay ningún canal pequeño que haga exactamente "un caso viral completo por vídeo". Los más cercanos (1.000–80.000 suscriptores):
- **Chilling Scares Compilations** (inglés, 50.800 subs): mediana de 433.000 vistas, sin cara, recopilaciones de misterios de internet de unas 2 h. Es el canal secundario de un creador grande.
- **ШЕРОН / @alexsheroon** (ruso, 57.700 subs): mediana de 100.500 vistas, vídeos de 25 min sobre casos ("El caso que sacudió Japón", 455.000).
- **Sleepy Mystery Channel** (inglés, 14.400 subs): mediana de 27.000 vistas, misterios para dormir de 2,5 h.

Descartados: Les Noticies (vlogs con cámara) y varios canales de cotilleos de famosos.
