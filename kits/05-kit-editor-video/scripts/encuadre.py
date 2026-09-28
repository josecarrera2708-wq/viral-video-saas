#!/usr/bin/env python3
"""Saca fotogramas con una regla encima para elegir el recorte vertical.

Uso:  python scripts/encuadre.py <carpeta-del-proyecto>

Un vídeo horizontal no cabe en vertical: hay que decidir qué franja se queda.
Este paso no lo adivina, lo enseña. Genera tres fotogramas con marcas cada
10 % y el rectángulo de recorte dibujado, para mirarlos y decir dónde está
la cara. Después se guarda esa posición con:

  python scripts/encuadre.py <proyecto> --centro 0.38
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

PROPORCION = c.ANCHO / c.ALTO   # 0.5625


def medidas_recorte(ancho, alto, centro=0.5):
    """Rectángulo 9:16 dentro del vídeo original. Devuelve (x, y, w, h)."""
    ancho_recorte = int(round(alto * PROPORCION / 2) * 2)
    if ancho_recorte <= ancho:
        x = int(round(ancho * centro - ancho_recorte / 2))
        x = max(0, min(x, ancho - ancho_recorte))
        return x, 0, ancho_recorte, alto
    # El vídeo ya es más estrecho que 9:16: se recorta por arriba y abajo.
    alto_recorte = int(round(ancho / PROPORCION / 2) * 2)
    alto_recorte = min(alto_recorte, alto)
    # Se deja más aire arriba que abajo: las caras quedan mejor en el tercio alto.
    y = int(round((alto - alto_recorte) * 0.35))
    return 0, max(0, y), ancho, alto_recorte


def dibujar_regla(imagen, ancho, alto, centro):
    from PIL import ImageDraw

    d = ImageDraw.Draw(imagen, "RGBA")
    tipo = c.fuente("mono", max(18, alto // 34), 700)
    for pct in range(0, 101, 10):
        x = int(ancho * pct / 100)
        x = min(max(x, 1), ancho - 2)
        d.line([(x, 0), (x, alto)], fill=(255, 255, 255, 90), width=2)
        etiqueta = "{0}".format(pct)
        d.rectangle([x + 4, 6, x + 14 + 22 * len(etiqueta), 12 + alto // 30],
                    fill=(0, 0, 0, 150))
        d.text((x + 9, 9), etiqueta, font=tipo, fill=(255, 255, 255, 230))
    rx, ry, rw, rh = medidas_recorte(ancho, alto, centro)
    d.rectangle([rx, ry, rx + rw - 1, ry + rh - 1],
                outline=(255, 122, 0, 255), width=6)
    # El rótulo va abajo: arriba taparía los números de la regla.
    banda = int(alto // 18)
    d.rectangle([rx, ry + rh - banda, rx + rw - 1, ry + rh - 1],
                fill=(255, 122, 0, 230))
    d.text((rx + 14, ry + rh - banda + 6),
           "recorte centro={0:.2f}".format(centro),
           font=tipo, fill=(0, 0, 0, 255))
    return imagen


def previsualizar(proyecto):
    from PIL import Image

    estado = c.cargar_proyecto(proyecto)
    origen = c.ruta_origen(estado)
    info = estado["origen_info"]
    total = float(info["duracion"])
    centro = float(estado.get("encuadre", {}).get("centro", 0.5))
    carpeta = c.trabajo(estado, "encuadre")
    carpeta.mkdir(parents=True, exist_ok=True)

    generados = []
    for etiqueta, fraccion in (("inicio", 0.15), ("medio", 0.5), ("final", 0.85)):
        crudo = carpeta / "crudo-{0}.png".format(etiqueta)
        c.correr_ffmpeg([
            "-ss", "{0:.3f}".format(total * fraccion), "-i", str(origen),
            "-frames:v", "1", "-q:v", "2", str(crudo),
        ])
        img = Image.open(crudo).convert("RGB")
        dibujar_regla(img, img.width, img.height, centro)
        destino = carpeta / "guia-{0}.png".format(etiqueta)
        img.save(destino)
        crudo.unlink(missing_ok=True)
        generados.append(destino)

    print("Fotogramas con regla en trabajo/encuadre/:")
    for g in generados:
        print("  {0}".format(g.name))
    print("\nMira dónde queda la cara en la regla (0 = izquierda, 100 = derecha)")
    print("y fija el centro del recorte, por ejemplo al 38 %:")
    print("  python scripts/encuadre.py \"{0}\" --centro 0.38".format(
        estado["_carpeta"]))
    return generados


def fijar(proyecto, centro, modo):
    estado = c.cargar_proyecto(proyecto)
    if not 0.0 <= centro <= 1.0:
        raise RuntimeError("El centro va de 0.0 a 1.0 (0.5 es el medio).")
    info = estado["origen_info"]
    estado["encuadre"] = {"modo": modo, "centro": round(centro, 3)}
    c.guardar_proyecto(estado)
    x, y, w, h = medidas_recorte(info["ancho"], info["alto"], centro)
    print("Encuadre guardado: modo {0}, centro {1:.2f}".format(modo, centro))
    if modo == "recorte":
        print("  recorta {0}x{1} desde x={2} y={3} y lo escala a {4}x{5}".format(
            w, h, x, y, c.ANCHO, c.ALTO))
    else:
        print("  el vídeo entero cabe dentro, con fondo desenfocado detrás")
    print("\nSiguiente paso: aplicar los cortes")
    print("  python scripts/cortar.py \"{0}\"".format(estado["_carpeta"]))
    return estado


def main():
    ap = argparse.ArgumentParser(description="Elige el recorte vertical")
    ap.add_argument("proyecto")
    ap.add_argument("--centro", type=float, default=None,
                    help="0.0 izquierda, 0.5 centro, 1.0 derecha")
    ap.add_argument("--modo", choices=["recorte", "marco"], default="recorte",
                    help="recorte = llena la pantalla; marco = entero con fondo")
    a = ap.parse_args()
    try:
        if a.centro is None:
            previsualizar(a.proyecto)
        else:
            fijar(a.proyecto, a.centro, a.modo)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
