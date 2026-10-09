import os, json, base64, time, sys, urllib.request
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "video/lagartijas-01/marca")
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, expressive detailed human character with realistic proportions and a strong emotional face, "
          "cinematic lighting, saturated harmonious palette of teal, orange and warm skin tones, 16:9 YouTube thumbnail composition, very high contrast, subject large and instantly readable on a phone. "
          "The protagonist is always the same young Latino man with short dark hair and a black tank top. Absolutely no text, no letters, no numbers, no logos, no watermarks.")
P = {
 "A": "Split-screen before and after composition divided by a glowing vertical energy line in the middle. LEFT half: dark, desaturated, teal-gray tones, the protagonist in push-up position on a living room floor, thin arms, tired exhausted face. RIGHT half: bright warm orange tones, the same protagonist in the same push-up position, visibly much bigger muscular arms and shoulders, confident smirk looking at the viewer. Dramatic rim light, living room background.",
 "B": "Extreme close-up of the protagonist on the floor in push-up position, wide-eyed shocked amazed face looking at his own huge muscular arms, glowing orange energy around his arms, a giant glowing calendar page with a big glowing ring around it floating at the top right (no numbers on it), dark teal living room background, dramatic orange rim light. The LEFT 40% of the frame is darker and simpler, left clear for big text.",
}
for k in sys.argv[1:] or P:
    f = f"{OUT}/base_{k}.png"
    if os.path.exists(f): continue
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\n" + P[k], "size": "1536x864", "quality": "medium", "n": 1}).encode()
    for t in range(2):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print(k, "ok", flush=True); break
        except Exception as e:
            print(k, "error", str(e)[:100], flush=True); time.sleep(10)
