import os, json, base64, time, urllib.request, sys
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = f"{BASE}/video/musculo-01/marca/mini"
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, expressive detailed human character with realistic proportions and a strong emotional face, "
          "cinematic lighting, saturated harmonious palette of teal, orange and warm skin tones, 16:9 YouTube thumbnail composition, very high contrast, subject large and instantly readable on a phone. "
          "Absolutely no text, no letters, no numbers, no logos, no watermarks.")
P = {
 "A": "Extreme close-up of a young muscular athlete in a black tank top, on the RIGHT 60% of the frame, frustrated and puzzled expression, one eyebrow raised, looking straight at the viewer while squeezing his flexed bicep that looks disappointingly small. Dark teal blurred gym background. The LEFT 40% of the frame is dark, simple and empty, left clear for big text.",
 "B": "Medium close-up of a young athlete in a black tank top on the RIGHT half, shocked wide-eyed face, hand on his chin, next to him a big round magnifier circle (right-top) showing thin weak muscle fibers with a glowing red cross mark. Dramatic orange rim light, dark teal gym background. The LEFT 45% of the frame is dark, simple and empty, left clear for big text.",
}
for k in sys.argv[1:] or P:
    f = f"{OUT}/{k}.png"
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\n" + P[k], "size": "1536x864", "quality": "high", "n": 1}).encode()
    for _ in range(6):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print(k, "ok", flush=True); break
        except Exception as e:
            print(k, "error", str(e)[:150], flush=True); time.sleep(14)
