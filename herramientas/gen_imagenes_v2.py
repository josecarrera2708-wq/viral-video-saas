#!/usr/bin/env python3
"""Genera las 41 escenas en el estilo 'semi-realista' (v2). Uso: gen_imagenes_v2.py [nums...]  (sin args: las que falten)"""
import re, sys, os, json, base64, time, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{BASE}/guiones/musculo-paquete-chatgpt-01.md"
OUT = f"{BASE}/video/musculo-01/escenas_v2"; os.makedirs(OUT, exist_ok=True)
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, "
 "expressive detailed human characters with realistic proportions and emotional faces (use real-looking cartoon people, never plain white mannequins or stick figures), "
 "richly detailed environments with depth (gym, office, laboratory, factory, kitchen, bedroom), cinematic lighting, "
 "saturated but harmonious palette with teal, orange and warm skin tones, 16:9 widescreen, close-up or medium shot. "
 "Absolutely no text, no letters, no numbers, no logos, no watermarks, no captions anywhere in the image.")
txt = open(SRC, encoding="utf-8").read()
esc = {int(n): img.strip() for n, img in re.findall(r"\*\*ESCENA (\d+)\*\*\nLocución:.*?\nImagen: (.*?)\n", txt, re.S)}
nums = [int(a) for a in sys.argv[1:]] or sorted(esc)
for n in nums:
    f = f"{OUT}/{n:02d}.png"
    if os.path.exists(f) and len(sys.argv) == 1: continue
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\nScene (translate the idea, ignore any quoted text, show it visually instead): " + esc[n],
                       "size": "1536x864", "quality": "medium", "n": 1}).encode()
    for _ in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print(n, "ok", flush=True); break
        except Exception as e:
            print(n, "error", str(e)[:100], flush=True); time.sleep(14)
    time.sleep(14)
