#!/usr/bin/env python3
"""Pone la voz del canal (Cartesia, Ramon) a un short ya montado y la sincroniza con sus subtítulos quemados.
Uso:  python3 voz_short.py <video_in.mp4> <guion_short.txt> <video_out.mp4>
      python3 voz_short.py --subs <video_in.mp4>      (imprime cuándo cambia cada subtítulo quemado)
guion_short.txt: una línea por subtítulo:  `inicio_en_segundos | texto`  (o `+ texto` si sigue la misma frase)
  | = frase nueva (una toma de voz propia)      + = continúa la frase anterior: se genera junto a ella para
  mantener la entonación, se corta en la pausa y su trozo se coloca justo cuando aparece su subtítulo.
  Los números van en letras. Las líneas que empiezan por # se ignoran.
Cada frase se genera hasta con 3 tomas y se queda la que mejor coincide con el guion según whisper-1.
Si un trozo no cabe antes del siguiente subtítulo se acelera hasta un 10 %; si sobra mucho hueco se alarga hasta un 10 %;
si aun así queda una pausa de más de 0,6 s, el trozo siguiente se adelanta hasta 0,4 s respecto a su subtítulo.
El vídeo se copia sin recodificar; solo se cambia el audio. Voz sola, a -16 LUFS (igual que los vídeos largos) con margen de pico para el AAC.
Al terminar transcribe el audio final con whisper y avisa si falta o sobra algo del guion.
Variables: VOICE_ID, VOICE_SPEED (1.05), LEAD (0.12 s de retraso sobre el subtítulo), PAUSA_MAX (0.5), LUFS (-16), VOZ_TMP."""
import os, re, sys, wave, array, math, hashlib, difflib, unicodedata, subprocess, requests

VOICE = os.environ.get("VOICE_ID", "9b67072c-d46c-465d-87dc-f7a1c6db2bf3")
SPEED = float(os.environ.get("VOICE_SPEED", "1.05"))
LEAD = float(os.environ.get("LEAD", "0.12"))
PAUSA_MAX = float(os.environ.get("PAUSA_MAX", "0.5"))
LUFS = os.environ.get("LUFS", "-16")
TMP = os.environ.get("VOZ_TMP", "/tmp/voz_short")
GAP = 0.45          # si sobra más pausa que esto tras un trozo, se alarga un poco hasta dejarla en GAP (s)
MIN_GAP = 0.10      # pausa mínima tras un trozo; por debajo se acelera
MAX_FAST, MAX_SLOW = 1.10, 0.90
PAUSA_LARGA = 0.60  # pausa máxima aceptada con el trozo anterior; el siguiente se adelanta para acortarla
ADELANTO = 0.40     # cuánto puede adelantarse la voz respecto a su subtítulo
BREAK = "0.2s"      # pausa que se pide a Cartesia en los cortes (solo para tener un hueco limpio donde cortar)
NUMW = set('cero uno una un dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte veintiuno veintidos veintitres veinticuatro veinticinco treinta cuarenta cincuenta sesenta setenta ochenta noventa cien ciento doscientas doscientos trescientas cuatrocientas quinientas quinientos mil millon y coma primero segunda'.split())

def sh(*a):
    return subprocess.check_output(a, stderr=subprocess.STDOUT).decode()
