export const meta = {
  name: 'canales-referencia',
  description: 'Busca canales de referencia (1k-80k subs, outliers 6 meses, 25-40 min, hueco en español) en ~24 nichos y varios idiomas, verifica y elige 9',
  phases: [
    { title: 'Explorar', detail: 'un agente por nicho, búsquedas multi-idioma con yt-dlp' },
    { title: 'Verificar', detail: 'verificación adversarial de los mejores candidatos' },
    { title: 'Huecos', detail: 'crítico de completitud: nichos no explorados' },
    { title: 'Elegir', detail: 'selección final de 9 canales de 9 temas' },
  ],
}

const HOY = '2026-10-06'
const TOOL = 'python3 /home/user/viral-video-saas/herramientas/buscar_canales.py'
const SCRATCH = '/tmp/claude-0/-home-user-viral-video-saas/4fc25ed8-7367-56d4-8e53-4682774195e3/scratchpad'

const CONTEXTO = `
CONTEXTO: Hoy es ${HOY}. Un creador hispanohablante (DJ venezolano con experiencia en trading) quiere abrir 9 canales de YouTube nuevos en ESPAÑOL, cada uno de un tema distinto (ya tiene uno de salud/ejercicio, que NO cuenta). Busca CANALES DE REFERENCIA en otros idiomas (inglés, alemán, francés, portugués, italiano, polaco, turco, japonés, coreano, ruso, etc.) cuyo formato pueda traer al español donde nadie lo hace. Objetivo: vídeos virales de muchos millones de vistas y RPM alto.

FILTROS OBLIGATORIOS del canal de referencia (método de un experto en automatización de YouTube):
1. Suscriptores entre 1.000 y 80.000.
2. Outliers recientes: vídeos de los ÚLTIMOS 6 MESES (desde 2026-04-06) con >=3x la mediana de vistas del canal. Las visitas deben venir de la DEMANDA del mercado, no de la audiencia: muchos vídeos con más vistas que suscriptores.
3. Vídeos largos: ideal 25-40 min (aceptable 20-45).
4. Hueco en español: nadie en YouTube en español hace ese mismo formato+tema (o lo hacen mal/poco).
5. Fácil de replicar con nuestra fábrica: guion con IA + locución IA (Cartesia, español) + imágenes generadas con gpt-image (pueden ser realistas, incluso personas, pero NO personajes idénticos en 40 escenas) + montaje ffmpeg con zoom/transiciones/subtítulos. NO tenemos cara de presentador, ni metraje de stock propio, ni grabación real. Formatos de mapas, gráficos, ilustraciones, escenas históricas, objetos, paisajes = muy replicables.
6. Copyright: DESCARTA canales que dependen de clips de películas/series/TV/noticias/deportes, música comercial, metraje ajeno o "reused content". Temas: todos permitidos (guerra incluida). EXCLUYE canales en hindi/urdu/de India/Pakistán, contenido infantil, música, compilaciones.
7. RPM alto: audiencia con poder adquisitivo (finanzas, negocios, tecnología, historia, etc.). Da rangos de RPM en español como ESTIMACIÓN, nunca como dato.

HERRAMIENTA (gratis, yt-dlp, ya instalada). Ejecútala con Bash:
- ${TOOL} filtrar "<consulta>" --n 40 --periodo anio --hilos 2   -> busca vídeos >20 min del último año ordenados por vistas, saca estadísticas de cada canal y aplica los filtros. Devuelve "pasan" y "descartados".
  Variantes útiles: --periodo mes (último mes, encuentra canales nuevos), --orden relevancia, --max-subs 300000 (para ver canales que crecieron rápido).
- ${TOOL} buscar "<consulta>" --n 40 [--periodo anio|mes|any] [--orden vistas|relevancia]   -> solo la lista de vídeos.
- ${TOOL} canal <channel_id|@handle|url>   -> estadísticas completas del canal (caché compartida).
- Miniaturas para ver el estilo visual: curl -s -o ${SCRATCH}/thumbs/<id>.jpg https://i.ytimg.com/vi/<id>/hqdefault.jpg  y luego ábrela con la herramienta Read (ves la imagen). Crea la carpeta thumbs si no existe.
- Puedes usar WebSearch para ideas de consultas, RPM por nicho o canales mencionados en foros, pero los NÚMEROS deben salir de la herramienta.
CORTESÍA CON YOUTUBE: no lances más de un comando de la herramienta a la vez (nada de & ni bucles paralelos), --hilos 2 como máximo. Si ves errores 429 o "Sign in to confirm", espera 60 s y reintenta menos agresivo.
NO uses vidIQ (no hay créditos). No escribas archivos en el repo salvo la caché que genera la herramienta.

TÉCNICA DE BÚSQUEDA: las búsquedas por vistas devuelven sobre todo canales gigantes; para encontrar canales pequeños con outliers, usa consultas ESPECÍFICAS (títulos tipo outlier: "why X...", "the dark truth about...", "how X really..."), en VARIOS IDIOMAS escritas en ese idioma, combina --periodo anio y --periodo mes, y --orden relevancia. Haz como mínimo 14 consultas cubriendo al menos 5 idiomas. Cuando un canal pequeño encaje, mira sus outliers y sus títulos para sacar más consultas (bola de nieve).
Responde todo en español.
`

