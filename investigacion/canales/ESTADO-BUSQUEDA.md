# Estado de la búsqueda de canales (7-oct-2026, 12:40 en Málaga)

> **Si lees esto desde otra ventana:** la búsqueda **sigue en marcha en la sesión original**
> (https://claude.ai/code/session_01D1GgcjSTcAeDSRXDqtsNTP). No la repitas: el resultado llegará allí
> y se guardará en esta carpeta.

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

## Progreso
**Ronda 1 (terminada):** 24 nichos explorados y 71 canales verificados. **6 temas con canal válido:**

| Tema | Canal de referencia | Nota |
|---|---|---|
| Crimen y estafas | NET CREATIVE (indonesio) | 13/18 |
| Economía | 옳지경제학 / Olji Economics (coreano) | 12/18 |
| Naturaleza | Wild Testament | 11/18 |
| Historias de jubilación y vida real | 은빛시나리오 (coreano) | 13/18 |
| Cultura asiática | Inner Court | 12/18 |
| Misterios | The Eastham Foundation | 12/18 |

**Ronda 2 (en marcha):** formatos difíciles de copiar que propuso el crítico:
- Economía de la calle: por qué se hunde un sector cotidiano en España y LatAm (formato coreano).
- Las cuentas de…: empresas y dinero público explicados con cifras.
- Ciudades que el dinero levantó y hundió.
- Reintento de finanzas: mercados con datos reales explicados sobre el gráfico por un trader.
- Reintento de motor y aviación: ángulo de negocio.

**Después:** un juez final elige los 9. Primero los verificados; si faltan, los "casi válidos", con advertencia.

## Hallazgo clave: el español está saturado de clones hechos con IA
En 2026, cualquier formato sin cara que funcione en inglés tiene copias en español hechas con IA en pocas
semanas (a veces con el título traducido literalmente). Además, el doblaje automático de YouTube ya lleva
muchos originales al español. Por eso cayeron casi todos los candidatos.

Implica salir rápido, superar en calidad a los clones y tener un ángulo propio: temas hispanos, audiencia
de España o la experiencia de trader.

## Pendiente al terminar
1. Informe de los 9 canales en esta carpeta: verificados o casi válidos, reservas, advertencias y RPM estimado.
2. Pasos para crear los canales de forma segura:
   - cuentas de marca;
   - un solo AdSense en España;
   - W-8BEN (0 % de retención como residente en España);
   - autónomo e IRPF en Andalucía;
   - lanzamiento escalonado;
   - estilo propio en cada canal (para evitar el "contenido inauténtico");
   - nada de proxies.
3. Opcional: validar los finalistas con vidIQ, avisando antes del coste.

## Archivos
- `ronda1_exploracion.json`: los 24 nichos explorados (candidatos, hueco, RPM estimado e ideas).
- `verificaciones_ronda1.json`: las 71 verificaciones (si sigue válido, problemas y datos).
- `critica_ronda1.json`: propuestas para la ronda 2.
- `vidiq/outliers_en_6m.json`: datos de vidIQ.
- `workflow/`:
  - script de la búsqueda;
  - copia del journal;
  - `guardar_progreso.py`, que regenera los JSON a partir del journal.
- Herramienta: `herramientas/buscar_canales.py` (yt-dlp; subcomandos `buscar`, `canal` y `filtrar`).
