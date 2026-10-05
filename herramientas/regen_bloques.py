#!/usr/bin/env python3
"""Regenera bloques de voz con varias tomas (velocidad ligeramente distinta) y se queda con la que mejor coincide con el guion según whisper.
Uso: GUION=... VOZ_TMP=... regen_bloques.py 39 4 47"""
import os, sys, difflib, requests, shutil
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "revisar_voz.py")).read().split("solo = [int")[0]
ns = {"__file__": os.path.abspath(__file__)}; exec(src, ns)
bloques, norm, stt, TMP = ns["bloques"], ns["norm"], ns["stt"], ns["TMP"]
VOICE = os.environ.get("VOICE_ID", "9b67072c-d46c-465d-87dc-f7a1c6db2bf3")
def tts(t, speed):
    r = requests.post("https://api.cartesia.ai/tts/bytes", headers={"Cartesia-Version": "2025-04-16"},
        json={"model_id": "sonic-3", "transcript": t, "voice": {"mode": "id", "id": VOICE}, "language": "es",
              "generation_config": {"speed": speed}, "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}})
    r.raise_for_status(); return r.content
def score(i, f):
    a, b = norm(bloques[i]), norm(stt(f))
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if tag != "equal")
for i in map(int, sys.argv[1:]):
    f = f"{TMP}/{i:03d}.mp3"
    if not os.path.exists(f + ".orig"): shutil.copy(f, f + ".orig")
    mejor = (score(i, f + ".orig"), f + ".orig"); print(i, "original", mejor[0], flush=True)
    for k, sp in enumerate([1.05, 1.03, 1.07, 1.02]):
        if mejor[0] == 0: break
        g = f"{TMP}/{i:03d}_t{k}.mp3"
        try: open(g, "wb").write(tts(bloques[i], sp))
        except Exception as e: print("  tts error", str(e)[:80]); continue
        s = score(i, g); print("  toma", k, sp, "diferencias", s, flush=True)
        if s < mejor[0]: mejor = (s, g)
    shutil.copy(mejor[1], f); print("  ->", i, "queda con", os.path.basename(mejor[1]), "diferencias", mejor[0], flush=True)