const NICHOS = [
  { id: 'finanzas', nombre: 'Finanzas, trading e inversión (VENTAJA del usuario: sabe trading, sistemas de inversión, interés compuesto, bots y wallets)', semillas: 'historia de cracks y burbujas, grandes traders y sus estrategias, fraudes financieros, interés compuesto, cómo piensan los inversores, mercados explicados con historia; inglés: "stock market crash explained", "the trader who", "how the richest investors"; alemán: "Börsencrash Geschichte"; francés: "krach boursier histoire"; portugués: "crash da bolsa história"' },
  { id: 'economia', nombre: 'Economía mundial y geopolítica económica', semillas: 'por qué un país quebró, inflación, monedas, deuda, comercio mundial, petróleo, cómo China/Japón/Alemania se hicieron ricos; "why X economy collapsed", "how X became rich", "Wirtschaft erklärt", "économie pourquoi"' },
  { id: 'empresas', nombre: 'Historias de empresas y negocios (auge y caída, fraudes corporativos, marcas)', semillas: '"the rise and fall of", "how X destroyed itself", "the company that", "Aufstieg und Fall", "l\'histoire de la marque", "a história da empresa"' },
  { id: 'ricos', nombre: 'Riqueza, multimillonarios, dinero antiguo (old money), lujo y cómo viven los ricos', semillas: '"how billionaires", "old money families", "the richest family", "inside the life of", "les plus riches familles", "die reichsten Familien"' },
  { id: 'tecnologia', nombre: 'Tecnología, IA e inventos (cómo funciona, futuro, inventos que cambiaron el mundo)', semillas: '"how X actually works", "the invention that", "AI explained documentary", "the future of", "wie funktioniert", "comment fonctionne"' },
  { id: 'historia_antigua', nombre: 'Historia antigua, civilizaciones perdidas y tecnologías antiguas', semillas: '"ancient civilization", "lost technology", "what archaeologists found", "Antike Zivilisation", "civilisation perdue", "civilização antiga"' },
  { id: 'militar', nombre: 'Historia militar y guerras (batallas, armas, estrategia, unidades)', semillas: '"the battle that", "the deadliest", "why X army", "WW2 documentary", "Schlacht Dokumentation", "bataille histoire", "historia militar"' },
  { id: 'religion', nombre: 'Religión, Biblia, mitología e historias sagradas', semillas: '"bible stories documentary", "the untold story of", "what the bible says", "mythology explained", "Mythologie", "mythologie grecque", "histórias da bíblia"' },
  { id: 'ciencia_espacio', nombre: 'Ciencia y espacio (universo, física, planetas)', semillas: '"what if", "the universe", "black hole", "space documentary", "Weltraum Doku", "l\'univers documentaire"' },
  { id: 'psicologia', nombre: 'Psicología, filosofía y estoicismo', semillas: '"psychology of", "dark psychology", "stoicism", "why people", "Psychologie", "philosophie", "psicologia"' },
  { id: 'crimen', nombre: 'Crimen real, estafas famosas y casos judiciales', semillas: '"the scam that", "biggest heist", "the con man who", "true crime documentary", "Betrug", "arnaque", "golpe"' },
  { id: 'misterios', nombre: 'Misterios sin resolver, paranormal, conspiraciones y OVNIs', semillas: '"unsolved mystery", "the mystery of", "unexplained", "Mysterium", "mystère non résolu", "mistério"' },
  { id: 'geografia', nombre: 'Geografía, países, ciudades y curiosidades del mundo', semillas: '"why X country", "the most isolated", "why nobody lives", "geography explained", "Geographie", "pourquoi ce pays"' },
  { id: 'desastres', nombre: 'Desastres, accidentes, ingeniería fallida (aviones, barcos, puentes)', semillas: '"the disaster that", "what went wrong", "plane crash documentary", "engineering failure", "Katastrophe Doku", "catastrophe"' },
  { id: 'megaproyectos', nombre: 'Megaproyectos, arquitectura, ingeniería y cómo se construye/fabrica', semillas: '"megaproject", "how they built", "how it\'s made", "the most expensive", "Megaprojekt", "mégaprojet"' },
  { id: 'biografias', nombre: 'Biografías y personajes históricos (cuidado con rostros reales)', semillas: '"the life of", "the man who", "the untold story", "Leben von", "la vie de", "a vida de"' },
  { id: 'naturaleza', nombre: 'Naturaleza, animales, océanos y supervivencia', semillas: '"deep ocean", "deadliest animals", "how animals survive", "Tiere Doku", "animaux", "survival"' },
  { id: 'historias_vida', nombre: 'Historias narradas de vida real para público mayor (jubilación, 50+, lecciones de vida, historias de familia)', semillas: '"I lost everything at 60", "retirement story", "life lessons from", "stories for seniors", "Rentner Geschichte", "histoire de retraite"' },
  { id: 'vida_cotidiana', nombre: 'Historia de la vida cotidiana ("cómo era vivir en...", edad media, oficios antiguos) e historia para dormir', semillas: '"what life was like", "medieval life", "a day in the life of a", "history for sleep", "Leben im Mittelalter", "la vie au moyen âge"' },
  { id: 'motor_aviacion', nombre: 'Coches, motor, aviación y transporte (historia y curiosidades)', semillas: '"the car that", "why X failed car", "aviation history", "the fastest", "Autogeschichte", "histoire de l\'automobile"' },
  { id: 'lore_ficcion', nombre: 'Lore de sagas/videojuegos y ficción narrada (ojo copyright)', semillas: '"full lore", "the complete story of", "lore explained", "Lore erklärt", "histoire complète"' },
  { id: 'relatos_ia', nombre: 'Relatos y películas generadas con IA (fantasía, historias épicas, cuentos largos para adultos)', semillas: '"AI movie full", "fantasy story full", "epic story", "full fantasy film AI", "KI Film", "histoire fantastique"' },
  { id: 'cultura_asia', nombre: 'Japón, China, Corea y cultura asiática (historia, sociedad, curiosidades)', semillas: '"why Japan", "inside China", "the dark side of Japan", "Japan Doku", "pourquoi le Japon"' },
  { id: 'derecho_sociedad', nombre: 'Sociedad, leyes, sistemas (cómo funciona la cárcel, el dinero, el poder, la política sin partidismo)', semillas: '"how prisons work", "the system", "why X is illegal", "how the world really works", "comment fonctionne le système"' },
]

