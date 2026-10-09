#!/usr/bin/env python3
"""Monta un Short vertical 1080x1920 a partir de tomas fijas: cámara con keyframes y suavizado, vibración de mano, fundidos rápidos,
destellos, subtítulos karaoke (palabra activa en naranja), título gancho, botón final, barra de progreso, viñeta y grano; sonido con
whooshes/impactos sobre voz+música.
Uso: python3 montar_short_pro.py <montaje.json> <tomas_dir> <voz.mp3> <palabras.json> <musica> <salida.mp4>"""
import sys, os, json, subprocess, math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
MON, TOM, VOZ, PAL, MUS, OUT = sys.argv[1:7]
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = f"{BASE}/herramientas/Anton-Regular.ttf"; SFX = f"{BASE}/kits/05-kit-editor-video/assets/sfx"
W, H, FPS = 1080, 1920, 30; ORA = (255, 138, 31); BLA = (255, 255, 255)
m = json.load(open(MON, encoding="utf-8")); DUR = m["dur"]; N = int(DUR * FPS)
tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"), "short_pro"); os.makedirs(tmp, exist_ok=True)
imgs = {}
def img(i):
    if i not in imgs: imgs[i] = cv2.cvtColor(cv2.imread(f"{TOM}/{i:02d}.png"), cv2.COLOR_BGR2RGB)
    return imgs[i]
