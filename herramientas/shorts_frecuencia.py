#!/usr/bin/env python3
"""Genera Shorts verticales 1080x1920 a partir de las escenas del vídeo (no del mp4 final, que lleva subtítulos horizontales grabados).
Uso: python3 shorts_frecuencia.py <carpeta_video> <mapa> <plano_camara> <audio> <salida_dir>   (SHORTS = lista en este archivo)
Cada Short: ventana [a,b] de la locución, recorte 9:16 con movimientos de cámara (cv2.warpAffine), cortes secos entre escenas, titular arriba,
subtítulos grandes de 4 palabras, aviso final y audio con loudnorm -14 LUFS. Sin coste (todo local)."""
import os, re, json, subprocess, sys
V, MAPF, CAMF, AUD, OUT = [a.rstrip("/") for a in sys.argv[1:6]]
os.makedirs(OUT, exist_ok=True)
TMP = os.environ.get("VID_TMP", "/tmp/shorts_tmp"); os.makedirs(TMP, exist_ok=True)
FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Anton-Regular.ttf")
FPS, FIN_S = 25, 20.0
SHORTS = [
    dict(n="short1_seis_dias", a=256.8, b=316.9, titulo="¿6 DÍAS = EL DOBLE|DE MÚSCULO?", cta="LA CIENCIA RESPONDE|VÍDEO COMPLETO EN EL CANAL"),
    dict(n="short2_relleno_vs_duro", a=439.4, b=481.9, titulo="EL ERROR QUE|FRENA TU MÚSCULO", cta="LOS 3 CASOS EN EL|VÍDEO COMPLETO"),
    dict(n="short3_verdadero_falso", a=58.4, b=92.7, titulo="¿VERDADERO|O FALSO?", cta="RESPUESTAS EN EL|VÍDEO COMPLETO"),
]
sec_de = {int(k): v for k, v in json.load(open(MAPF)).items()}
CAM = {int(k): v for k, v in json.load(open(CAMF)).items()}
tj = json.load(open(f"{V}/tiempos.json"))
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUD]))
ini = {}
for b in tj: ini.setdefault(b["seccion"], b["inicio"])
ini[min(ini)] = 0.0
secs = sorted(ini); ultima = max(sec_de); fin_t = total - FIN_S
MAP = {}
for e, s in sorted(sec_de.items()):
    if e != ultima: MAP.setdefault(s, []).append(e)
esc = []; t = 0.0                                      # (escena, inicio, duración): misma cuenta que montar_video_v4.py
for i, s in enumerate(secs):
    fin = ini[secs[i + 1]] if i + 1 < len(secs) else fin_t
    d = (fin - ini[s]) / len(MAP[s])
    for e in MAP[s]: esc.append((e, ini[s] + (len(esc) and 0), d))
# recalcular inicios acumulados por sección
esc = []
for i, s in enumerate(secs):
    fin = ini[secs[i + 1]] if i + 1 < len(secs) else fin_t
    d = (fin - ini[s]) / len(MAP[s])
    for j, e in enumerate(MAP[s]): esc.append((e, ini[s] + j * d, d))
