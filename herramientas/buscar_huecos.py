#!/usr/bin/env python3
"""Busca huecos de contenido: búsquedas populares (autocompletado de Google y YouTube)
que en YouTube tienen pocos vídeos, malos o viejos.

Uso:
  python3 herramientas/buscar_huecos.py expandir   # paso 1: autocompletado -> demanda.json
  python3 herramientas/buscar_huecos.py oferta     # paso 2: mira YouTube -> oferta.json (reanudable)
  python3 herramientas/buscar_huecos.py informe    # paso 3: puntúa -> HUECOS.md + huecos.csv

Sin APIs de pago. Salida en investigacion/huecos/.
"""
import csv, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

OUT = os.path.join(os.path.dirname(__file__), '..', 'investigacion', 'huecos')
os.makedirs(OUT, exist_ok=True)
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36'

MERCADOS = [  # (id, idioma, país)
    ('es-ES', 'es', 'ES'), ('es-US', 'es', 'US'), ('en-US', 'en', 'US'),
    ('es-MX', 'es', 'MX'), ('es-AR', 'es', 'AR'), ('es-CO', 'es', 'CO'),
]
SEMILLAS = {
    'es': ['por qué', 'qué pasó con', 'qué pasó en', 'cómo funciona', 'qué pasaría si', 'historia de',
           'cómo se hizo', 'la verdad sobre', 'quién fue', 'por qué ya no', 'cómo vivían', 'el misterio de',
           'cómo era la vida', 'por qué se hundió', 'qué hay dentro de', 'cuánto cuesta', 'cómo se construyó',
           'qué le pasó a', 'por qué desapareció', 'el caso de'],
    'en': ['why do', 'why did', 'what happened to', 'how does', 'what if', 'history of', 'how was',
           'the truth about', 'who was', 'why is', 'what was life like', 'why did they stop', 'how did',
           'mystery of', 'what is inside', 'how much does', 'how was built', 'why did disappear',
           'the case of', 'what really happened'],
}
# búsquedas que no dan para un vídeo largo (tiempo, compras, deportes en directo, letras, servicios...)
RUIDO = re.compile(r'\b(hoy|today|tonight|ahora mismo|cerca de mi|near me|en vivo|live|letra|lyrics|chords|acordes|'
                   r'tiempo en|weather|clima|resultado|score|horario|hours|precio de hoy|stock price|login|iniciar sesi|'
                   r'descargar|download|apk|gratis|free|online|netflix|capitulo|episode|cap \d|pelicula completa|'
                   r'full movie|reddit|wiki|pdf|meme|tiktok|instagram|whatsapp|roblox|minecraft|fortnite|gta|'
                   r'no funciona|not working|down|caido|calculator|calculadora|traductor|translate|test|quiz|'
                   r'en ingles|in spanish|significado|meaning|definicion|definition|sinonimo|synonym)\b')


def get(url, intentos=3):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en-US,en;q=0.8'})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            if i == intentos - 1:
                raise
            time.sleep(2 * (i + 1))


def sugerencias(q, idioma, pais, yt):
    url = ('https://suggestqueries.google.com/complete/search?client=firefox&hl=%s&gl=%s&q=%s%s'
           % (idioma, pais.lower(), urllib.parse.quote(q), '&ds=yt' if yt else ''))
    try:
        return json.loads(get(url))[1]
    except Exception:
        return []


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def expandir():
    tareas = []
    for mid, idioma, pais in MERCADOS:
        for sem in SEMILLAS[idioma]:
            for suf in [''] + [' ' + c for c in 'abcdefghijklmnopqrstuvwyz']:
                for yt in (False, True):
                    tareas.append((mid, idioma, pais, sem + suf, yt))
    print(len(tareas), 'consultas de autocompletado')
    dem = {}

    def uno(t):
        mid, idioma, pais, q, yt = t
        return t, sugerencias(q, idioma, pais, yt)

    with ThreadPoolExecutor(8) as ex:
        for n, (t, sug) in enumerate(ex.map(uno, tareas), 1):
            mid, idioma, pais, q, yt = t
            for pos, s in enumerate(sug):
                k = norm(s).strip()
                if len(k.split()) < 3 or RUIDO.search(k):
                    continue
                d = dem.setdefault(k, {'consulta': s, 'idioma': idioma, 'mercados': [], 'google': 0, 'youtube': 0, 'pts': 0.0})
                if mid not in d['mercados']:
                    d['mercados'].append(mid)
                d['youtube' if yt else 'google'] += 1
                d['pts'] += 1.0 / (1 + pos)  # las primeras sugerencias son las más buscadas
            if n % 500 == 0:
                print(n, 'hechas,', len(dem), 'búsquedas')
    for d in dem.values():
        # demanda: posición + presencia en Google y YouTube + varios mercados
        d['demanda'] = round(d['pts'] * (1.5 if d['google'] and d['youtube'] else 1) * (1 + 0.5 * (len(d['mercados']) - 1)), 3)
    json.dump(sorted(dem.values(), key=lambda d: -d['demanda']), open(os.path.join(OUT, 'demanda.json'), 'w'),
              ensure_ascii=False, indent=1)
    print(len(dem), 'búsquedas guardadas en demanda.json')


def num(s):
    s = re.sub(r'[^\d]', '', s or '')
    return int(s) if s else 0


def dur(s):
    p = [int(x) for x in re.findall(r'\d+', s or '')]
    m = 0
    for x in p:
        m = m * 60 + x
    return m / 60 if p else 0  # minutos


