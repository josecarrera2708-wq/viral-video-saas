#!/usr/bin/env python3
"""Monta el vídeo: N escenas, 3 encuadres distintos por escena (zoom/paneo), fundidos entre escenas, subtítulos y audio ya mezclado.
Uso: python3 montar_video_v3.py <carpeta_video> <mapa_escenas.json> [--dry]   (la carpeta debe tener escenas/, tiempos.json, audio_final_musica_efectos.mp3)"""
import os, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
V, MAPF = sys.argv[1].rstrip("/"), sys.argv[2]
TMP = os.environ.get("VID_TMP", "/tmp/clips_v3"); os.makedirs(TMP, exist_ok=True)
X, FPS, SS = 0.5, 25, 5760
sec_de = {int(k): v for k, v in json.load(open(MAPF)).items()}   # escena -> sección
MAP = {}
for e, s in sorted(sec_de.items()): MAP.setdefault(s, []).append(e)
tj = json.load(open(f"{V}/tiempos.json"))
AUD = f"{V}/audio_final_musica_efectos.mp3"
total = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",AUD]))
ini = {}
for b in tj: ini.setdefault(b["seccion"], b["inicio"])
ini[min(ini)] = 0.0
secs = sorted(ini); durs = []
for i, s in enumerate(secs):
    fin = ini[secs[i+1]] if i+1 < len(secs) else total
    esc = MAP[s]; d = (fin - ini[s]) / len(esc)
    durs += [(e, d) for e in esc]
durs.sort()
def shot(e, idx, n, k):
    """idx 0,1,2 = tres encuadres distintos; k alterna el orden/dirección entre escenas."""
    out = f"{TMP}/{e:02d}_{idx}.mp4"
    if os.path.exists(out): return out
    forma = (idx + k) % 3
    if forma == 0: z, x, y = f"1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif forma == 1: z, x, y = "1.16", f"(iw-iw/zoom)*{'on/'+str(n) if k%2==0 else '(1-on/'+str(n)+')'}", "ih/2-(ih/zoom/2)"
    else: z, x, y = f"1.14-0.14*on/{n}", "(iw-iw/zoom)*0.7", "(ih-ih/zoom)*0.3"
    vf = f"scale={SS}:{SS*9//16}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps={FPS},format=yuv420p"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",f"{V}/escenas/{e:02d}.png","-vf",vf,"-frames:v",str(n),
                    "-c:v","libx264","-preset","veryfast","-crf","16",out], check=True)
    return out
def clip(k):
    e, d = durs[k]; L = d + (X if k < len(durs)-1 else 0); n = int(round(L*FPS)); a = n // 3
    ns = [a, a, n - 2*a]
    out = f"{TMP}/{e:02d}.mp4"
    if os.path.exists(out): return out
    partes = [shot(e, i, ns[i], k) for i in range(3)]
    lst = f"{TMP}/{e:02d}.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in partes))
    subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",lst,"-c","copy",out], check=True)
    return out
def ts(t):
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
def srt():
    cues, c = [], 1
    for b in tj:
        frases = [f for f in re.split(r"(?<=[.!?:])\s+", b["texto"]) if f]
        trozos = []
        for f in frases:
            w = f.split()
            for i in range(0, len(w), 9): trozos.append(" ".join(w[i:i+9]))
        tot = sum(len(t) for t in trozos); t0 = b["inicio"]; span = b["fin"] - b["inicio"]
        for t in trozos:
            d = span * len(t) / tot
            cues.append(f"{c}\n{ts(t0)} --> {ts(t0+d)}\n{t}\n"); c += 1; t0 += d
    open(f"{V}/subtitulos.srt", "w", encoding="utf-8").write("\n".join(cues))
if __name__ == "__main__":
    print(len(durs), "escenas, total", round(total,1), "s, ~", round(total/len(durs)/3,1), "s por encuadre", flush=True)
    if "--dry" in sys.argv: raise SystemExit
    with ThreadPoolExecutor(int(os.environ.get("HILOS", "4"))) as ex: clips = list(ex.map(clip, range(len(durs))))
    print("clips listos", flush=True); srt()
    ins = []
    for c in clips: ins += ["-i", c]
    ins += ["-i", AUD]
    fc, prev, S = [], "[0:v]", 0.0
    for k in range(len(durs)-1):
        S += durs[k][1]; lab = f"[x{k}]"
        fc.append(f"{prev}[{k+1}:v]xfade=transition=fade:duration={X}:offset={S:.3f}{lab}"); prev = lab
    fc.append(f"{prev}subtitles={V}/subtitulos.srt:force_style='FontName=DejaVu Sans,Bold=1,FontSize=17,Outline=2,Shadow=1,MarginV=36',format=yuv420p[v]")
    crf = os.environ.get("CRF", "26")
    subprocess.run(["ffmpeg","-y","-loglevel","error"]+ins+["-filter_complex",";".join(fc),"-map","[v]","-map",f"{len(clips)}:a",
        "-pix_fmt","yuv420p","-profile:v","high","-c:v","libx264","-preset","veryfast","-crf",crf,"-c:a","aac","-b:a","160k","-shortest",
        "-movflags","+faststart",f"{V}/lagartijas-01.mp4"], check=True)
    print("listo", flush=True)