const CAND = {
  type: 'object',
  properties: {
    canal: { type: 'string' }, url: { type: 'string' }, idioma: { type: 'string' },
    suscriptores: { type: 'integer' }, mediana_vistas: { type: 'integer' },
    ratio_mediana_subs: { type: 'number' }, pct_videos_vistas_mayor_que_subs: { type: 'integer' },
    duracion_mediana_min: { type: 'number' }, pct_videos_25_45_min: { type: 'integer' },
    outliers: { type: 'array', items: { type: 'object', properties: { titulo: { type: 'string' }, vistas: { type: 'integer' }, fecha: { type: 'string' }, duracion_min: { type: 'number' } }, required: ['titulo', 'vistas'] } },
    formato_visual: { type: 'string' },
    replicable: { type: 'string', enum: ['alta', 'media', 'baja'] },
    riesgo_copyright: { type: 'string', enum: ['bajo', 'medio', 'alto'] },
    notas: { type: 'string' },
  },
  required: ['canal', 'url', 'idioma', 'suscriptores', 'mediana_vistas', 'outliers', 'formato_visual', 'replicable', 'riesgo_copyright'],
}

const NICHO_SCHEMA = {
  type: 'object',
  properties: {
    nicho: { type: 'string' },
    consultas_realizadas: { type: 'array', items: { type: 'string' } },
    idiomas_cubiertos: { type: 'array', items: { type: 'string' } },
    candidatos: { type: 'array', items: CAND, description: 'máx 5, el mejor primero; solo canales que cumplen 1k-80k y tienen outliers recientes' },
    cerca_del_limite: { type: 'array', items: { type: 'object', properties: { canal: { type: 'string' }, url: { type: 'string' }, suscriptores: { type: 'integer' }, motivo: { type: 'string' } }, required: ['canal', 'suscriptores', 'motivo'] }, description: 'canales que validan la demanda pero fallan un filtro (p.ej. 80k-300k crecidos en meses)' },
    hueco_espanol: {
      type: 'object',
      properties: {
        consultas_es: { type: 'array', items: { type: 'string' } },
        competidores: { type: 'array', items: { type: 'object', properties: { canal: { type: 'string' }, suscriptores: { type: 'integer' }, vistas_tipicas: { type: 'integer' }, mismo_formato: { type: 'boolean' } }, required: ['canal', 'mismo_formato'] } },
        veredicto: { type: 'string', enum: ['hueco claro', 'hueco parcial', 'saturado'] },
      },
      required: ['consultas_es', 'competidores', 'veredicto'],
    },
    rpm_estimado_es: { type: 'string', description: 'rango USD estimado para audiencia hispana + razón/fuente' },
    ventaja_usuario: { type: 'string' },
    ideas_doblez: { type: 'array', items: { type: 'string' }, description: '3-4 formas de "doblar" el nicho hacia un hueco' },
    puntuacion_nicho: { type: 'integer', description: '0-18: 0-2 por tamaño, demanda, recencia, duración, hueco ES, replicabilidad, copyright, RPM, potencial viral' },
    veredicto: { type: 'string' },
  },
  required: ['nicho', 'consultas_realizadas', 'idiomas_cubiertos', 'candidatos', 'hueco_espanol', 'rpm_estimado_es', 'ideas_doblez', 'puntuacion_nicho', 'veredicto'],
}