def ease(t): return 0.5 * t + 0.5 * (t * t * (3 - 2 * t))
def vclip(e, d):
    """Escena completa en vertical (3 planos) de duración d; caché."""
    import cv2, numpy as np
    out = f"{TMP}/v{e:02d}_{int(d*100)}.mp4"
    if os.path.exists(out): return out
    img = cv2.imread(f"{V}/escenas/{e:02d}.png"); H, W = img.shape[:2]
    planos = CAM.get(e) or [["push", 1.0, 1.2, .5, .45]]
    n = int(round(d * FPS)); m = len(planos); ns = [n // m] * m; ns[-1] = n - sum(ns[:-1])
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "1080x1920", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for pl, k in zip(planos, ns):
        if pl[0] == "push" or pl[0] == "pull": _, z0, z1, fx, fy = pl; f0 = f1 = (fx, fy)
        elif pl[0] == "pan": _, z0, fx0, fy, fx1 = pl; z1 = z0; f0 = (fx0, fy); f1 = (fx1, fy)
        else: z0 = z1 = 1.0; f0 = f1 = (.5, .5)
        z0 *= 1.0; z1 *= 1.0
        for i in range(k):
            u = ease(i / max(k - 1, 1)); z = z0 + (z1 - z0) * u
            fx = f0[0] + (f1[0] - f0[0]) * u; fy = f0[1] + (f1[1] - f0[1]) * u
            ch = H / z; cw = ch * 9 / 16
            x0 = min(max(fx * W - cw / 2, 0), W - cw); y0 = min(max(fy * H - ch / 2, 0), H - ch)
            sc = 1920 / ch
            M = np.float64([[sc, 0, -x0 * sc], [0, sc, -y0 * sc]])
            p.stdin.write(cv2.warpAffine(img, M, (1080, 1920), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).tobytes())
    p.stdin.close(); p.wait(); return out
def ts(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{t%60:06.3f}".replace(".", ",")
def srt(a, b, path):
    cues, c = [], 1
    for bl in tj:
        if bl["fin"] <= a or bl["inicio"] >= b: continue
        frases = [f for f in re.split(r"(?<=[.!?:])\s+", bl["texto"]) if f]; trozos = []
        for f in frases:
            w = f.split()
            for i in range(0, len(w), 4): trozos.append(" ".join(w[i:i + 4]))
        tot = sum(len(x) for x in trozos); t0 = bl["inicio"]; span = bl["fin"] - bl["inicio"]
        for x in trozos:
            d = span * len(x) / tot
            s0, s1 = max(t0, a) - a, min(t0 + d, b) - a
            if s1 > s0: cues.append(f"{c}\n{ts(s0)} --> {ts(s1)}\n{x.upper()}\n"); c += 1
            t0 += d
    open(path, "w", encoding="utf-8").write("\n".join(cues))
def lineas(txt, y0, size, color):
    return [f"drawtext=fontfile={FONT}:text='{l}':fontsize={size}:fontcolor={color}:borderw=6:bordercolor=black:x=(w-text_w)/2:y={y0 + i * (size + 14)}"
            for i, l in enumerate(txt.split("|"))]
def hacer(S):
    a, b = S["a"], S["b"]; D = b - a; partes = []
    for e, s0, d in esc:
        o0, o1 = max(a, s0), min(b, s0 + d)
        if o1 - o0 < 0.05: continue
        clip = vclip(e, d); out = f"{TMP}/{S['n']}_{e:02d}.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{o0 - s0:.3f}", "-t", f"{o1 - o0:.3f}", "-i", clip, "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS), out], check=True); partes.append(out)
    lst = f"{TMP}/{S['n']}.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in partes))
    base = f"{TMP}/{S['n']}_base.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", base], check=True)
    sub = f"{TMP}/{S['n']}.srt"; srt(a, b, sub)
    vf = ",".join(["vignette=PI/6"] + lineas(S["titulo"], 170, 120, "0xFFD400") +
                  [f"subtitles={sub}:force_style='FontName=DejaVu Sans,Bold=1,FontSize=15,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=4,Shadow=0,Alignment=2,MarginV=52'"] +
                  [x + f":enable='gte(t,{D - 3.2:.2f})'" for x in lineas(S["cta"], 1180, 66, "0xFFD400")] + ["format=yuv420p"])
    af = f"atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=out:st={D - 0.4:.2f}:d=0.4,loudnorm=I=-14:TP=-1.5:LRA=11"
    salida = f"{OUT}/{S['n']}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", base, "-i", AUD, "-filter_complex", f"[0:v]{vf}[v];[1:a]{af}[a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-t", f"{D:.2f}", "-movflags", "+faststart", salida], check=True)
    print("listo", salida, round(D, 1), "s", flush=True)
if __name__ == "__main__":
    for S in SHORTS: hacer(S)
