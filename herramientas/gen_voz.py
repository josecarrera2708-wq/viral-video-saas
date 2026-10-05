import os, re, json, subprocess, requests, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("GUION", f"{BASE}/guiones/musculo-guion-02.md")
OUT = os.environ.get("OUT_DIR", f"{BASE}/video/musculo-01")
TMP = os.environ.get("VOZ_TMP", "/tmp/voz_partes")
VOICE = os.environ.get("VOICE_ID", "9b67072c-d46c-465d-87dc-f7a1c6db2bf3")
SPEED = float(os.environ.get("VOICE_SPEED", "1.05"))
PAUSA = 0.45
os.makedirs(TMP, exist_ok=True)
txt = open(SRC, encoding="utf-8").read()
secciones = re.split(r"\n## (\d+)\. .*\n", txt)[1:]
bloques = []  # (seccion, texto)
for i in range(0, len(secciones), 2):
    n = int(secciones[i]); cuerpo = secciones[i+1].split("\n---")[0]
    for p in re.split(r"\n\s*\n", cuerpo.strip()):
        p = " ".join(l.strip() for l in p.strip().splitlines())
        if p: bloques.append((n, p))
def tts(i, t):
    f = f"{TMP}/{i:03d}.mp3"
    if os.path.exists(f): return f
    for _ in range(4):
        r = requests.post("https://api.cartesia.ai/tts/bytes",
            headers={"Cartesia-Version": "2025-04-16"},
            json={"model_id": "sonic-3", "transcript": t, "voice": {"mode": "id", "id": VOICE}, "language": "es",
                  "generation_config": {"speed": SPEED},
                  "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}})
        if r.status_code == 200:
            open(f, "wb").write(r.content); return f
        print(i, r.status_code, r.text[:200], file=sys.stderr)
    raise SystemExit("fallo TTS")
def dur(f):
    return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]).decode())
print(len(bloques), "bloques", sum(len(t) for _, t in bloques), "caracteres")
if "--dry" in sys.argv: raise SystemExit
sil = f"{TMP}/sil.mp3"
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t",str(PAUSA),"-b:a","128k",sil],check=True)
t0, tiempos, lista = 0.0, [], []
for i, (n, t) in enumerate(bloques):
    f = tts(i, t); d = dur(f)
    tiempos.append({"seccion": n, "texto": t, "inicio": round(t0, 2), "fin": round(t0 + d, 2)})
    lista += [f, sil]; t0 += d + PAUSA
open(f"{TMP}/lista.txt", "w").write("".join(f"file '{x}'\n" for x in lista))
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","concat","-safe","0","-i",f"{TMP}/lista.txt","-c:a","libmp3lame","-b:a","128k",f"{OUT}/voz.mp3"],check=True)
json.dump(tiempos, open(f"{OUT}/tiempos.json","w"), ensure_ascii=False, indent=1)
print("duración total", round(t0/60, 2), "min")