const VERIF_SCHEMA = {
  type: 'object',
  properties: {
    canal: { type: 'string' }, url: { type: 'string' },
    sigue_valido: { type: 'boolean' },
    problemas: { type: 'array', items: { type: 'string' } },
    suscriptores: { type: 'integer' }, mediana_vistas: { type: 'integer' }, duracion_mediana_min: { type: 'number' },
    outliers_verificados: { type: 'array', items: { type: 'object', properties: { titulo: { type: 'string' }, vistas: { type: 'integer' }, fecha: { type: 'string' }, duracion_min: { type: 'number' } }, required: ['titulo', 'vistas'] } },
    formato_visual_verificado: { type: 'string', description: 'qué se ve en las miniaturas/vídeos: ilustración IA, fotos realistas IA, stock, mapas, cara de presentador, clips ajenos...' },
    replicable: { type: 'string', enum: ['alta', 'media', 'baja'] },
    riesgo_copyright: { type: 'string', enum: ['bajo', 'medio', 'alto'] },
    competidores_es: { type: 'array', items: { type: 'object', properties: { canal: { type: 'string' }, url: { type: 'string' }, suscriptores: { type: 'integer' }, vistas_tipicas: { type: 'integer' }, mismo_formato: { type: 'boolean' } }, required: ['canal', 'mismo_formato'] } },
    hueco_espanol: { type: 'string', enum: ['hueco claro', 'hueco parcial', 'saturado'] },
    puntuacion_corregida: { type: 'integer', description: '0-18' },
    resumen: { type: 'string' },
  },
  required: ['canal', 'url', 'sigue_valido', 'problemas', 'suscriptores', 'outliers_verificados', 'formato_visual_verificado', 'replicable', 'riesgo_copyright', 'competidores_es', 'hueco_espanol', 'puntuacion_corregida', 'resumen'],
}

