#!/usr/bin/env python3
"""Transcribe cada bloque de voz con whisper-1 y lo compara con el guion para detectar pronunciaciones raras.
Uso: GUION=... VOZ_TMP=... revisar_voz.py   (imprime los bloques con coincidencia baja)"""
import os, re, json, sys, difflib, requests, unicodedata, concurrent.futures as cf
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("GUION", f"{BASE}/guiones/lagartijas-guion-01.md"); TMP = os.environ.get("VOZ_TMP", "/tmp/voz_lag")
txt = open(SRC, encoding="utf-8").read()
sec = re.split(r"\n## (\d+)\. .*\n", txt)[1:]; bloques = []
for i in range(0, len(sec), 2):
    for p in re.split(r"\n\s*\n", sec[i+1].split("\n---")[0].strip()):
        p = " ".join(l.strip() for l in p.strip().splitlines())
        if p: bloques.append(p)
NUMW = set('cero uno una un dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco treinta cuarenta cincuenta sesenta setenta ochenta noventa cien ciento doscientas doscientos trescientas cuatrocientas quinientas quinientos mil millon y coma primero segunda'.split())
def norm(s):
    s = re.sub(r"\d+", " ", s)
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z]+", s) if w not in NUMW]
def stt(f):
    for _ in range(2):
        r = requests.post("https://api.openai.com/v1/audio/transcriptions", files={"file": open(f, "rb")}, data={"model": "whisper-1", "language": "es"}, timeout=120)
        if r.status_code == 200: return r.json()["text"]
    return ""
def un(i):
    f = f"{TMP}/{i:03d}.mp3"; t = stt(f); a, b = norm(bloques[i]), norm(t)
    sm = difflib.SequenceMatcher(None, a, b)
    falt = sum(i2 - i1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("delete", "replace"))
    return i, 1 - falt / max(len(a), 1), t
solo = [int(x) for x in sys.argv[1:]]
with cf.ThreadPoolExecutor(4) as ex:
    res = sorted(ex.map(un, solo or range(len(bloques))))
json.dump({i: (round(r, 2), t) for i, r, t in res}, open(f"{TMP}/revision.json", "w"), ensure_ascii=False, indent=1)
for i, r, t in res:
    if r < 0.94: print(i, round(r, 2), "\n  GUION:", bloques[i][:160], "\n  VOZ  :", t[:160])
print("revisados", len(res), "bajos", sum(1 for _, r, _ in res if r < 0.94))
