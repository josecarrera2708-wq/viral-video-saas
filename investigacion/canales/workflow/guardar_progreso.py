import json, sys, os
J, OUT = sys.argv[1], sys.argv[2]
ev = [json.loads(l) for l in open(J) if l.strip()]
lab, orden = {}, []
for e in ev:
    if (e.get('type') or e.get('event')) == 'started':
        lab[e['key']] = e.get('label') or ''
        orden.append(e['key'])
def parse(r):
    if isinstance(r, str):
        try: return json.loads(r)
        except Exception: return {'texto': r}
    return r
res = {}
for e in ev:
    if (e.get('type') or e.get('event')) == 'result':
        res[e['key']] = parse(e['result'])  # el último gana (caché repetida)
# frontera ronda 1 / ronda 2: arranque del crítico
# el crítico y el juez arrancaron (y fallaron) en ejecuciones cortadas por el límite: vale el último arranque
pos_crit = [i for i, k in enumerate(orden) if lab[k] == 'critico-completitud']
crit_key = orden[pos_crit[-1]] if pos_crit else None
corte = pos_crit[-1] if pos_crit else len(orden)
r1, r2 = {}, {}
ver1, ver2 = {}, {}
for i, k in enumerate(orden):
    if k not in res: continue
    l = lab[k]; ronda2 = i > corte
    if l.startswith('explorar:'):
        d = dict(res[k]); d['nicho_id'] = l.split(':', 1)[1]
        (r2 if ronda2 else r1)[l] = d
    elif l.startswith('verificar:'):
        d = dict(res[k]); d['nicho_id'] = l.split(':')[1]
        (ver2 if ronda2 else ver1)[(d['nicho_id'], d.get('canal'))] = d
def dump(nombre, obj):
    with open(os.path.join(OUT, nombre), 'w') as f: json.dump(obj, f, ensure_ascii=False, indent=1)
dump('ronda1_exploracion.json', list(r1.values()))
dump('verificaciones_ronda1.json', list(ver1.values()))
if crit_key in res: dump('critica_ronda1.json', res[crit_key])
if r2: dump('ronda2_exploracion.json', list(r2.values()))
if ver2: dump('verificaciones_ronda2.json', list(ver2.values()))
juez = [k for k in orden if lab[k] == 'juez-final' and k in res]
if juez: dump('juez_final.json', res[juez[-1]])
validos = {}
for d in list(ver1.values()) + list(ver2.values()):
    if d.get('sigue_valido'): validos.setdefault(d['nicho_id'], []).append(f"{d.get('canal')} ({d.get('puntuacion_corregida')})")
print('ronda1 exploraciones', len(r1), '| verificaciones r1', len(ver1), '| ronda2 exploraciones', len(r2), '| verificaciones r2', len(ver2), '| juez', bool(juez))
print('nichos con canal válido:', len(validos))
for n, c in validos.items(): print(' -', n, ':', '; '.join(c))
