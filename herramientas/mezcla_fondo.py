#!/usr/bin/env python3
"""Voz + una sola pista de música de fondo (bajita, tipo relleno), sin tocar la voz.
Uso: python3 mezcla_fondo.py <voz.mp3> <musica> <salida.mp3>
Variables: MUS_LUFS (música sola, def. -27), DUCK (1 = baja la música mientras habla, def. 1), COLA (s de música tras la voz, def. 4), CRUCE (s de fundido entre repeticiones, def. 6).
La música se repite con fundido cruzado hasta cubrir el vídeo; máster en dos pasadas a -14 LUFS, pico -1,5 dBTP."""
import json, subprocess, sys, os, re, tempfile
voz, mus, out = sys.argv[1:4]
MUS_LUFS = float(os.environ.get("MUS_LUFS", -27)); COLA = float(os.environ.get("COLA", 4)); X = float(os.environ.get("CRUCE", 6)); DUCK = os.environ.get("DUCK", "1") == "1"
tmp = tempfile.mkdtemp()
def run(a): subprocess.run(["ffmpeg", "-v", "error", "-y"] + a, check=True)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
def lufs(f):
    o = subprocess.run(["ffmpeg", "-hide_banner", "-i", f, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", o)[-1])
total = dur(voz) + COLA; d = dur(mus); n = 1
while n * d - (n - 1) * X < total: n += 1
f = "[0:a]" + "".join(f"[{i}:a]acrossfade=d={X}[c{i}];[c{i}]" for i in range(1, n)); f = f.rsplit(";", 1)[0] if n > 1 else "[0:a]anull[c0]"
last = f"[c{n - 1}]" if n > 1 else "[c0]"
loop = f"{tmp}/loop.wav"
run(sum([["-i", mus] for _ in range(n)], []) + ["-filter_complex", f, "-map", last, "-t", f"{total:.2f}", "-ar", "44100", "-ac", "2", loop])
g = MUS_LUFS - lufs(loop)
cama = f"{tmp}/cama.wav"
run(["-i", loop, "-af", f"volume={g:.2f}dB,afade=t=in:d=2,afade=t=out:st={total - COLA:.2f}:d={COLA}", cama])
g_voz = -16 - lufs(voz)
duck = "[1:a][vsc]sidechaincompress=threshold=0.03:ratio=2.5:attack=30:release=500[mus]" if DUCK else "[1:a]anull[mus]"
filt = f"[0:a]aformat=channel_layouts=stereo,volume={g_voz:.2f}dB,apad=whole_dur={total:.2f},asplit=2[v1][vsc];{duck};[v1][mus]amix=inputs=2:duration=longest:normalize=0,atrim=0:{total:.2f},alimiter=limit=0.95:level=false[a]"
pre = f"{tmp}/pre.wav"
run(["-i", voz, "-i", cama, "-filter_complex", filt, "-map", "[a]", "-ar", "44100", pre])
o = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
m = json.loads(o[o.rindex("{"):o.rindex("}") + 1])
run(["-i", pre, "-af", f"loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}", "-ar", "44100", "-b:a", "192k", out])
print("ok", round(total / 60, 2), "min,", n, "repeticiones ->", out)