def dur(f):
    return float(sh("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f))

def cambios_subs(video):
    """Instantes en que cambia el texto blanco de la franja de subtítulos (1/30 s de precisión)."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-vf",
        "crop=iw:240:0:ih*0.855,format=gray,lutyuv=y='if(gt(val,240),255,0)',select='gt(scene,0.004)',showinfo",
        "-an", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", out)]

def norm(s):
    s = re.sub(r"\d+", " ", s)
    s = unicodedata.normalize("NFD", s.lower()); s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z]+", s) if w not in NUMW]

def tts(t, speed, f):
    r = requests.post("https://api.cartesia.ai/tts/bytes", headers={"Cartesia-Version": "2025-04-16"},
        json={"model_id": "sonic-3", "transcript": t, "voice": {"mode": "id", "id": VOICE}, "language": "es",
              "generation_config": {"speed": speed}, "output_format": {"container": "mp3", "sample_rate": 44100, "bit_rate": 128000}})
    r.raise_for_status(); open(f, "wb").write(r.content)

def limpiar(f):
    """Mismo tratamiento que gen_voz.py: recorta silencio inicial, limita pausas largas y suaviza bordes."""
    g = f.replace(".mp3", "_c.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f, "-af",
        f"silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.06:stop_periods=-1:stop_duration=0.5:stop_threshold=-45dB:stop_silence={PAUSA_MAX},afade=t=in:d=0.012",
        "-ar", "44100", "-ac", "1", g], check=True)
    h = g.replace("_c.wav", "_f.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", g, "-af", f"afade=t=out:st={max(dur(g)-0.04, 0):.3f}:d=0.04", h], check=True)
    os.replace(h, g); return g

def stt(f):
    for _ in range(2):
        r = requests.post("https://api.openai.com/v1/audio/transcriptions", files={"file": open(f, "rb")},
                          data={"model": "whisper-1", "language": "es"}, timeout=120)
        if r.status_code == 200: return r.json()["text"]
    return ""

def diferencias(guion, texto):
    a, b = norm(guion), norm(texto)
    return sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes() if tag != "equal")

def huecos(f, min_len=0.15, umbral=-48):
    """Pausas interiores (inicio, fin) en s: tramos de energía baja que duran al menos min_len."""
    tmp = f + ".16k.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-ar", "16000", "-ac", "1", tmp], check=True)
    w = wave.open(tmp); a = array.array("h"); a.frombytes(w.readframes(w.getnframes())); w.close(); os.remove(tmp)
    env = [10 * math.log10(sum(x * x for x in a[i:i + 160]) / 160 / 32768 ** 2 + 1e-12) for i in range(0, len(a) - 160, 160)]
    runs, st = [], None
    for i, e in enumerate(env + [0]):
        if e < umbral:
            if st is None: st = i
        elif st is not None:
            runs.append([st * 0.01, i * 0.01]); st = None
    fus = []
    for r in runs:                       # une tramos separados por un pico de menos de 40 ms
        if fus and r[0] - fus[-1][1] < 0.04: fus[-1][1] = r[1]
        else: fus.append(r)
    fin = len(env) * 0.01
    return [(a0, b0) for a0, b0 in fus if b0 - a0 >= min_len and a0 > 0.02 and b0 < fin - 0.02]

def main():
    if sys.argv[1] == "--subs":
        print(" ".join(f"{x:.2f}" for x in cambios_subs(sys.argv[2]))); return
    video, guion, salida = sys.argv[1:4]
    os.makedirs(TMP, exist_ok=True)
    frases = []                          # [{"trozos": [(inicio, texto)]}]
    for l in open(guion, encoding="utf-8"):
        m = re.match(r"^\s*([\d.]+)\s*([|+])\s*(.+?)\s*$", l)
        if not m: continue
        t0, marca, txt = float(m.group(1)), m.group(2), m.group(3)
        if marca == "+" and frases: frases[-1].append((t0, txt))
        else: frases.append([(t0, txt)])
    total = dur(video)
    piezas = []                          # (inicio_subtitulo, wav, duracion)
    for i, fr in enumerate(frases):
        guion_txt = " ".join(t for _, t in fr)
        tts_txt = f' <break time="{BREAK}"/> '.join(t for _, t in fr)
        mejor = None
        for k, sp in enumerate([SPEED, 1.03, 1.07]):
            f = f"{TMP}/{hashlib.md5(f'{tts_txt}|{sp}|{VOICE}'.encode()).hexdigest()[:10]}.mp3"
            if not os.path.exists(f): tts(tts_txt, sp, f)
            g = limpiar(f); d = diferencias(guion_txt, stt(g))
            hz = sorted(sorted(huecos(g), key=lambda r: r[0] - r[1])[:len(fr) - 1])   # los cortes = las pausas más largas
            if len(hz) < len(fr) - 1: d += 10                                           # toma sin pausa donde cortar
            print(f"  frase {i} toma {k} (speed {sp}): {d} diferencias, {dur(g):.2f} s, cortes {[(round(a, 2), round(b, 2)) for a, b in hz]}", flush=True)
            if mejor is None or d < mejor[0]: mejor = (d, g, hz)
            if d == 0: break
        d, g, hz = mejor
        if d: print(f"  AVISO frase {i}: queda con {d} diferencias")
        if len(hz) < len(fr) - 1: raise SystemExit(f"frase {i}: no hay pausas donde cortar; separa las líneas con | en el guion")
        lim = [0.0] + [x for a, b in hz for x in (a + 0.05, b - 0.05)] + [dur(g)]
        for j, (t0, txt) in enumerate(fr):
            ini, fin = lim[2 * j], lim[2 * j + 1]
            p = f"{g[:-4]}_p{j}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", g, "-af",
                f"atrim=start={ini:.3f}:end={fin:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={max(fin - ini - 0.03, 0):.3f}:d=0.03", p], check=True)
            piezas.append((t0, txt, p, dur(p)))
    # colocación: cada trozo empieza con su subtítulo (+LEAD). Si queda una pausa larga con el trozo anterior,
    # arranca hasta ADELANTO s antes del subtítulo; si no cabe se acelera, y si sobra mucho hueco se alarga un poco.
    ent, filt, etiq, fin_prev = [], [], [], None
    for j, (t0, txt, p, d) in enumerate(piezas):
        ultimo = j + 1 == len(piezas)
        nxt = total - 0.2 if ultimo else piezas[j + 1][0] + LEAD
        ini = t0 + LEAD
        if fin_prev is not None:
            if ini - fin_prev > PAUSA_LARGA: ini = max(fin_prev + PAUSA_LARGA, t0 - ADELANTO)
            ini = max(ini, fin_prev + 0.05)
        pausa = nxt - (ini + d)
        a = 1.0
        if pausa < MIN_GAP: a = min(d / max(nxt - MIN_GAP - ini, 0.1), MAX_FAST)
        elif pausa > GAP and not ultimo: a = max(d / (nxt - GAP - ini), MAX_SLOW)
        fin = ini + d / a; fin_prev = fin
        nota = "  <-- NO CABE" if fin > nxt - 0.02 else ""
        print(f"  subtítulo {t0:5.2f}s '{txt[:34]}': voz {ini:.2f} -> {fin:.2f} s (desfase {ini - t0:+.2f}, tempo {a:.3f}, pausa {max(nxt - fin, 0):.2f}){nota}")
        ms = int(ini * 1000)
        ent += ["-i", p]
        filt.append(f"[{j}:a]" + (f"atempo={a:.4f}," if abs(a - 1) > 0.001 else "") + f"adelay={ms}|{ms}[a{j}]")
        etiq.append(f"[a{j}]")
    filt.append("".join(etiq) + f"amix=inputs={len(etiq)}:duration=longest:normalize=0,apad,atrim=0:{total},"
                f"loudnorm=I={LUFS}:TP=-2:LRA=11,aformat=sample_rates=44100:channel_layouts=mono[a]")
    voz = f"{TMP}/voz_short.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + ent + ["-filter_complex", ";".join(filt), "-map", "[a]", voz], check=True)
    texto_final = stt(voz); d = diferencias(" ".join(t for _, t, _, _ in piezas), texto_final)   # el audio final dice todo el guion?
    print("  comprobación final (whisper):", "OK, texto completo" if d == 0 else f"AVISO {d} diferencias -> '{texto_final}'")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", voz, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "128k", "-t", f"{total}", "-movflags", "+faststart", salida], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", voz, "-c:a", "libmp3lame", "-b:a", "128k", salida.rsplit(".", 1)[0] + "_voz.mp3"], check=True)
    print("ok ->", salida, f"({total:.2f} s)")

if __name__ == "__main__":
    main()
