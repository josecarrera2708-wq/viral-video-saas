#!/usr/bin/env python3
"""Subtítulos karaoke: cada palabra se enciende cuando se dice.

Uso:  python scripts/subtitulos.py <carpeta-del-proyecto>

Los subtítulos se dibujan aquí, con Pillow, y salen como imágenes PNG con
fondo transparente. No se usa el filtro de texto de ffmpeg ni ficheros .ass
a propósito: así el resultado es idéntico en Mac y en Windows y no depende de
cómo esté compilado el ffmpeg de cada uno, que es de donde vienen la mitad de
los problemas con los subtítulos quemados.

Salida:
  trabajo/subs/*.png      una imagen por estado
  trabajo/subs/lista.txt  el orden y la duración de cada imagen
  trabajo/subs.json       los grupos y sus tiempos, para el resto del motor
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

# Cómo se agrupan las palabras en pantalla.
MAX_PALABRAS = 4
MAX_CARACTERES = 18
HUECO_GRUPO = 0.55      # a partir de este silencio empieza grupo nuevo
HUECO_ENCADENADO = 0.25  # por debajo de esto no hay fundido: cambio seco
ADELANTO = 0.08          # el grupo aparece un pelo antes de la primera palabra
COLA = 0.12              # y se queda un pelo después de la última

ESTILO = {
    "tamano": 78,
    "color_texto": "#FFFFFF",
    "color_activo": "#FF7A00",
    # Alto de la tira dentro del vídeo. Más abajo choca con los botones y el
    # texto que TikTok e Instagram pintan encima.
    "y": 1300,
    "margen": 56,
    "borde": 8,
    "sombra": 0.45,
}

# Errores típicos de transcripción en vídeos de este tipo. Se pueden añadir
# más en trabajo/correcciones.json sin tocar este archivo.
CORRECCIONES = {
    "cloud": "claude", "cloude": "claude", "clod": "claude", "clode": "claude",
    "clau": "claude", "cloe": "claude", "yipiti": "gpt", "chatgpt": "chatgpt",
    "gitjub": "github", "yijab": "github", "prompt": "prompt",
    "termina": "terminal", "tiktok": "tiktok",
}
PUNTUACION = '.,;:!?"¿¡()[]…-–—'
POP = [(0.88, 0.55), (0.95, 0.85), (1.02, 1.0)]   # entrada con rebote
FUNDIDO = [0.60, 0.28]                            # salida


def _color(hexa, alfa=255):
    h = hexa.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alfa)


# ── de tiempos del original a tiempos del vídeo cortado ────────────────────


def remapear(t, mapa):
    for i, (a, b, off) in enumerate(mapa):
        if a <= t < b:
            return off + (t - a), i
    return None, None


def palabras_en_corte(palabras, mapa, correcciones):
    """Solo las palabras que sobreviven a los cortes, con su tiempo nuevo."""
    salida = []
    for p in palabras:
        nuevo_inicio, trozo = remapear(p["inicio"], mapa)
        if nuevo_inicio is None:
            continue
        a, b, off = mapa[trozo]
        nuevo_fin = off + (min(p["fin"], b) - a)
        if nuevo_fin <= nuevo_inicio:
            nuevo_fin = nuevo_inicio + 0.08
        crudo = p["texto"].strip()
        limpio = crudo.strip(PUNTUACION)
        arreglado = correcciones.get(limpio.lower(), limpio)
        if not arreglado:
            continue
        salida.append({
            "inicio": round(nuevo_inicio, 3),
            "fin": round(nuevo_fin, 3),
            "texto": arreglado.upper(),
            "fin_frase": crudo[-1:] in ".?!…",
            "trozo": trozo,
        })
    return salida


def agrupar(palabras):
    grupos, actual = [], []
    for p in palabras:
        if actual:
            largo = (sum(len(x["texto"]) for x in actual) + len(actual)
                     + len(p["texto"]))
            corta = (p["inicio"] - actual[-1]["fin"] > HUECO_GRUPO
                     or len(actual) >= MAX_PALABRAS
                     or largo > MAX_CARACTERES
                     or actual[-1]["fin_frase"]
                     or p["trozo"] != actual[-1]["trozo"])
            if corta:
                grupos.append(actual)
                actual = []
        actual.append(p)
    if actual:
        grupos.append(actual)
    return grupos


def tiempos_grupos(grupos, total):
    """Cuándo entra y sale cada grupo, y qué palabra está activa en cada momento."""
    salida, fin_previo = [], 0.0
    for gi, g in enumerate(grupos):
        hueco_antes = g[0]["inicio"] - (grupos[gi - 1][-1]["fin"] if gi else 0.0)
        encadenado = gi > 0 and hueco_antes < HUECO_ENCADENADO
        if encadenado:
            # Habla seguida: el grupo anterior da paso al siguiente sin fundido,
            # que si no parece que parpadee.
            inicio = fin_previo
        else:
            inicio = max(g[0]["inicio"] - ADELANTO, fin_previo + 0.01)
        if gi + 1 < len(grupos):
            hueco_despues = grupos[gi + 1][0]["inicio"] - g[-1]["fin"]
            if hueco_despues < HUECO_ENCADENADO:
                fin = grupos[gi + 1][0]["inicio"]
            else:
                fin = min(g[-1]["fin"] + COLA,
                          grupos[gi + 1][0]["inicio"] - 0.10)
        else:
            hueco_despues = 99.0
            fin = min(g[-1]["fin"] + COLA, total)
        fin = max(fin, g[-1]["fin"] + 0.02)
        fin_previo = fin
        eventos = []
        for i in range(len(g)):
            desde = inicio if i == 0 else g[i]["inicio"]
            hasta = g[i + 1]["inicio"] if i + 1 < len(g) else fin
            if hasta > desde:
                eventos.append([round(desde, 3), round(hasta, 3), i])
        salida.append({
            "palabras": [p["texto"] for p in g],
            "inicio": round(inicio, 3), "fin": round(fin, 3),
            "entra": not encadenado,
            "sale": hueco_despues >= HUECO_ENCADENADO,
            "eventos": eventos,
        })
    return salida


# ── dibujo ─────────────────────────────────────────────────────────────────


class Pintor:
    """Dibuja una tira de subtítulo. Todas las tiras miden lo mismo."""

    def __init__(self, estilo):
        self.e = estilo
        self.ancho = c.ANCHO
        self.usable = c.ANCHO - 2 * estilo["margen"]
        self.alto_linea = int(estilo["tamano"] * 1.16)
        self.alto = self.alto_linea * 2 + 90

    def _partir(self, palabras, tipo):
        """Reparte las palabras en una o dos líneas que quepan a lo ancho."""
        lineas, actual = [], []
        for idx, palabra in enumerate(palabras):
            prueba = actual + [(palabra, idx)]
            texto = " ".join(p for p, _ in prueba)
            if actual and tipo.getlength(texto) > self.usable:
                lineas.append(actual)
                actual = [(palabra, idx)]
            else:
                actual = prueba
        if actual:
            lineas.append(actual)
        return lineas[:2]

    def tira(self, palabras, activo, escala=1.0, alfa=1.0):
        from PIL import Image, ImageDraw, ImageFilter

        e = self.e
        tamano = e["tamano"]
        tipo = c.fuente("titulo", tamano, 700)
        lineas = self._partir(palabras, tipo)
        # Si con dos líneas aún no cabe, se baja el cuerpo hasta que entre.
        while tamano > 52 and any(
                tipo.getlength(" ".join(p for p, _ in l)) > self.usable
                for l in lineas):
            tamano -= 4
            tipo = c.fuente("titulo", tamano, 700)
            lineas = self._partir(palabras, tipo)

        lienzo = Image.new("RGBA", (self.ancho, self.alto), (0, 0, 0, 0))
        mascara = Image.new("L", (self.ancho, self.alto), 0)
        d = ImageDraw.Draw(lienzo)
        dm = ImageDraw.Draw(mascara)

        alto_linea = int(tamano * 1.16)
        alto_bloque = alto_linea * len(lineas)
        y = (self.alto - alto_bloque) // 2

        cajas = []
        for linea in lineas:
            texto = " ".join(p for p, _ in linea)
            x = (self.ancho - tipo.getlength(texto)) / 2
            # El contorno se dibuja de una vez con la línea entera: si se
            # dibujara palabra a palabra, el borde de una taparía la anterior.
            d.text((x, y), texto, font=tipo, fill=(0, 0, 0, 255),
                   stroke_width=e["borde"], stroke_fill=(0, 0, 0, 255))
            dm.text((x, y), texto, font=tipo, fill=255,
                    stroke_width=e["borde"], stroke_fill=255)
            # Cada palabra se sitúa midiendo el trozo de línea que la precede,
            # así encaja exactamente con el contorno ya dibujado.
            cursor = 0
            for palabra, idx in linea:
                dx = tipo.getlength(texto[:cursor]) if cursor else 0.0
                cajas.append((x + dx, y, palabra, idx))
                cursor += len(palabra) + 1
            y += alto_linea

        # Sombra por debajo: sin ella el texto se pierde sobre fondos claros.
        if e["sombra"] > 0:
            difusa = mascara.filter(ImageFilter.GaussianBlur(11))
            sombra = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
            sombra.putalpha(difusa.point(lambda v: int(v * e["sombra"])))
            desplazada = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
            desplazada.paste(sombra, (0, 9))
            lienzo = Image.alpha_composite(desplazada, lienzo)
            d = ImageDraw.Draw(lienzo)

        for x0, y0, palabra, idx in cajas:
            color = _color(e["color_activo"] if idx == activo else e["color_texto"])
            d.text((x0, y0), palabra, font=tipo, fill=color)

        if escala != 1.0:
            nuevo = (max(int(self.ancho * escala), 2), max(int(self.alto * escala), 2))
            reducida = lienzo.resize(nuevo, Image.LANCZOS)
            lienzo = Image.new("RGBA", (self.ancho, self.alto), (0, 0, 0, 0))
            lienzo.paste(reducida, ((self.ancho - nuevo[0]) // 2,
                                    (self.alto - nuevo[1]) // 2))
        if alfa < 1.0:
            banda = lienzo.getchannel("A").point(lambda v: int(v * alfa))
            lienzo.putalpha(banda)
        return lienzo

    def vacia(self):
        from PIL import Image
        return Image.new("RGBA", (self.ancho, self.alto), (0, 0, 0, 0))


# ── secuencia de imágenes ──────────────────────────────────────────────────


def estados_por_fotograma(grupos, total, fps):
    """Qué imagen toca en cada fotograma, ya resuelto rebote y fundido."""
    tira = []
    cursor = 0
    for gi, g in enumerate(grupos):
        inicio_f = int(round(g["inicio"] * fps))
        if inicio_f > cursor:
            tira.append(("vacio", inicio_f - cursor))
            cursor = inicio_f
        estados = []
        for desde, hasta, idx in g["eventos"]:
            n = int(round(hasta * fps)) - int(round(desde * fps))
            estados.extend([("ev", gi, idx)] * max(n, 1))
        if not estados:
            continue
        if g["entra"]:
            for k in range(min(len(POP), len(estados))):
                estados[k] = ("pop", gi, k)
        if g["sale"] and len(estados) > len(POP) + len(FUNDIDO):
            ultimo = estados[-1][2]
            for k in range(len(FUNDIDO)):
                estados[-1 - k] = ("fade", gi, ultimo, k)
        # Se agrupan los fotogramas iguales para no repetir imágenes.
        for estado in estados:
            if tira and tira[-1][0] == estado:
                tira[-1] = (estado, tira[-1][1] + 1)
            else:
                tira.append((estado, 1))
        cursor += len(estados)
    final_f = int(round(total * fps))
    if final_f > cursor:
        tira.append(("vacio", final_f - cursor))
    return tira


def clave(estado):
    if estado == "vacio":
        return "vacio"
    if estado[0] == "ev":
        return "g{0:03d}-p{1}".format(estado[1], estado[2])
    if estado[0] == "pop":
        return "g{0:03d}-pop{1}".format(estado[1], estado[2])
    return "g{0:03d}-out{1}".format(estado[1], estado[3])


def generar(proyecto, refrescar=False):
    estado_p = c.cargar_proyecto(proyecto)
    trans = c.leer_json(c.trabajo(estado_p, "transcripcion.json"),
                        {"palabras": []})
    plan = c.leer_json(c.trabajo(estado_p, "plan-cortes.json"), None)
    master = c.trabajo(estado_p, "master.mp4")
    if not master.is_file():
        raise FileNotFoundError(
            "Falta trabajo/master.mp4. Corre primero:\n"
            "  python scripts/cortar.py \"{0}\"".format(estado_p["_carpeta"])
        )
    total = c.duracion(master)
    mapa = plan["mapa"] if plan and plan.get("mapa") else [[0.0, total, 0.0]]

    estilo = dict(ESTILO)
    estilo.update(estado_p.get("subs") or {})
    correcciones = dict(CORRECCIONES)
    correcciones.update({k.lower(): v for k, v in c.leer_json(
        c.trabajo(estado_p, "correcciones.json"), {}).items()})

    palabras = palabras_en_corte(trans.get("palabras") or [], mapa, correcciones)
    if not palabras:
        print("No hay palabras que subtitular (¿vídeo sin voz?). Se salta el paso.")
        c.escribir_json(c.trabajo(estado_p, "subs.json"),
                        {"grupos": [], "alto": 0, "y": estilo["y"]})
        return None

    grupos = tiempos_grupos(agrupar(palabras), total)
    tira = estados_por_fotograma(grupos, total, c.FPS)

    carpeta = c.trabajo(estado_p, "subs")
    if carpeta.exists() and refrescar:
        shutil.rmtree(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)

    pintor = Pintor(estilo)
    hechas = {}
    for est, _ in tira:
        nombre = clave(est)
        if nombre in hechas:
            continue
        destino = carpeta / (nombre + ".png")
        if est == "vacio":
            imagen = pintor.vacia()
        elif est[0] == "ev":
            imagen = pintor.tira(grupos[est[1]]["palabras"], est[2])
        elif est[0] == "pop":
            escala, alfa = POP[est[2]]
            imagen = pintor.tira(grupos[est[1]]["palabras"], 0, escala, alfa)
        else:
            imagen = pintor.tira(grupos[est[1]]["palabras"], est[2],
                                 1.0, FUNDIDO[est[3]])
        imagen.save(destino)
        hechas[nombre] = destino

    lineas = ["ffconcat version 1.0"]
    for est, n in tira:
        lineas.append("file '{0}.png'".format(clave(est)))
        lineas.append("duration {0:.6f}".format(n / c.FPS))
    # La última imagen se repite: si no, el demuxer ignora su duración.
    lineas.append("file '{0}.png'".format(clave(tira[-1][0])))
    (carpeta / "lista.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    c.escribir_json(c.trabajo(estado_p, "subs.json"), {
        "grupos": grupos,
        "alto": pintor.alto,
        "y": estilo["y"],
        "lista": "subs/lista.txt",
    })
    estado_p.setdefault("pasos", {})["subtitulos"] = "ok"
    c.guardar_proyecto(estado_p)

    print("Subtítulos: {0} grupos, {1} imágenes, {2} tramos".format(
        len(grupos), len(hechas), len(tira)))
    print("  tira de {0}x{1} px colocada en y={2}".format(
        pintor.ancho, pintor.alto, estilo["y"]))
    for g in grupos[:6]:
        print("  {0}  {1}".format(c.hhmmss(g["inicio"]), " ".join(g["palabras"])))
    if len(grupos) > 6:
        print("  … y {0} grupos más".format(len(grupos) - 6))
    print("\nSiguiente paso: quemar los subtítulos y los efectos")
    print("  python scripts/componer.py \"{0}\"".format(estado_p["_carpeta"]))
    return grupos


def main():
    ap = argparse.ArgumentParser(description="Genera los subtítulos karaoke")
    ap.add_argument("proyecto")
    ap.add_argument("--refrescar", action="store_true",
                    help="borrar las imágenes anteriores")
    a = ap.parse_args()
    try:
        generar(a.proyecto, a.refrescar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
