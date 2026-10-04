import os, sys, json, base64, time, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{BASE}/video/musculo-01/prueba_estilo"
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, "
 "expressive detailed human characters with realistic proportions and emotional faces, richly detailed environments with depth "
 "(gym, office, laboratory, factory), cinematic lighting, saturated but harmonious palette with teal, orange and warm skin tones, "
 "16:9 widescreen, close-up or medium shot. No logos, no watermarks, no subtitles, no captions, no text anywhere in the image.")
ESC = {
 "01": "A tired young Latino man in a gym looking at himself in a big mirror, frustrated, a heavy barbell behind him; his arms look exactly the same as months ago; a big red X floats over the mirror.",
 "05": "Dramatic medical cross-section of a muscle fiber thickening, glowing mint-green protein filaments appearing inside it, arrows pointing outward, dark blue lab background.",
 "06": "A busy factory interior with a conveyor belt and workers building muscle-shaped parts, a mailbox on the left with an order slip going in, warm industrial light.",
 "24": "A smiling female nutritionist in a green blazer in a bright kitchen pointing at a plate of grilled chicken, rice and vegetables next to a kitchen scale showing 80 kg, friendly expression.",
}
for k, p in ESC.items():
    f = f"{OUT}/{k}.png"
    if os.path.exists(f): continue
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\nScene: " + p, "size": "1536x864", "quality": "medium", "n": 1}).encode()
    for _ in range(5):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print(k, "ok"); break
        except Exception as e:
            print(k, "error", str(e)[:120]); time.sleep(14)
    time.sleep(14)
