#!/usr/bin/env python3
"""Genera las imágenes de las escenas desde guiones/musculo-paquete-chatgpt-01.md con la API de OpenAI.
Uso: gen_imagenes.py [nums...]   (sin args: todas las que falten)"""
import re, sys, os, json, base64, urllib.request, concurrent.futures as cf
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{BASE}/guiones/musculo-paquete-chatgpt-01.md"
OUT = f"{BASE}/video/musculo-01/escenas"
MODEL = os.environ.get("IMG_MODEL", "gpt-image-2")
SIZE = os.environ.get("IMG_SIZE", "1536x864")
QUALITY = os.environ.get("IMG_QUALITY", "medium")
txt = open(SRC, encoding="utf-8").read()
estilo = re.search(r"### ESTILO FIJO.*?\n(.*?)\n###", txt, re.S).group(1).strip()
escenas = {int(n): img.strip() for n, img in re.findall(r"\*\*ESCENA (\d+)\*\*\nLocución:.*?\nImagen: (.*?)\n", txt, re.S)}
def gen(n):
    path = f"{OUT}/{n:02d}.png"
    prompt = f"{estilo}\n\nEscena: {escenas[n]}"
    body = json.dumps({"model": MODEL, "prompt": prompt, "size": SIZE, "quality": QUALITY, "n": 1}).encode()
    for intento in range(6):
        try:
            req = urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=300))
            open(path, "wb").write(base64.b64decode(r["data"][0]["b64_json"]))
            return n, "ok"
        except Exception as e:
            import time; time.sleep(14)
            err = getattr(e, "read", lambda: b"")().decode()[:300] or str(e)
    return n, "ERROR " + err
nums = [int(a) for a in sys.argv[1:]] or [n for n in sorted(escenas) if not os.path.exists(f"{OUT}/{n:02d}.png")]
with cf.ThreadPoolExecutor(1) as ex:
    for n, s in ex.map(gen, nums): print(n, s, flush=True)
