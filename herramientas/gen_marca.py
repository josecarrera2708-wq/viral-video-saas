import os, json, base64, time, urllib.request, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{BASE}/video/musculo-01/marca"
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, expressive detailed characters, "
          "cinematic lighting, saturated harmonious palette of teal, orange and warm tones. Absolutely no text, no letters, no numbers, no logos, no watermarks.")
P = {
 "miniatura_base": ("1536x864", "Dramatic composition. LEFT HALF: a young athlete in a black tank top in a dark gym, looking intensely at his own flexed bicep with a glowing orange spot on it. RIGHT THIRD: two round magnifier circles stacked vertically showing muscle fibers: the top circle shows thin sparse fibers with a red cross mark, the bottom circle shows thick dense fibers with glowing mint filaments and a green check mark. The TOP-LEFT and CENTER-LEFT area behind the athlete's head stays darker and simple so big text can be added over it later."),
 "perfil_base": ("1024x1024", "Circular badge emblem, centered, symmetrical: a stylized muscle fiber and a double-helix DNA strand wrapped around a dumbbell, teal and orange, dark teal background, bold clean shapes, simple enough to read at tiny size."),
 "portada_base": ("1536x864", "Ultra-wide cinematic banner scene: on the far LEFT a muscular athlete lifting a barbell in a moody gym, on the far RIGHT a glowing anatomical muscle fiber cross-section with mint-green filaments; the CENTER is calm dark teal gradient with soft light rays and nothing important, left clear for a channel name. Wide horizontal composition."),
}
for k in sys.argv[1:] or P:
    f = f"{OUT}/{k}.png"
    if os.path.exists(f): continue
    size, p = P[k]
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\n" + p, "size": size, "quality": "high", "n": 1}).encode()
    for _ in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print(k, "ok", flush=True); break
        except Exception as e:
            print(k, "error", str(e)[:100], flush=True); time.sleep(14)
    time.sleep(14)