function explorePrompt(n) {
  return `${CONTEXTO}
TU NICHO: ${n.nombre}
Ideas de partida (amplíalas mucho, escribe consultas nativas en cada idioma): ${n.semillas}

TAREA:
1. Encuentra los mejores canales de referencia de este nicho que cumplan los filtros 1-3 (usa "filtrar" con muchas consultas y bola de nieve). Mínimo 14 consultas, mínimo 5 idiomas.
2. Para los 2-3 mejores, abre 2 miniaturas de sus outliers (curl + Read) para describir el formato visual real y juzgar replicabilidad y copyright.
3. Hueco en español: haz al menos 5 búsquedas en español del mismo tema/formato (${TOOL} filtrar "<consulta en español>" --max-subs 100000000 --periodo anio, y también "buscar" con --periodo any) y lista los canales hispanos que ya lo hacen, con suscriptores y vistas típicas. Decide: hueco claro / parcial / saturado.
4. Estima RPM en español (rango, razonado) y puntúa el nicho 0-18.
Sé honesto: si no encuentras canales que cumplan, devuelve candidatos vacíos y dilo en el veredicto. No inventes números: todo número de canal debe salir de la herramienta.`
}

function verifyPrompt(c, nichoNombre) {
  return `${CONTEXTO}
ERES UN VERIFICADOR ESCÉPTICO. Otro agente propuso este canal como referencia para el nicho "${nichoNombre}". Tu trabajo es intentar DESCARTARLO. Por defecto, si dudas, sigue_valido=false.
Canal propuesto: ${JSON.stringify({ canal: c.canal, url: c.url, idioma: c.idioma, suscriptores: c.suscriptores, formato: c.formato_visual, outliers: (c.outliers || []).slice(0, 4) })}

COMPRUEBA:
a) ${TOOL} canal "${c.url}" --refrescar : ¿suscriptores 1k-80k? ¿outliers >=3x mediana en los últimos 6 meses (desde 2026-04-06)? ¿duración típica 20-45 min? ¿las visitas vienen de demanda (vídeos con más vistas que subs)? ¿sigue activo?
b) Abre 3 miniaturas (curl a i.ytimg.com + Read) y, si hace falta, los títulos de sus vídeos: ¿usa cara de presentador, clips de películas/TV/noticias/deportes, metraje ajeno, música comercial? ¿Es contenido reutilizado? ¿Se puede replicar solo con imágenes IA + voz IA + montaje ffmpeg?
c) ¿Es un canal de India/Pakistán, infantil o de música? (descartar)
d) HUECO EN ESPAÑOL, a fondo: al menos 6 búsquedas en español (y alguna en portugués no cuenta) con distintas formulaciones del mismo formato y tema, usando "${TOOL} buscar ... --periodo any --orden relevancia" y "${TOOL} filtrar ... --max-subs 100000000". Lista los canales hispanos que ya hacen ESTE formato con sus números. ¿Queda hueco?
Devuelve los números verificados y una puntuación corregida 0-18.`
}

// ---------- Fase 1+2: explorar y verificar en pipeline ----------
phase('Explorar')
log(`Explorando ${NICHOS.length} nichos en paralelo`)

async function exploreAndVerify(nichos) {
  return pipeline(
    nichos,
    n => agent(explorePrompt(n), { label: `explorar:${n.id}`, phase: 'Explorar', schema: NICHO_SCHEMA }),
    async (res, n) => {
      if (!res) return null
      const top = (res.candidatos || []).slice(0, 3)
      if (!top.length) { log(`${n.id}: sin candidatos que cumplan`); return { nicho_id: n.id, exploracion: res, verificaciones: [] } }
      // Verificación secuencial: el siguiente candidato solo si el anterior cae (ahorra uso)
      const ok = []
      for (const c of top) {
        const v = await agent(verifyPrompt(c, n.nombre), { label: `verificar:${n.id}:${c.canal}`.slice(0, 60), phase: 'Verificar', schema: VERIF_SCHEMA })
        if (v) ok.push(v)
        if (v && v.sigue_valido) break
      }
      log(`${n.id}: ${ok.filter(v => v.sigue_valido).length ? 'candidato verificado' : 'ningún candidato sobrevive'} (${ok.length} verificados)`)
      return { nicho_id: n.id, exploracion: res, verificaciones: ok }
    },
  )
}

