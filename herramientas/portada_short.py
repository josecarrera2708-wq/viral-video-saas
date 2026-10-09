#!/usr/bin/env python3
"""Portada vertical 1080x1920 de un Short: foto de fondo + título grande (Anton). Uso: portada_short.py <imagen> <salida.png> "LINEA1|LINEA2|LINEA3" [PALABRA_NARANJA]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
src, out, txt = sys.argv[1:4]; res = sys.argv[4] if len(sys.argv) > 4 else ""
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Anton-Regular.ttf"); W, H = 1080, 1920
im = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS); im = ImageEnhance.Contrast(im).enhance(1.12)
g = Image.new("L", (1, H)); 
for y in range(H): g.putpixel((0, y), int(60 * max(0, 1 - y / 700) + 215 * max(0, (y - 800) / 800) ** 0.9))
im = Image.composite(Image.new("RGB", (W, H), (5, 8, 14)), im, g.resize((W, H)))
d = ImageDraw.Draw(im); lines = txt.split("|"); y = int(os.environ.get("Y0", 190))
for ln in lines:
    sz = 230 if len(ln) <= 6 else (150 if len(ln) <= 12 else 118)
    f = ImageFont.truetype(F, sz)
    # ajusta para que quepa
    while d.textlength(ln, font=f) > W - 110: sz -= 4; f = ImageFont.truetype(F, sz)
    col = (255, 138, 31) if ln == res else (255, 255, 255)
    d.text((W / 2 + 6, y + 8), ln, font=f, fill=(0, 0, 0), anchor="ma", stroke_width=16, stroke_fill=(0, 0, 0))
    d.text((W / 2, y), ln, font=f, fill=col, anchor="ma", stroke_width=14, stroke_fill=(0, 0, 0))
    ult = (y, sz, d.textlength(ln, font=f)); y += int(sz * 1.2)
emo = os.environ.get("EMOJI")
if emo:   # emoji de color (Noto) a la derecha de la última línea
    e = Image.new("RGBA", (136, 128), (0, 0, 0, 0)); ImageDraw.Draw(e).text((0, 0), emo, font=ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109), embedded_color=True)
    e = e.resize((200, 188), Image.LANCZOS); y0, sz0, w0 = ult
    im.paste(e, (int(min(W / 2 + w0 / 2 + 5, W - 205)), int(y0 + sz0 * 0.5 - 85)), e)
im.save(out); print("ok", out)
