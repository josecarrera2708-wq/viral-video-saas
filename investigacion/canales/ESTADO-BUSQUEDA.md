# Estado de la búsqueda de canales (terminada el 7-oct-2026)

> La búsqueda ya terminó. No hace falta repetirla.

## Usuario
- DJ venezolano y trader con experiencia. Vive en **Málaga** y cobrará los canales **desde España**
  (AdSense de España, transferencia SEPA). Hora peninsular (UTC+2 hasta el 25-oct-2026).
- Ya tiene "La Ciencia de la Salud" (contexto en `CONTEXTO-CANALES.md`, rama `claude/eager-goldberg-g9gfdy`).
  Quiere **9 canales nuevos** en español, uno por tema, sin salud.
- Respuestas concisas en español. Avisar del coste antes de usar APIs de pago. Nunca mostrar credenciales.
  No tocar un guion sin que lo pida. Música solo CC0. Commit y push antes de terminar un turno que cree archivos.

## Filtros de la búsqueda
1. Canal de referencia con 1.000–80.000 suscriptores.
2. Outliers de los últimos 6 meses (desde 2026-04-06) con 3x o más la mediana. Las vistas deben venir de la demanda, no de la audiencia.
3. Vídeos de 25–40 min (se aceptan 20–45).
4. Hueco en español.
5. Fácil de replicar sin cara: guion IA, voz Cartesia, imágenes gpt-image realistas y montaje ffmpeg.
6. Sin copyright: nada de clips de cine, TV, noticias o deportes, música comercial ni contenido reutilizado. Guerra permitida. Fuera India/Pakistán, contenido infantil y música.
7. RPM alto (siempre como estimación).
8. 9 temas distintos, sin salud.
9. Referencias en muchos idiomas.
10. Miniaturas y guiones se analizan después, solo de los finalistas.

## Resultado (búsqueda terminada el 7-oct-2026)
29 temas explorados en 2 rondas y 86 verificaciones. Informe completo en `INFORME-9-CANALES.md` y guía de creación en `PASOS-CREAR-CANALES.md`.

| # | Canal sugerido | Referencia | Estado |
|---|---|---|---|
| 1 | Expediente Ponzi (estafas financieras) | NET CREATIVE (indonesio) | verificado |
| 2 | Años de Plata (jubilación y dinero, +50) | 은빛시나리오 (coreano) | verificado |
| 3 | Madres Salvajes (naturaleza) | Wild Testament | verificado |
| 4 | El Archivo Valdés (misterio y ovnis, ficción) | The Eastham Foundation | verificado |
| 5 | La Razón del Colapso (geopolítica económica) | 옳지경제학 / Olji Economics (coreano) | verificado |
| 6 | La Corte de Jade (cortes imperiales de Asia) | Inner Court | verificado |
| 7 | Tus Ahorros Perdidos (crisis y ahorros) | Moss Garner (alemán) | casi válido |
| 8 | Hecho a Pulso (megaproyectos) | Brasil Construído (portugués) | casi válido |
| 9 | El Porqué de las Máquinas (tecnología) | ゆっくり情報科学ちゃんねる (japonés) | casi válido |

## Hallazgo clave: el español está saturado de clones hechos con IA
En 2026, cualquier formato sin cara que funcione en inglés tiene copias en español hechas con IA en pocas
semanas (a veces con el título traducido literalmente). Además, el doblaje automático de YouTube ya lleva
muchos originales al español. Por eso cayeron casi todos los candidatos.

Implica salir rápido, superar en calidad a los clones y tener un ángulo propio: temas hispanos, audiencia
de España o la experiencia de trader.

## Siguiente paso
Lanzar primero los canales 1, 2 y 7 (ver `PASOS-CREAR-CANALES.md`). Opcional: validar los finalistas con vidIQ, avisando antes del coste.

## Archivos
- `INFORME-9-CANALES.md` y `juez_final.json`: la selección final.
- `PASOS-CREAR-CANALES.md`: cómo crear los canales de forma segura.
- `ronda1_exploracion.json` y `ronda2_exploracion.json`: los 29 temas explorados.
- `verificaciones_ronda1.json` y `verificaciones_ronda2.json`: las 86 verificaciones.
- `critica_ronda1.json`: propuestas para la ronda 2.
- `vidiq/outliers_en_6m.json`: datos de vidIQ.
- `workflow/`:
  - script de la búsqueda;
  - copia del journal;
  - `guardar_progreso.py`, que regenera los JSON a partir del journal.
- Herramienta: `herramientas/buscar_canales.py` (yt-dlp; subcomandos `buscar`, `canal` y `filtrar`).