const ronda1 = (await exploreAndVerify(NICHOS)).filter(Boolean)

// ---------- Fase 3: crítico de completitud ----------
phase('Huecos')
const resumenR1 = ronda1.map(r => ({
  nicho: r.exploracion.nicho,
  puntuacion: r.exploracion.puntuacion_nicho,
  hueco_es: r.exploracion.hueco_espanol && r.exploracion.hueco_espanol.veredicto,
  validos: r.verificaciones.filter(v => v.sigue_valido).map(v => `${v.canal} (${v.suscriptores} subs, ${v.puntuacion_corregida}/18)`),
  descartes: r.verificaciones.filter(v => !v.sigue_valido).map(v => `${v.canal}: ${String((v.problemas || [])[0] || '').slice(0, 220)}`),
  consultas: (r.exploracion.consultas_realizadas || []).length,
}))

const CRITIC_SCHEMA = {
  type: 'object',
  properties: {
    nichos_nuevos: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, nombre: { type: 'string' }, semillas: { type: 'string' }, por_que: { type: 'string' } }, required: ['id', 'nombre', 'semillas', 'por_que'] }, description: 'máx 6 nichos NO cubiertos con potencial de RPM alto y replicables' },
    nichos_a_reintentar: { type: 'array', items: { type: 'object', properties: { id: { type: 'string' }, nombre: { type: 'string' }, semillas: { type: 'string' }, por_que: { type: 'string' } }, required: ['id', 'nombre', 'semillas', 'por_que'] }, description: 'máx 4 nichos prometedores que quedaron sin candidatos válidos por búsqueda pobre; da consultas/idiomas NUEVOS' },
  },
  required: ['nichos_nuevos', 'nichos_a_reintentar'],
}

const critica = await agent(`${CONTEXTO}
ERES EL CRÍTICO DE COMPLETITUD. Esta es la ronda 1 de exploración (${ronda1.length} nichos):
${JSON.stringify(resumenR1, null, 1)}

Pregúntate: ¿qué nichos de RPM alto, replicables con imágenes IA + voz IA y con potencial de millones de vistas NO se han explorado? (Piensa en mercados no ingleses: Alemania, Francia, Brasil, Japón, Corea, Polonia, Turquía; en formatos concretos que están explotando en 2026; en subnichos de finanzas, negocios, historia, ciencia.) ¿Qué nichos prometedores quedaron sin candidatos por una búsqueda pobre y merecen otra pasada con consultas e idiomas distintos?
Puedes usar WebSearch y la herramienta para comprobar ideas rápidamente. NO repitas nichos ya cubiertos salvo en "nichos_a_reintentar". Excluye salud/ejercicio (ya tiene ese canal).

HALLAZGO CLAVE DE LA RONDA 1 (mira "descartes"): un verificador escéptico revisó 2-3 candidatos por nicho y casi todos cayeron por el filtro 4. En 2026 el YouTube en español está lleno de clones con IA que copian en semanas cualquier formato sin cara que funcione en inglés (a veces traducen los títulos literalmente), y el doblaje automático de YouTube ya lleva muchos originales al español (pistas es-US). Por eso NO basta con "otro nicho": propón formatos DIFÍCILES DE CLONAR o con un hueco estructural, por ejemplo:
- formatos que exigen conocimiento experto real (el usuario es trader: operaciones históricas explicadas con gráficos de precios reales, sistemas de inversión, interés compuesto simulado, psicología del trading, quiebras de fondos explicadas por un trader);
- temas con datos o investigación pesada que un clonador no copia en una tarde;
- mercados de referencia NO ingleses (coreano, japonés, turco, polaco, alemán, francés, italiano, ruso, indonesio, vietnamita) cuyos formatos aún no han llegado al español;
- temas hispanos propios (historia, economía, empresas, crímenes o misterios de España y Latinoamérica) o con audiencia de España (RPM más alto);
- formatos que están explotando en 2026 con poca oferta en español.
Para cada propuesta explica en "por_que" por qué el hueco en español aguantaría y qué búsquedas en español lo comprueban. En "nichos_a_reintentar" pon solo nichos con un ÁNGULO NUEVO, no la misma búsqueda.`, { label: 'critico-completitud', phase: 'Huecos', schema: CRITIC_SCHEMA })

