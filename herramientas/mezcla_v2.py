#!/usr/bin/env python3
"""Mezcla profesional: voz + música por tramos (con fundidos cruzados y ducking bajo la voz) + efectos anclados a frases del guion.
Uso: python3 mezcla_v2.py <plan.json> <salida.mp3>
El plan (JSON) define voz, tiempos, música por secciones y efectos por frase. La música arranca con la voz y sigue unos segundos
después de la última palabra con un fundido de salida (nunca se corta de golpe). Máster a -14 LUFS (estándar de YouTube)."""
import json, subprocess, sys, os, tempfile, re
P = json.load(open(sys.argv[1])); OUT = sys.argv[2]
base = os.path.dirname(os.path.abspath(sys.argv[1]))
ruta = lambda f: f if os.path.isabs(f) else os.path.join(base, f)
T = json.load(open(ruta(P["tiempos"])))
fin_voz = T[-1]["fin"]; COLA = P.get("cola", 4.0); total = fin_voz + COLA
ini_sec = {}
for b in T: ini_sec.setdefault(b["seccion"], b["inicio"])
tmp = tempfile.mkdtemp()

import functools
@functools.lru_cache(None)
def lufs(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
def run(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)

# 1. Lecho musical: un tramo por bloque de secciones, en bucle, con fundidos de entrada y salida que se solapan.
XF = P.get("fundido_musica", 4.0)
tramos = P["musica"]
# Ecualización para altavoces pequeños (móvil/portátil): se aplica una vez por pista y se mide después
_eq = {}
for m in tramos:
    a = ruta(m["archivo"])
    if a not in _eq:
        _eq[a] = f"{tmp}/eq{len(_eq)}.wav"
        run(["-i", a, "-af", P.get("musica_eq", "anull"), "-ar", "44100", _eq[a]])
    m["archivo"] = _eq[a]
partes = []
for k, m in enumerate(tramos):
    t0 = 0.0 if k == 0 else ini_sec[m["desde_seccion"]] - XF / 2
    t1 = total if k == len(tramos) - 1 else ini_sec[tramos[k + 1]["desde_seccion"]] + XF / 2
    d = t1 - t0
    fi = 3.0 if k == 0 else XF
    fo = COLA if k == len(tramos) - 1 else XF
    f = f"{tmp}/m{k}.wav"
    run(["-stream_loop", "-1", "-ss", str(m.get("inicio", 0)), "-i", ruta(m["archivo"]), "-t", f"{d:.2f}",
         "-af", f"aformat=channel_layouts=stereo,volume={-23 - lufs(ruta(m['archivo'])) + m.get('gain', 0):.2f}dB,"
                f"afade=t=in:d={fi},afade=t=out:st={d - fo:.2f}:d={fo},adelay={int(t0 * 1000)}|{int(t0 * 1000)}",
         "-ar", "44100", f])
    partes.append(f)
ent = []
for f in partes: ent += ["-i", f]
run(ent + ["-filter_complex", "".join(f"[{i}:a]" for i in range(len(partes))) + f"amix=inputs={len(partes)}:normalize=0:duration=longest,atrim=0:{total:.2f}[m]",
           "-map", "[m]", f"{tmp}/musica.wav"])

# 2. Efectos anclados a frases: el instante se estima por la posición de la frase dentro de su párrafo.
def instante(frase):
    for b in T:
        i = b["texto"].find(frase)
        if i >= 0: return b["inicio"] + (b["fin"] - b["inicio"]) * i / max(len(b["texto"]), 1)
    raise SystemExit(f"Frase no encontrada en el guion: {frase!r}")
g_voz = -16 - lufs(ruta(P["voz"]))
ent = ["-i", ruta(P["voz"]), "-i", f"{tmp}/musica.wav"]
filt = [f"[0:a]aformat=channel_layouts=stereo,volume={g_voz:.2f}dB[v]", "[v]asplit=2[v1][vsc]",
        f"[1:a][vsc]sidechaincompress=threshold={P.get('duck_umbral', 0.03)}:ratio={P.get('duck_ratio', 4)}:attack=80:release=900[mus]"]
etiq = ["[v1]", "[mus]"]; n = 2
for e in P["efectos"]:
    t = max(instante(e["frase"]) + e.get("desfase", 0), 0)
    dur = e.get("dur", 8)
    ent += ["-i", ruta(e["archivo"])]
    filt.append(f"[{n}:a]aformat=channel_layouts=stereo,atrim=0:{dur},asetpts=PTS-STARTPTS,volume={-20 - lufs(ruta(e['archivo'])) + e.get('gain', -12) + P.get('efectos_offset', 0) + (P.get('efectos_offset_intro', 0) if t < P.get('fin_intro', 0) else 0)}dB,"
                f"afade=t=in:d={e.get('fade_in', 0.05)},afade=t=out:st={max(dur - e.get('fade_out', 1.5), 0)}:d={e.get('fade_out', 1.5)},"
                f"adelay={int(t * 1000)}|{int(t * 1000)}[e{n}]")
    etiq.append(f"[e{n}]"); n += 1
filt.append("".join(etiq) + f"amix=inputs={n}:duration=longest:normalize=0,atrim=0:{total:.2f},"
            f"alimiter=limit=0.95:level=false[a]")
pre = f"{tmp}/premaster.wav"
run(ent + ["-filter_complex", ";".join(filt), "-map", "[a]", "-t", f"{total:.2f}", "-ar", "44100", pre])
# Máster en dos pasadas (lineal): medir y luego ajustar a -14 LUFS sin bombeo al inicio
o = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(o[o.rindex("{"):o.rindex("}") + 1])
run(["-i", pre, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}",
     "-ar", "44100", "-b:a", "192k", OUT])
print("ok", round(total / 60, 2), "min,", len(tramos), "tramos de música,", n - 2, "efectos")
