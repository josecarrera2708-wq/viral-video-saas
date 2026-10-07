#!/usr/bin/env python3
"""Mezcla profesional: voz + música por tramos (con fundidos cruzados y ducking bajo la voz) + efectos anclados a frases del guion.
Uso: python3 mezcla_v2.py <plan.json> <salida.mp3>
El plan (JSON) define voz, tiempos, música por secciones y efectos por frase. La música arranca con la voz y sigue unos segundos
después de la última palabra con un fundido de salida (nunca se corta de golpe). Máster a -14 LUFS (estándar de YouTube)."""
import json, subprocess, sys, os, tempfile
P = json.load(open(sys.argv[1])); OUT = sys.argv[2]
base = os.path.dirname(os.path.abspath(sys.argv[1]))
ruta = lambda f: f if os.path.isabs(f) else os.path.join(base, f)
T = json.load(open(ruta(P["tiempos"])))
fin_voz = T[-1]["fin"]; COLA = P.get("cola", 4.0); total = fin_voz + COLA
ini_sec = {}
for b in T: ini_sec.setdefault(b["seccion"], b["inicio"])
tmp = tempfile.mkdtemp()

def run(args): subprocess.run(["ffmpeg", "-v", "error", "-y"] + args, check=True)

# 1. Lecho musical: un tramo por bloque de secciones, en bucle, con fundidos de entrada y salida que se solapan.
XF = P.get("fundido_musica", 4.0)
tramos = P["musica"]
partes = []
for k, m in enumerate(tramos):
    t0 = 0.0 if k == 0 else ini_sec[m["desde_seccion"]] - XF / 2
    t1 = total if k == len(tramos) - 1 else ini_sec[tramos[k + 1]["desde_seccion"]] + XF / 2
    d = t1 - t0
    fi = 1.5 if k == 0 else XF
    fo = COLA if k == len(tramos) - 1 else XF
    f = f"{tmp}/m{k}.wav"
    run(["-stream_loop", "-1", "-ss", str(m.get("inicio", 0)), "-i", ruta(m["archivo"]), "-t", f"{d:.2f}",
         "-af", f"aformat=channel_layouts=stereo,loudnorm=I=-23:TP=-3,volume={m.get('gain', 0)}dB,"
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
ent = ["-i", ruta(P["voz"]), "-i", f"{tmp}/musica.wav"]
filt = ["[0:a]aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2[v]", "[v]asplit=2[v1][vsc]",
        f"[1:a][vsc]sidechaincompress=threshold={P.get('duck_umbral', 0.03)}:ratio={P.get('duck_ratio', 4)}:attack=80:release=900[mus]"]
etiq = ["[v1]", "[mus]"]; n = 2
for e in P["efectos"]:
    t = max(instante(e["frase"]) + e.get("desfase", 0), 0)
    dur = e.get("dur", 8)
    ent += ["-i", ruta(e["archivo"])]
    filt.append(f"[{n}:a]aformat=channel_layouts=stereo,atrim=0:{dur},asetpts=PTS-STARTPTS,loudnorm=I=-20:TP=-3,volume={e.get('gain', -12)}dB,"
                f"afade=t=in:d={e.get('fade_in', 0.05)},afade=t=out:st={max(dur - e.get('fade_out', 1.5), 0)}:d={e.get('fade_out', 1.5)},"
                f"adelay={int(t * 1000)}|{int(t * 1000)}[e{n}]")
    etiq.append(f"[e{n}]"); n += 1
filt.append("".join(etiq) + f"amix=inputs={n}:duration=longest:normalize=0,atrim=0:{total:.2f},"
            f"loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.89[a]")
run(ent + ["-filter_complex", ";".join(filt), "-map", "[a]", "-t", f"{total:.2f}", "-ar", "44100", "-b:a", "192k", OUT])
print("ok", round(total / 60, 2), "min,", len(tramos), "tramos de música,", n - 2, "efectos")
