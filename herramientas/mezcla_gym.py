#!/usr/bin/env python3
"""Mezcla voz + música con rejilla de compás (la música y la voz van al mismo pulso) + efectos en los cambios de sección.
Uso: python3 mezcla_gym.py <plan.json> <salida.mp3>
Requisitos: la voz se generó con gen_voz.py BEAT=<60/bpm> BAR=4 (las secciones arrancan en el primer pulso de un compás) y todas las
pistas de música van al mismo tempo (bpm) y empiezan en el pulso 1. Cada pista se corta en un número entero de compases, se repite
con un solapamiento de 1 compás y se coloca siempre en una línea de compás: los bombos de dos pistas distintas nunca se pisan.
Plan (JSON): voz, tiempos, bpm, compas(4), cola, fundido, musica_lufs, duck_umbral, duck_ratio, musica[{archivo, compases, desde_seccion, gain}],
efectos[{seccion, archivo, gain}]. Variables de entorno: HASTA (prueba rápida: solo los primeros N s), STEMS (carpeta para guardar la cama
de música sin voz y la música ya agachada, para medirlas).
Máster en dos pasadas a -14 LUFS, pico -1,5 dBTP (estándar de YouTube)."""
import json, subprocess, sys, os, re, tempfile, math, array, functools
P = json.load(open(sys.argv[1])); OUT = sys.argv[2]
base = os.path.dirname(os.path.abspath(sys.argv[1]))
ruta = lambda f: f if os.path.isabs(f) else os.path.join(base, f)
T = json.load(open(ruta(P["tiempos"])))
BPM = P["bpm"]; COMPAS = P.get("compas", 4); B = 60 / BPM * COMPAS      # duración de un compás (s)
XF = P.get("fundido", 4.0); COLA = P.get("cola", 4.0)
fin_voz = T[-1]["fin"]; total = fin_voz + COLA
HASTA = float(os.environ.get("HASTA", 0)); STEMS = os.environ.get("STEMS")
ini_sec = {}
for b in T: ini_sec.setdefault(b["seccion"], b["inicio"])
tmp = tempfile.mkdtemp()
def run(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)
@functools.lru_cache(None)
def lufs(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
def pico(f):
    """Instante (s) del máximo de energía de un efecto: la 'subida' de un whoosh se alinea con el compás, no su comienzo."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True).stdout
    a = array.array("h"); a.frombytes(raw); h = 160
    e = [sum(x * x for x in a[i:i + h]) for i in range(0, len(a) - h, h)]
    return e.index(max(e)) * h / 8000

# 1. Cama de música: un tramo por pista, en línea de compás, repetida con 1 compás de solape y fundidos entre pistas.
partes = []
MUS = P["musica"]
for k, m in enumerate(MUS):
    N = m["compases"]; arch = ruta(m["archivo"])
    S = 0.0 if k == 0 else math.floor((ini_sec[m["desde_seccion"]] - XF / 2) / B) * B
    E = total if k == len(MUS) - 1 else math.floor((ini_sec[MUS[k + 1]["desde_seccion"]] - XF / 2) / B) * B + XF
    need = E - S; ini_c = m.get("inicio_compases", 0)
    trozos = [(ini_c * B, N * B)]; largo = (N - ini_c) * B
    while largo < need: trozos.append((0, N * B)); largo += N * B - B
    ent = []
    for u, v in trozos: ent += ["-ss", f"{u:.3f}", "-to", f"{v:.3f}", "-i", arch]
    loop = f"{tmp}/loop{k}.wav"
    if len(trozos) == 1: run(ent + ["-t", f"{need:.3f}", "-ar", "44100", "-ac", "2", loop])
    else:
        f = "[0:a]" + "".join(f"[{i}:a]acrossfade=d={B}[c{i}];[c{i}]" for i in range(1, len(trozos))); f = f.rsplit(";", 1)[0]
        run(ent + ["-filter_complex", f, "-map", f"[c{len(trozos) - 1}]", "-t", f"{need:.3f}", "-ar", "44100", "-ac", "2", loop])
    g = P.get("musica_lufs", -20) - lufs(loop) + m.get("gain", 0)
    fi = 0.15 if k == 0 else XF; fo = COLA if k == len(MUS) - 1 else XF
    # hueco para la voz: un poco menos de graves-medios y de presencia (la voz queda por encima sin subirla)
    carve = P.get("musica_eq", "highpass=f=40,equalizer=f=300:width_type=o:w=1.5:g=-3,equalizer=f=3000:width_type=o:w=1.5:g=-3")
    dest = f"{tmp}/m{k}.wav"
    run(["-i", loop, "-af", f"{carve},volume={g:.2f}dB,afade=t=in:d={fi},afade=t=out:st={need - fo:.2f}:d={fo},adelay={int(S * 1000)}|{int(S * 1000)}", "-ar", "44100", dest])
    partes.append(dest); print(f"  música {k + 1}: {os.path.basename(arch)} {S:.1f}s -> {S + need:.1f}s, {len(trozos)} vuelta(s), ganancia {g:+.1f} dB", flush=True)
ent = []
for f in partes: ent += ["-i", f]
cama = f"{tmp}/cama.wav"
run(ent + ["-filter_complex", "".join(f"[{i}:a]" for i in range(len(partes))) + f"amix=inputs={len(partes)}:normalize=0:duration=longest,atrim=0:{total:.2f}[m]", "-map", "[m]", cama])

# 2. Voz a -16 LUFS, música agachada bajo la voz (sidechain) y efectos en el primer pulso de cada sección.
g_voz = -16 - lufs(ruta(P["voz"]))
ent = ["-i", ruta(P["voz"]), "-i", cama]
filt = [f"[0:a]aformat=channel_layouts=stereo,volume={g_voz:.2f}dB,apad=whole_dur={total:.2f}[v]", "[v]asplit=2[v1][vsc]",   # apad: el sidechain acabaría con la voz y cortaría la cola de música
        f"[1:a][vsc]sidechaincompress=threshold={P.get('duck_umbral', 0.02)}:ratio={P.get('duck_ratio', 4)}:attack={P.get('duck_ataque', 30)}:release={P.get('duck_suelta', 500)}[mus]"]
if STEMS: filt[-1] = filt[-1].replace("[mus]", "[mus0]") + ";[mus0]asplit=2[mus][musst]"
etiq = ["[v1]", "[mus]"]; n = 2
for e in P.get("efectos", []):
    t = ini_sec[e["seccion"]]; arch = ruta(e["archivo"])
    if HASTA and t > HASTA: continue
    pk = pico(arch) if e.get("alinear_pico", True) else 0.0
    ini = max(t - pk, 0.0); dur = e.get("dur", 6)
    ent += ["-i", arch]
    filt.append(f"[{n}:a]aformat=channel_layouts=stereo,atrim=0:{dur},asetpts=PTS-STARTPTS,volume={P.get('efectos_lufs', -26) - lufs(arch) + e.get('gain', 0):.2f}dB,"
                f"afade=t=out:st={max(dur - 1.0, 0):.2f}:d=1.0,adelay={int(ini * 1000)}|{int(ini * 1000)}[e{n}]")
    etiq.append(f"[e{n}]"); n += 1
filt.append("".join(etiq) + f"amix=inputs={n}:duration=longest:normalize=0,atrim=0:{total:.2f},alimiter=limit=0.95:level=false[a]")
pre = f"{tmp}/premaster.wav"; lim = HASTA or total
run(ent + ["-filter_complex", ";".join(filt), "-map", "[a]", "-t", f"{lim:.2f}", "-ar", "44100", pre]
    + (["-map", "[musst]", "-t", f"{lim:.2f}", "-ar", "44100", f"{STEMS}/musica-agachada.wav"] if STEMS else []))
if STEMS: subprocess.run(["cp", cama, f"{STEMS}/cama-musica.wav"])
# 3. Máster en dos pasadas (lineal): medir y ajustar a -14 LUFS sin bombeo al inicio
o = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(o[o.rindex("{"):o.rindex("}") + 1])
run(["-i", pre, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}",
     "-ar", "44100", "-b:a", "192k", OUT])
print("ok", round(total / 60, 2), "min,", len(MUS), "pistas,", n - 2, "efectos ->", OUT)
