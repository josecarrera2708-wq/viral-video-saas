#!/usr/bin/env python3
"""Pantalla final de YouTube (1920x1080, 16:9): fondo del vídeo con el personaje + "SUSCRÍBETE" + huecos donde van
los 2 elementos de vídeo y el círculo de suscripción de Studio. Se pone en los últimos 20 s del vídeo.
Uso: python3 pantalla_final.py <fondo.png> <salida.png> [--guia]
  fondo.png: ilustración 16:9 con el personaje a la izquierda y la derecha tranquila (ver FONDO_PROMPT; generarla con --generar).
  --generar: crea el fondo con gpt-image-2 (1 imagen, calidad media, máx. 2 intentos) si <fondo.png> no existe.
  --guia: además guarda <salida>_guia.png con los huecos rotulados, solo para colocar los elementos en Studio.
Variables: TITULO, LEMA, ENCABEZADO."""
import os, sys, json, base64, time, subprocess, urllib.request
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = f"{BASE}/herramientas/Anton-Regular.ttf"
TITULO = os.environ.get("TITULO", "SUSCRÍBETE")
LEMA = os.environ.get("LEMA", "CIENCIA DEL ENTRENAMIENTO, CADA SEMANA")
ENCABEZADO = os.environ.get("ENCABEZADO", "SIGUE VIENDO")
ESTILO = ("Semi-realistic 2D cartoon illustration in a polished vector style: clean bold outlines, soft cel shading, "
 "expressive detailed human characters with realistic proportions and emotional faces, cinematic lighting, "
 "saturated but harmonious palette with teal, orange and warm skin tones, 16:9 widescreen. "
 "Absolutely no text, no letters, no numbers, no logos, no watermarks, no captions anywhere in the image.")
FONDO_PROMPT = ("Wide 16:9 end-card background. On the LEFT third of the frame the channel's protagonist, a young Latino man with short dark hair "
 "and a black tank top, athletic build, stands in a dark modern gym facing the viewer with a confident friendly smile, one arm extended toward the right "
 "of the frame with an open palm, as if inviting the viewer to come along. Warm orange rim light on him, teal shadows. "
 "The RIGHT two thirds of the frame is a dark, softly out-of-focus gym (squat racks, dumbbell rack, bokeh lights), low contrast and very little detail, "
 "leaving a calm empty area for overlay graphics. Consistent protagonist: young Latino man, short dark hair, black tank top.")
# Huecos (px sobre 1920x1080): dos elementos de vídeo 16:9 y el círculo de suscripción
SLOT_W, SLOT_H = 520, 292
SLOTS = [(780, 500), (1340, 500)]
RING_C, RING_R = (1280, 930), 95

def generar_fondo(f):
    body = json.dumps({"model": "gpt-image-2", "prompt": ESTILO + "\n\nScene: " + FONDO_PROMPT, "size": "1536x864", "quality": "medium", "n": 1}).encode()
    for intento in range(2):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request("https://api.openai.com/v1/images/generations", body, {"Content-Type": "application/json"}), timeout=170))
            open(f, "wb").write(base64.b64decode(r["data"][0]["b64_json"])); print("fondo generado", f); return
        except Exception as e:
            print("error", str(e)[:140], flush=True); time.sleep(10)
    raise SystemExit("no se pudo generar el fondo (2 intentos); no se reintenta para no gastar")

def texto(sombra, relleno, size, x, y, t, grosor=12, fuente=FUENTE):
    """Texto con contorno y sombra: primero contorno grueso, luego relleno encima."""
    return ["-font", fuente, "-pointsize", str(size), "-gravity", "NorthWest",
            "-fill", "rgba(0,0,0,0.55)", "-stroke", "rgba(0,0,0,0.55)", "-strokewidth", str(grosor), "-annotate", f"+{x+8}+{y+10}", t,
            "-fill", sombra, "-stroke", sombra, "-strokewidth", str(grosor), "-annotate", f"+{x}+{y}", t,
            "-fill", relleno, "-stroke", "none", "-annotate", f"+{x}+{y}", t]

def componer(fondo, salida, guia=False):
    a = ["convert", fondo, "-resize", "1920x1080^", "-gravity", "center", "-extent", "1920x1080",
         # oscurece de izquierda a derecha para que el personaje destaque y los huecos se vean limpios
         "(", "-size", "1080x1920", "gradient:rgba(0,0,0,0)-rgba(0,0,0,0.80)", "-rotate", "-90", ")", "-compose", "over", "-composite",
         "-gravity", "NorthWest"]
    a += texto("black", "#FFD400", 205, 770, 40, TITULO, grosor=14)
    a += texto("black", "white", 60, 780, 292, LEMA, grosor=8)
    a += texto("black", "white", 52, 780, 425, ENCABEZADO, grosor=7)
    # huecos de los dos vídeos
    for x, y in SLOTS:
        a += ["-fill", "rgba(0,0,0,0.38)", "-stroke", "rgba(255,255,255,0.85)", "-strokewidth", "5", "-draw", f"roundrectangle {x},{y} {x+SLOT_W},{y+SLOT_H} 22,22"]
    # círculo de suscripción (anillo rojo) + flecha y texto
    cx, cy = RING_C
    a += ["-fill", "rgba(0,0,0,0.38)", "-stroke", "#FF2D2D", "-strokewidth", "10", "-draw", f"circle {cx},{cy} {cx+RING_R},{cy}"]
    a += texto("black", "white", 50, cx + RING_R + 40, cy - 38, "TOCA EL CÍRCULO", grosor=7)
    a += ["-gravity", "NorthWest", salida]
    subprocess.run(a, check=True)
    if guia:
        g = ["convert", salida, "-gravity", "NorthWest", "-fill", "yellow", "-stroke", "black", "-strokewidth", "3", "-font", FUENTE, "-pointsize", "46"]
        for i, (x, y) in enumerate(SLOTS):
            g += ["-annotate", f"+{x+20}+{y+20}", f"VIDEO {i+1}  ({SLOT_W}x{SLOT_H})"]
        g += ["-pointsize", "34", "-annotate", f"+{cx-78}+{cy-24}", "SUSCRIBIRSE", salida.replace(".png", "_guia.png")]
        subprocess.run(g, check=True)

if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    fondo, salida = args[0], args[1]
    if "--generar" in sys.argv and not os.path.exists(fondo): generar_fondo(fondo)
    componer(fondo, salida, "--guia" in sys.argv)
    print("listo", salida)
