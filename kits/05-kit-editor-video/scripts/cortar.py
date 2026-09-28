#!/usr/bin/env python3
"""Aplica el plan de cortes y deja el vídeo en vertical 1080x1920.

Uso:  python scripts/cortar.py <carpeta-del-proyecto>

Se hace todo en una sola pasada de ffmpeg: recortar los trozos, pegarlos,
pasar a vertical y dejarlo a 60 fps. Una sola pasada significa una sola
recompresión, así que no se pierde calidad por el camino.

Salida: trabajo/master.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c
from encuadre import medidas_recorte

MAX_TROZOS = 400


def cadena_vertical(info, encuadre):
    """Filtros que convierten el vídeo ya cortado en 1080x1920."""
    ancho, alto = info["ancho"], info["alto"]
    centro = float(encuadre.get("centro", 0.5))
    if encuadre.get("modo") == "marco":
        # El vídeo entero, con su propio fondo desenfocado detrás. Se ve todo,
        # aunque queden franjas arriba y abajo.
        return (
            "split=2[bg][fg];"
            "[bg]scale={a}:{b}:force_original_aspect_ratio=increase,"
            "crop={a}:{b},boxblur=42:2,eq=brightness=-0.12[bgb];"
            "[fg]scale={a}:-2:flags=lanczos[fgs];"
            "[bgb][fgs]overlay=(W-w)/2:(H-h)*0.42"
        ).format(a=c.ANCHO, b=c.ALTO)
    x, y, w, h = medidas_recorte(ancho, alto, centro)
    # Al ampliar un recorte se pierde nitidez; un unsharp suave lo compensa
    # sin que se marquen bordes.
    return ("crop={w}:{h}:{x}:{y},scale={A}:{B}:flags=lanczos,"
            "unsharp=5:5:0.5:5:5:0.0").format(
        w=w, h=h, x=x, y=y, A=c.ANCHO, B=c.ALTO)


def construir_filtro(mapa, tiene_audio, vertical):
    """Grafo completo: trozo a trozo, pegado y pasado a vertical."""
    n = len(mapa)
    partes = []
    if n == 1 and mapa[0][0] <= 0.01:
        partes.append("[0:v]null[vc]")
        if tiene_audio:
            partes.append("[0:a]anull[ac]")
    else:
        partes.append("[0:v]split={0}{1}".format(
            n, "".join("[v{0}]".format(i) for i in range(n))))
        if tiene_audio:
            partes.append("[0:a]asplit={0}{1}".format(
                n, "".join("[a{0}]".format(i) for i in range(n))))
        etiquetas = []
        for i, (a, b, _) in enumerate(mapa):
            partes.append("[v{0}]trim={1:.4f}:{2:.4f},setpts=PTS-STARTPTS[tv{0}]"
                          .format(i, a, b))
            etiquetas.append("[tv{0}]".format(i))
            if tiene_audio:
                partes.append(
                    "[a{0}]atrim={1:.4f}:{2:.4f},asetpts=PTS-STARTPTS[ta{0}]"
                    .format(i, a, b))
                etiquetas.append("[ta{0}]".format(i))
        partes.append("{0}concat=n={1}:v=1:a={2}[vc]{3}".format(
            "".join(etiquetas), n, 1 if tiene_audio else 0,
            "[ac]" if tiene_audio else ""))
    partes.append("[vc]{0},fps={1},setsar=1,format=yuv420p[vout]".format(
        vertical, c.FPS))
    return ";".join(partes)


def cortar(proyecto, calidad=16, refrescar=False):
    estado = c.cargar_proyecto(proyecto)
    salida = c.trabajo(estado, "master.mp4")
    if salida.is_file() and not refrescar:
        print("master.mp4 ya existe ({0}). Usa --refrescar para rehacerlo."
              .format(c.hhmmss(c.duracion(salida))))
        return salida

    origen = c.ruta_origen(estado)
    info = estado["origen_info"]
    plan = c.leer_json(c.trabajo(estado, "plan-cortes.json"), None)
    if plan and plan.get("mapa"):
        mapa = plan["mapa"]
        esperado = plan["duracion_final"]
    else:
        print("  ! No hay plan de cortes: se usa el vídeo entero.")
        mapa = [[0.0, float(info["duracion"]), 0.0]]
        esperado = float(info["duracion"])

    if len(mapa) > MAX_TROZOS:
        raise RuntimeError(
            "El plan tiene {0} trozos y eso es demasiado para una pasada. "
            "Sube el umbral de silencio para agrupar cortes:\n"
            "  python scripts/plan_cortes.py \"{1}\" --umbral 0.9"
            .format(len(mapa), estado["_carpeta"])
        )

    encuadre = estado.get("encuadre") or {"modo": "recorte", "centro": 0.5}
    if "encuadre" not in estado:
        print("  ! Sin encuadre elegido: se recorta por el centro. Para ajustarlo:")
        print("    python scripts/encuadre.py \"{0}\"".format(estado["_carpeta"]))

    filtro = construir_filtro(mapa, bool(info["tiene_audio"]),
                              cadena_vertical(info, encuadre))
    args = ["-i", str(origen), "-filter_complex", filtro,
            "-map", "[vout]"]
    if info["tiene_audio"]:
        args += ["-map", "[ac]", "-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
    else:
        args += ["-an"]
    args += ["-c:v", "libx264", "-preset", "medium", "-crf", str(calidad),
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(salida)]

    print("Cortando y pasando a vertical ({0} trozos)…".format(len(mapa)))
    c.correr_ffmpeg(args)

    real = c.duracion(salida)
    print("  ✓ master.mp4  {0}  ({1}x{2} a {3} fps)".format(
        c.hhmmss(real), c.ANCHO, c.ALTO, c.FPS))
    if abs(real - esperado) > 0.5:
        print("  ! Esperaba {0} y ha salido {1}. Si la diferencia se nota, "
              "revisa el plan de cortes.".format(c.hhmmss(esperado), c.hhmmss(real)))

    estado["duracion_master"] = round(real, 3)
    estado.setdefault("pasos", {})["cortar"] = "ok"
    c.guardar_proyecto(estado)
    print("\nSiguiente paso: generar los subtítulos")
    print("  python scripts/subtitulos.py \"{0}\"".format(estado["_carpeta"]))
    return salida


def main():
    ap = argparse.ArgumentParser(description="Corta y pasa el vídeo a vertical")
    ap.add_argument("proyecto")
    ap.add_argument("--calidad", type=int, default=16,
                    help="crf de x264: menos es mejor calidad (por defecto 16)")
    ap.add_argument("--refrescar", action="store_true")
    a = ap.parse_args()
    try:
        cortar(a.proyecto, a.calidad, a.refrescar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
