import os, re, json, math, subprocess, requests, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("GUION", f"{BASE}/guiones/musculo-guion-02.md")
OUT = os.environ.get("OUT_DIR", f"{BASE}/video/musculo-01")
TMP = os.environ.get("VOZ_TMP", "/tmp/voz_partes")
VOICE = os.environ.get("VOICE_ID", "9b67072c-d46c-465d-87dc-f7a1c6db2bf3")
MODEL = os.environ.get("MODEL", "sonic-3")
PAUSA_SECCION = float(os.environ.get("PAUSA_SECCION", "0"))  # pausa extra al cambiar de sección (s)
SPEED = float(os.environ.get("VOICE_SPEED", "1.05"))
PAUSA = float(os.environ.get("PAUSA", "0.55"))
PAUSA_MAX = float(os.environ.get("PAUSA_MAX", "0.4"))  # tope de pausa interna (s)
BEAT = float(os.environ.get("BEAT", "0"))  # periodo del pulso de la música (s, tiempo FINAL); con rejilla cada frase arranca en un pulso. 0 = sin rejilla
BAR = int(os.environ.get("BAR", "4"))  # pulsos por compás: las secciones nuevas arrancan en el primer pulso de un compás
PAUSA_MIN = float(os.environ.get("PAUSA_MIN", "0.2"))  # con rejilla: pausa mínima entre frases (s, tiempo final)
PAUSA_SECCION_MIN = float(os.environ.get("PAUSA_SECCION_MIN", "0.5"))  # con rejilla: pausa mínima al cambiar de sección
VOZ_AF = os.environ.get("VOZ_AF", "")  # filtros ffmpeg para la voz antes del atempo (tono, ecualización...)
ATEMPO = float(os.environ.get("ATEMPO", "1.0"))  # aceleración final de toda la voz sin cambiar el tono (sonic-3.5 ignora speed); los tiempos se reescalan
os.makedirs(TMP, exist_ok=True)
txt = open(SRC, encoding="utf-8").read()
secciones = re.split(r"\n## (\d+)\. .*\n", txt)[1:]
bloques = []  # (seccion, texto)
for i in range(0, len(secciones), 2):
    n = int(secciones[i]); cuerpo = secciones[i+1].split("\n---")[0]
    for p in re.split(r"\n\s*\n", cuerpo.strip()):
        p = " ".join(l.strip() for l in p.strip().splitlines())
        if p: bloques.append((n, p))
PRONUNCIA = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pronuncia.json"), encoding="utf-8")) if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pronuncia.json")) else {}
def fonetica(t):
    """Sustituye nombres extranjeros por su pronunciación (solo para la voz; el guion y los subtítulos no cambian)."""
    for a, b in PRONUNCIA.items(): t = t.replace(a, b)
    return t
def tts(i, t):
    f = f"{TMP}/{i:03d}.mp3"
    if os.path.exists(f): return f
    for _ in range(4):
        r = requests.post("https://api.cartesia.ai/tts/bytes",
            headers={"Cartesia-Version": "2025-04-16"},
            json={"model_id": MODEL, "transcript": fonetica(t), "voice": {"mode": "id", "id": VOICE}, "language": "es",
                  "generation_config": {"speed": SPEED, **({"emotion": os.environ["EMOTION"]} if os.environ.get("EMOTION") else {})},
                  "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}})
        if r.status_code == 200:
            open(f, "wb").write(r.content); return f
        print(i, r.status_code, r.text[:200], file=sys.stderr)
    raise SystemExit("fallo TTS")
def limpiar(f):
    """Recorta silencio inicial, limita pausas internas largas y suaviza bordes (evita saltos/cortes secos)."""
    g = f.replace(".mp3", "_c.wav")
    if os.path.exists(g) and os.path.getmtime(g) >= os.path.getmtime(f): return g
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f,"-af",
        f"silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06:stop_periods=-1:stop_duration=0.5:stop_threshold=-45dB:stop_silence={PAUSA_MAX},afade=t=in:d=0.012",
        "-ar","44100","-ac","1",g],check=True)
    d = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",g]).decode())
    h = g.replace("_c.wav","_f.wav")
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",g,"-af",f"afade=t=out:st={max(d-0.04,0):.3f}:d=0.04",h],check=True)
    os.replace(h, g); return g
def dur(f):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode())
print(len(bloques), "bloques", sum(len(t) for _, t in bloques), "caracteres")
if "--dry" in sys.argv: raise SystemExit
import concurrent.futures as cf
with cf.ThreadPoolExecutor(4) as ex: list(ex.map(lambda a: tts(*a), [(i, t) for i, (n, t) in enumerate(bloques)]))
sil = f"{TMP}/sil.wav"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t",str(PAUSA),"-ar","44100",sil],check=True)
silsec = f"{TMP}/silsec.wav"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t",str(max(PAUSA_SECCION,0.01)),"-ar","44100",silsec],check=True)
t0, tiempos, lista = 0.0, [], []
def silencio(seg):
    f = f"{TMP}/s_{int(round(seg*1000)):06d}.wav"
    if not os.path.exists(f):
        subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t",f"{seg:.4f}","-ar","44100",f],check=True)
    return f
for i, (n, t) in enumerate(bloques):
    f = limpiar(tts(i, t)); d = dur(f)
    if BEAT:   # rejilla: la frase arranca en el siguiente pulso (o primer pulso de compás si abre sección), respetando la pausa mínima
        nueva = i and n != bloques[i-1][0]
        if i:
            minimo = t0 / ATEMPO + (PAUSA_SECCION_MIN if nueva else PAUSA_MIN)
            malla = BEAT * BAR if nueva else BEAT
            ini_f = math.ceil(minimo / malla - 1e-9) * malla
            hueco = ini_f * ATEMPO - t0
            if hueco > 0.001: lista.append(silencio(hueco)); t0 += hueco
    elif PAUSA_SECCION and i and n != bloques[i-1][0]:
        lista.append(silsec); t0 += PAUSA_SECCION
    tiempos.append({"seccion": n, "texto": t, "inicio": round(t0, 2), "fin": round(t0 + d, 2)})
    lista.append(f); t0 += d
    if not BEAT: lista.append(sil); t0 += PAUSA
open(f"{TMP}/lista.txt", "w").write("".join(f"file '{x}'\n" for x in lista))
cadena = ",".join(x for x in [VOZ_AF, f"atempo={ATEMPO}" if ATEMPO != 1.0 else ""] if x)
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{TMP}/lista.txt"] + (["-af", cadena] if cadena else []) + ["-c:a","libmp3lame","-b:a","128k",f"{OUT}/voz.mp3"],check=True)
if ATEMPO != 1.0:
    for x in tiempos: x["inicio"] = round(x["inicio"] / ATEMPO, 2); x["fin"] = round(x["fin"] / ATEMPO, 2)
    t0 /= ATEMPO
json.dump(tiempos, open(f"{OUT}/tiempos.json","w"), ensure_ascii=False, indent=1)
print("duración total", round(t0/60, 2), "min", f"(atempo {ATEMPO})" if ATEMPO != 1.0 else "")
