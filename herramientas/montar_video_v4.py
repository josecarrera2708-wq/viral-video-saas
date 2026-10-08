#!/usr/bin/env python3
"""Monta el vídeo con planos de cámara variados: cada escena se divide en 2-3 planos (cortes de encuadre sobre la misma imagen:
general -> medio -> detalle) con movimientos distintos (push, pull, pan, handheld suave), fundidos entre escenas, fundido a negro
entre secciones, viñeta suave, subtítulos y el audio ya mezclado. La última escena es la pantalla final (estática, sin subtítulos).
Uso: python3 montar_video_v4.py <carpeta_video> <mapa_escenas.json> <plano_camara.json> <audio.mp3> <salida.mp4> [--dry]
plano_camara.json: {"N": [[tipo, ...], ...]} con tipos: ["push", z0, z1, fx, fy], ["pull", z0, z1, fx, fy], ["pan", z, fx0, fy, fx1], ["fijo"]
(fx, fy = punto de interés 0..1 de la imagen). Escena sin entrada: se genera un plano por defecto.
Variables: FIN_S (s de pantalla final, def. 20), HILOS, CRF, VID_TMP."""
import os, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
V, MAPF, CAMF, AUD, SAL = sys.argv[1].rstrip("/"), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
TMP = os.environ.get("VID_TMP", "/tmp/clips_v4"); os.makedirs(TMP, exist_ok=True)
FIN_S = float(os.environ.get("FIN_S", 20)); X = 0.5; XS = 0.9; FPS = 25; SS = 5760
sec_de = {int(k): v for k, v in json.load(open(MAPF)).items()}
CAM = {int(k): v for k, v in json.load(open(CAMF)).items()}
tj = json.load(open(f"{V}/tiempos.json"))
total = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUD]))
ini = {}
for b in tj: ini.setdefault(b["seccion"], b["inicio"])
ini[min(ini)] = 0.0
secs = sorted(ini); ultima = max(sec_de)
fin_t = total - FIN_S                                  # la pantalla final ocupa los últimos FIN_S s
MAP = {}
for e, s in sorted(sec_de.items()):
    if e != ultima: MAP.setdefault(s, []).append(e)
durs = []; cambio = set()
for i, s in enumerate(secs):
    fin = ini[secs[i + 1]] if i + 1 < len(secs) else fin_t
    esc = MAP[s]; d = (fin - ini[s]) / len(esc)
    if durs and i > 0: cambio.add(len(durs))           # primera escena de una sección nueva: fundido a negro
    durs += [(e, d) for e in esc]
durs.append((ultima, FIN_S)); cambio.add(len(durs) - 1)
def por_defecto(e):
    """Tres planos por defecto, rotando el estilo según el número de escena."""
    k = e % 3
    ops = [[["push", 1.0, 1.12, .5, .45], ["pan", 1.22, .35, .45, .65], ["push", 1.1, 1.38, .5, .4]],
           [["pull", 1.25, 1.0, .5, .45], ["push", 1.15, 1.35, .6, .4], ["pan", 1.2, .7, .5, .3]],
           [["push", 1.0, 1.2, .4, .45], ["pull", 1.35, 1.1, .5, .4], ["pan", 1.2, .3, .55, .6]]]
    return ops[k]
def shot(e, idx, n, plano):
    out = f"{TMP}/{e:02d}_{idx}.mp4"
    if os.path.exists(out): return out
    t = plano[0]
    if t == "fijo": z, fx, fy = "1", .5, .5
    if t in ("push", "pull"):
        _, z0, z1, fx, fy = plano; z = f"{z0}+({z1}-{z0})*on/{n}"
    elif t == "pan":
        _, zz, fx0, fy, fx1 = plano; z = f"{zz}"; fx = f"({fx0}+({fx1}-{fx0})*on/{n})"
    elif t == "fijo": pass
    sh = "+8*sin(on/17)" if t != "fijo" else ""        # temblor de cámara muy suave
    sv = "+6*sin(on/23+1)" if t != "fijo" else ""
    x = f"max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2{sh}))"; y = f"max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2{sv}))"
    vf = (f"scale={SS}:{SS*9//16}:flags=lanczos,zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps={FPS},"
          f"vignette=PI/6,format=yuv420p")
    img = f"{V}/escenas/{e:02d}.png" if e != ultima else f"{V}/marca/pantalla_final_1920x1080.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", img, "-vf", vf, "-frames:v", str(n),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", out], check=True)
    return out
def clip(k):
    e, d = durs[k]; L = d + ((XS if (k + 1) in cambio else X) if k < len(durs) - 1 else 0)
    n = int(round(L * FPS)); out = f"{TMP}/{e:02d}.mp4"
    if os.path.exists(out): return out
    planos = [["fijo"]] if e == ultima else CAM.get(e) or por_defecto(e)
    m = len(planos); ns = [n // m] * m; ns[-1] = n - sum(ns[:-1])
    partes = [shot(e, i, ns[i], planos[i]) for i in range(m)]
    lst = f"{TMP}/{e:02d}.txt"; open(lst, "w").write("".join(f"file '{p}'\n" for p in partes))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out], check=True)
    return out
def ts(t): return f"{int(t//3600):02d}:{int(t%3600//60):02d}:{t%60:06.3f}".replace(".", ",")
def srt():
    cues, c = [], 1
    for b in tj:
        if b["inicio"] >= fin_t: continue               # sin subtítulos sobre la pantalla final
        frases = [f for f in re.split(r"(?<=[.!?:])\s+", b["texto"]) if f]
        trozos = []
        for f in frases:
            w = f.split()
            for i in range(0, len(w), 9): trozos.append(" ".join(w[i:i + 9]))
        tot = sum(len(t) for t in trozos); t0 = b["inicio"]; span = b["fin"] - b["inicio"]
        for t in trozos:
            d = span * len(t) / tot
            cues.append(f"{c}\n{ts(t0)} --> {ts(min(t0 + d, fin_t))}\n{t}\n"); c += 1; t0 += d
    open(f"{V}/subtitulos.srt", "w", encoding="utf-8").write("\n".join(cues))
if __name__ == "__main__":
    print(len(durs), "escenas, total", round(total, 1), "s; duración por escena:", [round(d) for _, d in durs], flush=True)
    if "--dry" in sys.argv: raise SystemExit
    with ThreadPoolExecutor(int(os.environ.get("HILOS", "4"))) as ex: clips = list(ex.map(clip, range(len(durs))))
    print("clips listos", flush=True); srt()
    ins = []
    for c in clips: ins += ["-i", c]
    ins += ["-i", AUD]
    fc, prev, S = [], "[0:v]", 0.0
    for k in range(len(durs) - 1):
        S += durs[k][1]; lab = f"[x{k}]"
        tr, dd = ("fadeblack", XS) if (k + 1) in cambio else ("fade", X)
        fc.append(f"{prev}[{k + 1}:v]xfade=transition={tr}:duration={dd}:offset={S:.3f}{lab}"); prev = lab
    fc.append(f"{prev}subtitles={V}/subtitulos.srt:force_style='FontName=DejaVu Sans,Bold=1,FontSize=17,Outline=2,Shadow=1,MarginV=36',format=yuv420p[v]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error"] + ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-map", f"{len(clips)}:a",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-c:v", "libx264", "-preset", "veryfast", "-crf", os.environ.get("CRF", "26"),
        "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", SAL], check=True)
    print("listo", SAL, flush=True)
