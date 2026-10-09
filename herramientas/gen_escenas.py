#!/usr/bin/env python3
"""Genera escenas con gpt-image-2. Uso: ESC=archivo.md OUT_DIR=carpeta QUALITY=medium gen_escenas.py [nums...]
Máx. 2 reintentos por imagen; si 2 imágenes seguidas fallan, se detiene (para no gastar). No sobreescribe lo que ya existe."""
import re, sys, os, json, base64, time, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("ESC", f"{BASE}/guiones/lagartijas-escenas-01.md")
OUT = os.environ.get("OUT_DIR", f"{BASE}/video/lagartijas-01/escenas"); os.makedirs(OUT, exist_ok=True)
Q = os.environ.get("QUALITY", "medium"); SUF = os.environ.get("SUFIJO", "")
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, "
 "expressive detailed human characters with realistic proportions and emotional faces (use real-looking cartoon people, never plain white mannequins or stick figures), "
 "richly detailed environments with depth (gym, living room, bedroom, kitchen), cinematic lighting, "
 "saturated but harmonious palette with teal, orange and warm skin tones, 16:9 widescreen, close-up or medium shot. "
 "Absolutely no text, no letters, no numbers, no logos, no watermarks, no captions anywhere in the image.")
txt = open(SRC, encoding="utf-8").read()
esc = {int(n): img.strip() for n, img in re.findall(r"\*\*ESCENA (\d+)\*\*\nLocución:.*?\nImagen: (.*?)\n", txt, re.S)}
nums = [int(a) for a in sys.argv[1:]] or sorted(esc)
fallos = 0; hechas = 0
for n in nums:
    f = f"{OUT}/{n:02d}{SUF}.png"
    if os.path.exists(f): continue
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\nScene: " + esc[n], "size": "1536x864", "quality": Q, "n": 1}).encode()
    ok = False
    for intento in range(2):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); ok = True; hechas += 1; print(n, Q, "ok", flush=True); break
        except Exception as e:
            print(n, "error", str(e)[:120], flush=True); time.sleep(10)
    fallos = 0 if ok else fallos + 1
    if fallos >= 2: print("PARADO: 2 imágenes seguidas fallaron"); break
    time.sleep(12)
print("generadas:", hechas)
