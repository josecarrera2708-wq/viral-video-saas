#!/usr/bin/env python3
"""Crea un proyecto nuevo en workspace/ a partir de un vídeo en bruto.

Uso:  python scripts/nuevo.py "/ruta/al/video.mp4" [--nombre mi-video]

Deja workspace/<nombre>/proyecto.json con los datos del vídeo y avisa de lo
que pueda dar problemas más adelante (sin audio, muy corto, ya vertical…).
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c


def crear(origen, nombre=None, forzar=False):
    origen = Path(origen).expanduser().resolve()
    if not origen.is_file():
        raise FileNotFoundError(
            "No encuentro el vídeo en {0}. Arrastra el archivo al chat para "
            "que salga la ruta correcta.".format(origen)
        )
    info = c.info_media(origen)
    if info["duracion"] < 1.0:
        raise RuntimeError(
            "Ese archivo dura {0:.1f}s o no es un vídeo que ffmpeg entienda."
            .format(info["duracion"])
        )

    nombre = c.slug(nombre or origen.stem)
    carpeta = c.WORKSPACE / nombre
    if carpeta.exists() and not forzar:
        n = 2
        while (c.WORKSPACE / "{0}-{1}".format(nombre, n)).exists():
            n += 1
        nombre = "{0}-{1}".format(nombre, n)
        carpeta = c.WORKSPACE / nombre
    (carpeta / "trabajo").mkdir(parents=True, exist_ok=True)

    estado = {
        "nombre": nombre,
        "origen": str(origen),
        "creado": date.today().isoformat(),
        "origen_info": info,
        "motor_transcripcion": "whisper",
        "modelo_whisper": "small",
        "idioma": "es",
        "pasos": {},
        "_carpeta": str(carpeta),
    }
    c.guardar_proyecto(estado)

    print("Proyecto «{0}» creado.".format(nombre))
    print("  vídeo    {0}".format(origen.name))
    print("  duración {0}   {1}x{2} a {3} fps".format(
        c.hhmmss(info["duracion"]), info["ancho"], info["alto"], info["fps"]))
    print("  carpeta  {0}".format(carpeta))

    avisos = []
    if not info["tiene_audio"]:
        avisos.append("El vídeo no tiene audio: no habrá subtítulos ni cortes "
                      "de silencio. Solo se podrá recortar a vertical.")
    if info["alto"] and info["ancho"] / info["alto"] < 1.0:
        avisos.append("Ya es vertical, así que no hace falta reencuadrar; "
                      "el kit igualmente ajusta a 1080x1920.")
    if info["duracion"] > 600:
        avisos.append("Dura más de 10 minutos: transcribir y renderizar puede "
                      "llevar bastante. Considera recortar antes la parte útil.")
    if info["fps"] and info["fps"] > 61:
        avisos.append("Grabado a {0} fps: el resultado sale a 60 fps."
                      .format(info["fps"]))
    for a in avisos:
        print("  ! {0}".format(a))

    print("\nSiguiente paso: transcribir el audio")
    print("  python scripts/transcribir.py \"{0}\"".format(carpeta))
    return estado


def main():
    ap = argparse.ArgumentParser(description="Crea un proyecto de edición")
    ap.add_argument("video", help="ruta del vídeo en bruto")
    ap.add_argument("--nombre", default=None, help="nombre de la carpeta")
    ap.add_argument("--forzar", action="store_true",
                    help="reutilizar la carpeta si ya existe")
    a = ap.parse_args()
    try:
        crear(a.video, a.nombre, a.forzar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
