import os, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = f"{BASE}/video/musculo-01"
TMP = os.environ.get("VID_TMP", "/tmp/clips2"); os.makedirs(TMP, exist_ok=True)
X, FPS = 0.5, 25
MAP = {1:[1,2,3],2:[4,5],3:[6,7,8],4:[9,10],5:[11,12],6:[13],7:[14],8:[15],9:[16,17],10:[18],
       11:[19,20,21],12:[22,23],13:[24,25],14:[26,27,28],15:[29,30],16:[31,32],17:[33,34,35],
       18:[36,37],19:[38],20:[39,40,41]}
tj = json.load(open(f"{V}/tiempos.json"))
total = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"{V}/voz.mp3"]))
ini = {}
for b in tj: ini.setdefault(b["seccion"], b["inicio"])
ini[1] = 0.0
secs = sorted(ini); durs = []  # (escena, dur)
for i, s in enumerate(secs):
    fin = ini[secs[i+1]] if i+1 < len(secs) else total
    esc = MAP[s]; d = (fin - ini[s]) / len(esc)
    durs += [(e, d) for e in esc]
durs.sort()
def clip(k):
    e, d = durs[k]; L = d + (X if k < len(durs)-1 else 0); n = int(round(L*FPS))
    out = f"{TMP}/{e:02d}.mp4"
    if os.path.exists(out): return out
    z = f"1+0.10*on/{n}" if k % 2 == 0 else f"1.10-0.10*on/{n}"
    vf = f"scale=6400:3600:flags=lanczos,zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps={FPS},format=yuv420p"
    subprocess.run(["ffmpeg","-y","-loglevel","error","-loop","1","-i",f"{V}/escenas/{e:02d}.png","-vf",vf,"-frames:v",str(n),
                    "-c:v","libx264","-preset","veryfast","-crf","17",out], check=True)
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
    print(len(durs), "escenas, total", round(total,1), "s")
    if "--dry" in sys.argv: raise SystemExit
    with ThreadPoolExecutor(4) as ex: clips = list(ex.map(clip, range(len(durs))))
    srt()
    ins = []; 
    for c in clips: ins += ["-i", c]
    ins += ["-i", f"{V}/voz.mp3", "-stream_loop", "-1", "-i", f"{V}/musica/comercial.mp3"]
    fc, prev, S = [], "[0:v]", 0.0
    for k in range(len(durs)-1):
        S += durs[k][1]; lab = f"[x{k}]"
        fc.append(f"{prev}[{k+1}:v]xfade=transition=fade:duration={X}:offset={S:.3f}{lab}"); prev = lab
    fc.append(f"{prev}subtitles={V}/subtitulos.srt:force_style='FontName=DejaVu Sans,Bold=1,FontSize=17,Outline=2,Shadow=1,MarginV=36',format=yuv420p[v]")
    n = len(clips)
    fc.append(f"[{n+1}:a]volume=0.13,afade=t=in:st=0:d=3,afade=t=out:st={total-5.8:.1f}:d=5.8[m];[{n}:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5[a]")
    subprocess.run(["ffmpeg","-y","-loglevel","error"]+ins+["-filter_complex",";".join(fc),"-map","[v]","-map","[a]",
        "-pix_fmt","yuv420p","-c:v","libx264","-preset","veryfast","-crf","24","-c:a","aac","-b:a","160k","-shortest",
        "-movflags","+faststart",f"{V}/musculo-01_final.mp4"], check=True)
    print("listo")
