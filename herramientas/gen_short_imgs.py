#!/usr/bin/env python3
"""Genera las tomas verticales de un Short con gpt-image-2 (edición con imagen de referencia para que el personaje sea el del canal).
Uso: python3 gen_short_imgs.py <escenas.json> <salida_dir> <referencia.png> [ids...]   Variables: QUALITY (medium), SIZE (1152x2048)
Máx. 2 reintentos por imagen; 2 fallos seguidos detienen todo. No sobreescribe lo que existe."""
import sys, os, json, base64, time, requests
J, OUT, REF = sys.argv[1:4]; ids = [int(a) for a in sys.argv[4:]]
Q = os.environ.get("QUALITY", "medium"); SIZE = os.environ.get("SIZE", "1152x2048")
d = json.load(open(J, encoding="utf-8")); os.makedirs(OUT, exist_ok=True); fallos = 0
for t in d["tomas"]:
    if ids and t["id"] not in ids: continue
    f = f"{OUT}/{t['id']:02d}.png"
    if os.path.exists(f): continue
    prompt = d["estilo"] + "\n\n" + (d["host"] + "\n\n" if t["ref"] else "") + "Scene: " + t["prompt"]
    ok = False
    for intento in range(2):
        try:
            if t["ref"]:
                r = requests.post("https://api.openai.com/v1/images/edits", files={"image[]": ("ref.png", open(REF, "rb"), "image/png")},
                                  data={"model": "gpt-image-2", "prompt": prompt, "size": SIZE, "quality": Q, "n": "1"}, timeout=240)
            else:
                r = requests.post("https://api.openai.com/v1/images/generations", json={"model": "gpt-image-2", "prompt": prompt, "size": SIZE, "quality": Q, "n": 1}, timeout=240)
            if r.status_code != 200: raise RuntimeError(f"{r.status_code} {r.text[:150]}")
            open(f, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"])); ok = True; print(t["id"], "ok", flush=True); break
        except Exception as e:
            print(t["id"], "error", str(e)[:200], flush=True); time.sleep(8)
    fallos = 0 if ok else fallos + 1
    if fallos >= 2: print("PARADO: 2 fallos seguidos"); break
    time.sleep(6)