let ronda2 = []
if (critica) {
  const nuevos = critica.nichos_nuevos || [], reint = critica.nichos_a_reintentar || []
  const extra = [...nuevos.slice(0, 5), ...reint.slice(0, 2).map(x => ({ ...x, id: x.id + '_r2' }))]
  log(`Crítico propone ${extra.length} nichos extra: ${extra.map(x => x.id).join(', ')}`)
  if (nuevos.length > 5 || reint.length > 2) log(`No se exploran: ${[...nuevos.slice(5), ...reint.slice(2)].map(x => x.id).join(', ')}`)
  phase('Explorar')
  const AVISO = ' | AVISO DE LA RONDA 1: casi todos los candidatos cayeron porque el español ya está saturado de clones con IA y del doblaje automático de YouTube. Prioriza referencias cuyo formato NO tenga aún versión en español y compruébalo a fondo antes de proponerlas.'
  ronda2 = (await exploreAndVerify(extra.map(x => ({ id: x.id, nombre: x.nombre, semillas: x.semillas + ' | Motivo: ' + x.por_que + AVISO })))).filter(Boolean)
}

// ---------- Fase 4: selección final ----------
phase('Elegir')
const todo = [...ronda1, ...ronda2]
// Datos recortados para que el juez no reciba ~1 MB de JSON
const corta = (s, n) => (s == null ? s : String(s).slice(0, n))
const outl = o => `${corta(o.titulo, 90)} — ${o.vistas} — ${o.fecha || '¿?'}`
const compact = todo.map(r => ({
  nicho_id: r.nicho_id,
  nicho: corta(r.exploracion.nicho, 200),
  puntuacion_nicho: r.exploracion.puntuacion_nicho,
  rpm_estimado_es: corta(r.exploracion.rpm_estimado_es, 350),
  hueco_es_exploracion: r.exploracion.hueco_espanol && r.exploracion.hueco_espanol.veredicto,
  competidores_es: ((r.exploracion.hueco_espanol && r.exploracion.hueco_espanol.competidores) || []).slice(0, 5).map(c => `${c.canal} (${c.suscriptores} subs, ${c.vistas_tipicas} vistas típicas${c.mismo_formato ? ', mismo formato' : ''})`),
  ideas_doblez: (r.exploracion.ideas_doblez || []).slice(0, 4).map(x => corta(x, 260)),
  ventaja_usuario: corta(r.exploracion.ventaja_usuario, 260),
  veredicto_exploracion: corta(r.exploracion.veredicto, 450),
  candidatos: (r.exploracion.candidatos || []).slice(0, 4).map(c => ({ canal: c.canal, url: c.url, idioma: c.idioma, suscriptores: c.suscriptores, mediana_vistas: c.mediana_vistas, duracion_mediana_min: c.duracion_mediana_min, outliers: (c.outliers || []).slice(0, 2).map(outl), formato_visual: corta(c.formato_visual, 200), replicable: c.replicable, riesgo_copyright: c.riesgo_copyright })),
  cerca_del_limite: (r.exploracion.cerca_del_limite || []).slice(0, 3).map(c => `${c.canal} (${c.suscriptores} subs): ${corta(c.motivo, 140)}`),
  verificaciones: r.verificaciones.map(v => ({
    canal: v.canal, url: v.url, sigue_valido: v.sigue_valido, puntuacion_corregida: v.puntuacion_corregida,
    suscriptores: v.suscriptores, mediana_vistas: v.mediana_vistas, duracion_mediana_min: v.duracion_mediana_min,
    hueco_espanol: v.hueco_espanol, replicable: v.replicable, riesgo_copyright: v.riesgo_copyright,
    formato: corta(v.formato_visual_verificado, 200),
    outliers: (v.outliers_verificados || []).slice(0, 3).map(outl),
    competidores_es: (v.competidores_es || []).slice(0, 4).map(c => `${c.canal} (${c.suscriptores} subs${c.mismo_formato ? ', mismo formato' : ''})`),
    problemas: (v.problemas || []).slice(0, 3).map(p => corta(p, 220)),
    resumen: corta(v.resumen, 350),
  })),
}))
log(`Datos para el juez: ${JSON.stringify(compact).length} caracteres`)