def ss(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def cam(p, t):
    kf = p["kf"]
    if t <= kf[0][0]: z, cx, cy = kf[0][1:]
    elif t >= kf[-1][0]: z, cx, cy = kf[-1][1:]
    else:
        for a, b in zip(kf, kf[1:]):
            if a[0] <= t <= b[0]:
                k = ss((t - a[0]) / (b[0] - a[0])); z, cx, cy = [a[j] + (b[j] - a[j]) * k for j in (1, 2, 3)]; break
    s = p.get("shake", 0)
    if s:   # vibración de cámara en mano: senos lentos incommensurables
        cx += s * 0.0012 * (math.sin(t * 2.3) + 0.6 * math.sin(t * 5.1 + 1)); cy += s * 0.0012 * (math.sin(t * 1.9 + 2) + 0.6 * math.sin(t * 4.3))
        z *= 1 + s * 0.0015 * math.sin(t * 1.3)
    return z, cx, cy
def render_shot(p, t):
    im = img(p["toma"]); h, w = im.shape[:2]; z, cx, cy = cam(p, t)
    cx = min(max(cx, 0.5 / z), 1 - 0.5 / z); cy = min(max(cy, 0.5 / z), 1 - 0.5 / z)
    s = W / (w / z); M = np.float32([[s, 0, W / 2 - s * cx * w], [0, s, H / 2 - s * cy * h]])
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
def font(sz): return ImageFont.truetype(FONT, sz)
def sprite_lineas(lineas, sz, colores, y_gap=0.05, stroke=12):
    """lineas: lista de listas de (palabra, color). Devuelve RGBA centrada."""
    f = font(sz); d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    anchos = []
    for ln in lineas:
        x = 0; seg = []
        for w_, c in ln:
            a = d0.textlength(w_ + " ", font=f); seg.append((w_, c, x)); x += a
        anchos.append((seg, x - d0.textlength(" ", font=f)))
    lh = int(sz * 1.18); im = Image.new("RGBA", (W, lh * len(lineas) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, (seg, tw) in enumerate(anchos):
        x0 = (W - tw) / 2
        for w_, c, x in seg:
            d.text((x0 + x + 4, 30 + i * lh + 7), w_, font=f, fill=(0, 0, 0, 170), stroke_width=stroke, stroke_fill=(0, 0, 0, 170))
            d.text((x0 + x, 30 + i * lh), w_, font=f, fill=c + (255,), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return np.array(im)
# ---- subtítulos karaoke
fix = m.get("palabras_fix", {}); pal = json.load(open(PAL, encoding="utf-8")); words = []
for w_ in pal:
    t = w_["word"].strip().strip("¿¡"); t = fix.get(t.lower().strip(".,?!"), t) if t.lower().strip(".,?!") in fix else t
    words.append({"t": t.upper(), "s": w_["start"], "e": w_["end"]})
for i in range(len(words) - 1):    # whisper a veces da inicios repetidos: asegura orden y duración mínima
    if words[i + 1]["s"] < words[i]["s"] + 0.12: words[i + 1]["s"] = words[i]["s"] + 0.12
    words[i]["e"] = min(max(words[i]["e"], words[i]["s"] + 0.12), words[i + 1]["s"])
groups = []; cur = []
for w_ in words:
    cur.append(w_)
    if len(cur) >= 3 or w_["t"][-1] in ".?!" or w_["t"][-1] == ",":
        groups.append(cur); cur = []
if cur: groups.append(cur)
spr = {}
def sub_sprite(gi, ai):
    k = (gi, ai)
    if k not in spr:
        g = groups[gi]; txt = " ".join(x["t"] for x in g); sz = 104 if len(txt) < 18 else 92
        spr[k] = sprite_lineas([[(x["t"], ORA if j == ai else BLA) for j, x in enumerate(g)]], sz, None)
    return spr[k]
def overlay(frame, sp, y, a=1.0, sc=1.0):
    if sc != 1.0: sp = cv2.resize(sp, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
    h, w = sp.shape[:2]; x0 = (W - w) // 2; y0 = int(y - h / 2)
    xs, ys = max(x0, 0), max(y0, 0); xe, ye = min(x0 + w, W), min(y0 + h, H)
    if xe <= xs or ye <= ys: return
    s = sp[ys - y0:ye - y0, xs - x0:xe - x0].astype(np.float32); al = s[..., 3:4] / 255.0 * a
    frame[ys:ye, xs:xe] = (frame[ys:ye, xs:xe] * (1 - al) + s[..., :3] * al).astype(np.uint8)
# ---- título y botón
T = m["titulo"]; res = set(T.get("resalta", []))
titulo = sprite_lineas([[(w_, ORA if w_ in res else BLA) for w_ in ln.split()] for ln in T["lineas"]], 118, None, stroke=14)
def boton(txt):
    f = font(58); d0 = ImageDraw.Draw(Image.new("RGBA", (10, 10))); tw = d0.textlength(txt, font=f)
    bw, bh = int(tw + 150), 120; im = Image.new("RGBA", (W, bh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x0 = (W - bw) // 2
    d.rounded_rectangle((x0 + 5, 25, x0 + bw + 5, 25 + bh), 60, fill=(0, 0, 0, 150))
    d.rounded_rectangle((x0, 20, x0 + bw, 20 + bh), 60, fill=ORA + (255,))
    cy = 20 + bh // 2; d.polygon([(x0 + 38, cy - 24), (x0 + 38, cy + 24), (x0 + 80, cy)], fill=(20, 20, 20, 255))
    d.text((x0 + 105, cy), txt, font=f, fill=(20, 20, 20, 255), anchor="lm"); return np.array(im)
BTN = boton(m["cta"]["texto"])
# ---- viñeta, grano
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
VIN = (1 - 0.38 * np.clip(r - 0.55, 0, 1) ** 1.5)[..., None].astype(np.float32)
rng = np.random.default_rng(7); GR = [rng.normal(0, 3, (H, W, 1)).astype(np.float32) for _ in range(6)]
plano = m["plano"]; TR = 0.2
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "23", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p", f"{tmp}/v.mp4"], stdin=subprocess.PIPE)
for n in range(N):
    t = n / FPS; k = max(i for i, p in enumerate(plano) if p["ini"] <= t + 1e-6)
    fr = render_shot(plano[k], t).astype(np.float32)
    if k + 1 < len(plano) and t > plano[k + 1]["ini"] - TR:   # fundido de salida hacia la siguiente toma (la siguiente entra con zoom)
        a = ss((t - (plano[k + 1]["ini"] - TR)) / TR); fr = fr * (1 - a) + render_shot(plano[k + 1], t).astype(np.float32) * a
    f0 = plano[k]
    for p in plano[1:]:      # destello en los cortes marcados
        if p.get("flash") and 0 <= t - p["ini"] < 0.14: fr = fr + (1 - (t - p["ini"]) / 0.14) * 70
    fr = (fr - 128) * 1.07 + 128; fr = fr * VIN + GR[n % 6]
    fr = np.clip(fr, 0, 255).astype(np.uint8)
    if T["ini"] <= t < T["fin"]:
        a = min(ss((t - T["ini"]) / 0.18), ss((T["fin"] - t) / 0.2)); overlay(fr, titulo, 400, a, 0.88 + 0.12 * ss((t - T["ini"]) / 0.2))
    for gi, g in enumerate(groups):
        fin = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else g[-1]["e"] + 0.3
        if g[0]["s"] <= t < min(fin, g[-1]["e"] + 0.4):
            ai = max([j for j, x in enumerate(g) if x["s"] <= t] or [0]); pop = 0.9 + 0.1 * ss((t - g[0]["s"]) / 0.1)
            overlay(fr, sub_sprite(gi, ai), 1290, 1.0, pop); break
    if t >= m["cta"]["ini"]:
        a = ss((t - m["cta"]["ini"]) / 0.25); overlay(fr, BTN, 1530, a, (0.9 + 0.1 * a) * (1 + 0.035 * math.sin((t - m["cta"]["ini"]) * 6)))
    fr[:10, :int(W * t / DUR)] = ORA
    ff.stdin.write(fr.tobytes())
ff.stdin.close(); ff.wait()
# ---- audio: voz + música (mezcla_fondo) y efectos
env = dict(os.environ, COLA=str(round(DUR - float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", VOZ], capture_output=True, text=True).stdout), 2)), MUS_LUFS="-26")
subprocess.run(["python3", f"{BASE}/herramientas/mezcla_fondo.py", VOZ, MUS, f"{tmp}/base.mp3"], check=True, env=env)
ins = ["-i", f"{tmp}/base.mp3"]; fl = []; mix = ["[0:a]"]; j = 1
fx = [(p["ini"] - 0.12, p["sfx"]) for p in plano[1:] if p.get("sfx")] + [(m["cta"]["ini"], "pop.mp3")]
for t0, nombre in fx:
    ins += ["-i", f"{SFX}/{nombre}"]; ms = int(max(t0, 0) * 1000)
    fl.append(f"[{j}:a]aformat=channel_layouts=stereo,volume=-13dB,atrim=0:1.6,adelay={ms}|{ms}[s{j}]"); mix.append(f"[s{j}]"); j += 1
fl.append("".join(mix) + f"amix=inputs={j}:duration=first:normalize=0,alimiter=limit=0.95:level=false[a]")
subprocess.run(["ffmpeg", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[a]", "-ar", "44100", f"{tmp}/final.wav"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{tmp}/v.mp4", "-i", f"{tmp}/final.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", OUT], check=True)
print("ok", OUT)