def edad_dias(s):
    # formatos: "5 years ago" o abreviado "5y ago", "11mo ago", "3w ago", "2d ago", "4h ago"
    m = re.search(r'(\d+)\s*(second|sec|s|minute|min|hour|h|day|d|week|w|month|mo|year|y)s?\b', s or '')
    if not m:
        return None
    u = m.group(2)
    f = 365 if u.startswith('y') else 30 if u.startswith('mo') else 7 if u.startswith('w') else 1 if u.startswith('d') else 0
    return int(m.group(1)) * f


def youtube(q, pais):
    html = get('https://www.youtube.com/results?search_query=%s&hl=en&gl=%s' % (urllib.parse.quote(q), pais))
    m = re.search(r'var ytInitialData = (\{.*?\});</script>', html)
    if not m:
        raise RuntimeError('sin ytInitialData (¿bloqueo?)')
    vids = []

    def walk(o):
        if isinstance(o, dict):
            if 'videoRenderer' in o:
                v = o['videoRenderer']
                g = lambda k: (v.get(k) or {}).get('simpleText') or ''.join(r.get('text', '') for r in (v.get(k) or {}).get('runs', []))
                vids.append({'titulo': g('title'), 'vistas': num(g('viewCountText')), 'min': round(dur(g('lengthText')), 1),
                             'dias': edad_dias(g('publishedTimeText')), 'canal': g('ownerText'), 'id': v.get('videoId')})
                return
            for x in o.values():
                walk(x)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(json.loads(m.group(1)))
    return vids[:20]


VACIAS = set('el la los las de del y o a en un una por que qué como cómo es se su sus lo al para con the of a an to in is was why how what did do does who and on for if'.split())


def relevante(q, titulo):
    pq = [w for w in re.findall(r'\w+', norm(q)) if w not in VACIAS and len(w) > 2]
    if not pq:
        return False
    pt = set(re.findall(r'\w+', norm(titulo)))
    acierto = sum(1 for w in pq if w in pt or any(t.startswith(w[:5]) for t in pt if len(w) > 5))
    return acierto / len(pq) >= 0.6


def oferta(max_consultas=1200):
    dem = json.load(open(os.path.join(OUT, 'demanda.json')))
    ruta = os.path.join(OUT, 'oferta.json')
    hecho = json.load(open(ruta)) if os.path.exists(ruta) else {}
    pend = [d for d in dem[:max_consultas] if d['consulta'] not in hecho]
    print(len(pend), 'consultas pendientes en YouTube')
    fallos = 0
    for i, d in enumerate(pend, 1):
        pais = 'US' if d['idioma'] == 'en' else d['mercados'][0].split('-')[1]
        try:
            hecho[d['consulta']] = youtube(d['consulta'], pais)
            fallos = 0
        except Exception as e:
            fallos += 1
            print('fallo', d['consulta'], e)
            if fallos >= 5:
                print('5 fallos seguidos: pausa de 10 min por posible bloqueo')
                time.sleep(600)
                fallos = 0
            continue
        if i % 25 == 0:
            json.dump(hecho, open(ruta, 'w'), ensure_ascii=False)
            print(i, 'de', len(pend))
        time.sleep(1.2)
    json.dump(hecho, open(ruta, 'w'), ensure_ascii=False)


def informe():
    dem = {d['consulta']: d for d in json.load(open(os.path.join(OUT, 'demanda.json')))}
    of = json.load(open(os.path.join(OUT, 'oferta.json')))
    filas = []
    for q, vids in of.items():
        d = dem.get(q)
        if not d:
            continue
        rel = [v for v in vids if relevante(q, v['titulo'])]
        largos = [v for v in rel if v['min'] >= 8]
        recientes = [v for v in largos if v['dias'] is not None and v['dias'] <= 365 * 2]
        buenos_recientes = [v for v in recientes if v['vistas'] >= 20000]
        max_v = max([v['vistas'] for v in rel] or [0])
        # tipo de hueco
        if not largos:
            tipo = 'VACÍO: ningún vídeo largo que lo responda'
        elif not recientes:
            tipo = 'VIEJO: solo vídeos largos de hace más de 2 años'
        elif not buenos_recientes:
            tipo = 'FLOJO: los vídeos largos recientes tienen menos de 20.000 vistas'
        else:
            continue  # bien cubierto
        prueba = max(rel, key=lambda v: v['vistas'], default=None)
        # demanda probada: vídeos (aunque sean cortos o viejos) con muchas vistas
        bonus = 1 + min(max_v, 2_000_000) / 500_000
        filas.append({'consulta': q, 'idioma': d['idioma'], 'mercados': ' '.join(d['mercados']), 'demanda': d['demanda'],
                      'puntos': round(d['demanda'] * bonus * (1.3 if tipo.startswith('VAC') else 1), 2), 'hueco': tipo,
                      'relevantes': len(rel), 'largos': len(largos), 'max_vistas_rel': max_v,
                      'mejor_video': f"{prueba['titulo']} ({prueba['vistas']:,} vistas, {prueba['min']} min, hace {prueba['dias']} días)" if prueba else ''})
    filas.sort(key=lambda f: -f['puntos'])
    with open(os.path.join(OUT, 'huecos.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(len(of), 'búsquedas revisadas;', len(filas), 'con hueco')
    return filas


if __name__ == '__main__':
    {'expandir': expandir, 'oferta': oferta, 'informe': informe}[sys.argv[1]]()
