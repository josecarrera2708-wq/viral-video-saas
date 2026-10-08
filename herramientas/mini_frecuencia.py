#!/usr/bin/env python3
"""Miniatura 1280x720 del vídeo 3 con una escena ya generada (sin gastar imágenes) + texto grande en Anton.
Uso: python3 mini_frecuencia.py [escena.png] [salida.jpg]   (def. escena 18 -> marca/miniatura_frecuencia_1280x720.jpg)
El protagonista se desplaza a la izquierda y el hueco de la derecha se rellena con la propia escena desenfocada y oscurecida."""
import subprocess, sys, os
B = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = f"{B}/herramientas/Anton-Regular.ttf"
src = sys.argv[1] if len(sys.argv) > 1 else f"{B}/video/frecuencia-01/escenas/18.png"
out = sys.argv[2] if len(sys.argv) > 2 else f"{B}/video/frecuencia-01/marca/miniatura_frecuencia_1280x720.jpg"
SH = int(os.environ.get("SHIFT", 190))
def sh(*a): subprocess.run(a, check=True)
sh("convert", src, "-resize", "1280x720^", "-gravity", "center", "-extent", "1280x720", "/tmp/_a.png")
sh("convert", "/tmp/_a.png", "-blur", "0x18", "-modulate", "55,90", "/tmp/_base.png")
w = 1280 - SH
sh("convert", "/tmp/_a.png", "-crop", f"{w}x720+{SH}+0", "+repage", "(", "-size", f"{w}x720", "xc:white", "(", "-size", "150x720", "gradient:white-black", "-rotate", "-90", ")", "-gravity", "east", "-composite", ")", "-alpha", "off", "-compose", "CopyOpacity", "-composite", "/tmp/_host.png")
sh("convert", "/tmp/_base.png", "/tmp/_host.png", "-gravity", "west", "-compose", "over", "-composite", "/tmp/_comp.png")
def txt(t, y, color, size=132, x=640):
    return ["-font", F, "-pointsize", str(size), "-gravity", "NorthWest",
            "-fill", "black", "-stroke", "black", "-strokewidth", "16", "-annotate", f"+{x+6}+{y+8}", t,
            "-fill", color, "-stroke", "black", "-strokewidth", "8", "-annotate", f"+{x}+{y}", t,
            "-fill", color, "-stroke", "none", "-annotate", f"+{x}+{y}", t]
a = ["convert", "/tmp/_comp.png"] + txt("¿CUÁNTOS", 70, "white") + txt("DÍAS DEBO", 215, "white") + txt("ENTRENAR?", 360, "#FFD400", size=140) + ["-quality", "92", out]
sh(*a); print("listo", out, os.path.getsize(out) // 1024, "KB")
