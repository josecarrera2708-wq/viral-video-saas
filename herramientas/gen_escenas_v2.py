#!/usr/bin/env python3
"""Genera escenas con gpt-image-2 usando imágenes de referencia para que los personajes sean los mismos.
Uso: ESC=guiones/x-escenas.md OUT_DIR=carpeta QUALITY=medium python3 gen_escenas_v2.py [nums...]
Formato del .md: **ESCENA N** / Locución / Ref: none|host|md / Plano: ... / Imagen: ...
Ref host = personaje del canal (REF_HOST, def. pantalla final fondo); Ref md = Mateo y Diego (la escena REF_MD_ESC ya generada, def. 01).
Con referencia usa /images/edits; sin ella /images/generations. Máx. 2 intentos por imagen; se detiene si 2 imágenes seguidas fallan. No sobreescribe.
Escenas con Imagen: PANTALLA_FINAL se omiten (se montan aparte)."""
import re, sys, os, json, base64, time, requests
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("ESC", f"{BASE}/guiones/frecuencia-escenas-01.md")
OUT = os.environ.get("OUT_DIR", f"{BASE}/video/frecuencia-01/escenas"); os.makedirs(OUT, exist_ok=True)
Q = os.environ.get("QUALITY", "medium"); SUF = os.environ.get("SUFIJO", "")
REF_HOST = os.environ.get("REF_HOST", f"{BASE}/video/frecuencia-01/marca/pantalla_final_fondo.png")
REF_MD = f"{OUT}/{int(os.environ.get('REF_MD_ESC', 1)):02d}.png"
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, "
 "expressive detailed human characters with realistic proportions and emotional faces (real-looking cartoon people, never plain white mannequins or stick figures), "
 "richly detailed environments with depth, cinematic lighting and camera work, saturated but harmonious palette with teal, orange and warm skin tones, 16:9 widescreen. "
 "Absolutely no text, no letters, no numbers, no logos, no watermarks, no captions anywhere in the image; signs, boards, screens and papers show only abstract shapes or icons.")
txt = open(SRC, encoding="utf-8").read()
esc = {}
for n, ref, plano, img in re.findall(r"\*\*ESCENA (\d+)\*\*\nLocución:.*?\nRef: (.*?)\nPlano: (.*?)\nImagen: (.*?)\n", txt, re.S): esc[int(n)] = (ref.strip(), plano.strip(), img.strip())
nums = [int(a) for a in sys.argv[1:]] or sorted(esc)
def llamar(prompt, refs):
    if refs:
        files = [("image[]", (os.path.basename(p), open(p, "rb"), "image/png")) for p in refs]
        r = requests.post("https://api.openai.com/v1/images/edits", data={"model": "gpt-image-2", "prompt": prompt, "size": "1536x864", "quality": Q, "n": "1"}, files=files, timeout=300)
    else:
        r = requests.post("https://api.openai.com/v1/images/generations", json={"model": "gpt-image-2", "prompt": prompt, "size": "1536x864", "quality": Q, "n": 1}, timeout=300)
    if r.status_code != 200: raise RuntimeError(f"{r.status_code} {r.text[:150]}")
    return base64.b64decode(r.json()["data"][0]["b64_json"])
fallos = 0; hechas = 0
for n in nums:
    ref, plano, img = esc[n]
    f = f"{OUT}/{n:02d}{SUF}.png"
    if os.path.exists(f) or img == "PANTALLA_FINAL": continue
    refs = {"host": [REF_HOST], "md": [REF_MD], "none": []}[ref]
    if any(not os.path.exists(p) for p in refs): print(n, "falta la referencia", refs); continue
    pre = ("The attached reference image shows the recurring character(s) of this channel. Keep their exact face, hairstyle, skin tone, body type, clothing and art style, "
           "but create a completely NEW scene, composition and camera angle as described below (do not copy the reference's pose or background).\n\n") if refs else ""
    prompt = pre + ESTILO + f"\n\nCamera: {plano}.\nScene: {img}"
    ok = False
    for intento in range(2):
        try:
            open(f + ".tmp", "wb").write(llamar(prompt, refs)); os.replace(f + ".tmp", f); ok = True; hechas += 1; print(n, Q, "ok", "(ref)" if refs else "", flush=True); break
        except Exception as e:
            print(n, "error", str(e)[:160], flush=True); time.sleep(10)
    fallos = 0 if ok else fallos + 1
    if fallos >= 2: print("PARADO: 2 imágenes seguidas fallaron"); break
    time.sleep(4)
print("generadas:", hechas)