const FINAL_SCHEMA = {
  type: 'object',
  properties: {
    seleccion: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          puesto: { type: 'integer' }, nicho: { type: 'string' }, nombre_canal_sugerido_es: { type: 'string' },
          estado: { type: 'string', enum: ['verificado', 'casi válido'], description: 'verificado = sigue_valido=true; casi válido = descartado por un motivo que el doblez resuelve' },
          canal_referencia: { type: 'string' }, url: { type: 'string' }, idioma_referencia: { type: 'string' },
          suscriptores: { type: 'integer' }, mediana_vistas: { type: 'integer' }, duracion_mediana_min: { type: 'number' },
          mejores_outliers: { type: 'array', items: { type: 'string' }, description: '"título — vistas — fecha"' },
          formato_visual: { type: 'string' }, replicable: { type: 'string' }, riesgo_copyright: { type: 'string' },
          hueco_espanol: { type: 'string' }, competidores_es: { type: 'string' }, rpm_estimado_es: { type: 'string' },
          doblez_recomendado: { type: 'string' }, por_que: { type: 'string' },
          suplente: { type: 'string', description: 'otro canal de referencia del mismo nicho con URL, o "ninguno"' },
          puntuacion: { type: 'integer' },
        },
        required: ['puesto', 'nicho', 'estado', 'canal_referencia', 'url', 'suscriptores', 'mejores_outliers', 'formato_visual', 'hueco_espanol', 'rpm_estimado_es', 'doblez_recomendado', 'por_que', 'puntuacion'],
      },
    },
    reservas: { type: 'array', items: { type: 'string' }, description: 'otros nichos/canales válidos por si alguno de los 9 falla' },
    descartados_destacados: { type: 'array', items: { type: 'string' }, description: 'nichos atractivos descartados y el motivo concreto' },
    advertencias: { type: 'array', items: { type: 'string' } },
  },
  required: ['seleccion', 'reservas', 'descartados_destacados', 'advertencias'],
}

const final = await agent(`${CONTEXTO}
ERES EL JUEZ FINAL. Abajo están TODOS los resultados de exploración y verificación adversarial (${todo.length} nichos).
Elige EXACTAMENTE 9 canales de referencia, cada uno de un NICHO/TEMA DISTINTO (no dos del mismo tema; salud/ejercicio excluido), ordenados del mejor al peor.
Reglas:
- Primero, los canales con sigue_valido=true (estado "verificado").
- HALLAZGO: casi todos los candidatos cayeron porque el español ya está saturado de clones con IA y del doblaje automático de YouTube. Si no hay 9 nichos con un canal verificado, completa hasta 9 con los MEJORES "casi válidos": canales con demanda real cuyo motivo de descarte se pueda resolver con un doblez concreto (otro ángulo, otra duración, temas hispanos propios, audiencia de España, la experiencia de trader del usuario, más calidad que los clones). NUNCA uses canales descartados por copyright, metraje ajeno, presentador a cámara, contenido de la India/Pakistán o canal parado. Pon estado "casi válido", escribe un "hueco_espanol" honesto, explica en "por_que" el riesgo y cómo superarlo, y añade una advertencia por cada uno.
- Prioriza: demanda real (outliers grandes y recientes), hueco en español, RPM, facilidad de replicar con imágenes IA + voz IA, riesgo de copyright bajo, potencial de millones de vistas.
- Incluye el de finanzas/trading si hay un candidato verificado o casi válido (ventaja injusta del usuario), y explica cómo usar esa ventaja.
- En "advertencias" explica también el hallazgo de la saturación y qué implica para la estrategia (velocidad de salida, calidad por encima de los clones, doblez propio).
- Si dos verificaciones discrepan con la exploración, manda la verificación.
- Usa SOLO números que estén en los datos; no inventes.
- Para cada uno, sugiere un nombre de canal en español y el "doblez" concreto (cómo hacerlo distinto).

DATOS:
${JSON.stringify(compact)}`, { label: 'juez-final', phase: 'Elegir', schema: FINAL_SCHEMA })

return { final, critica, ronda1_resumen: resumenR1, todo: compact }
