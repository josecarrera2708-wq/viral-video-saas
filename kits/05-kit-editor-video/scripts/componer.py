#!/usr/bin/env python3
"""Monta el vídeo final: zooms, capas visuales y subtítulos, en una pasada.

Uso:  python scripts/componer.py <carpeta-del-proyecto>

Orden de las capas, de abajo a arriba:
  1. master.mp4 (ya cortado y en vertical)
  2. zooms          — el mismo plano ampliado, encima del trozo original
  3. capas          — rótulos, mockups y titulares (secuencias PNG)
  4. imágenes fijas — fotos o clips propios a pantalla completa
  5. subtítulos     — siempre lo último, para que nada los tape

Los zooms y las capas son opcionales: si no hay trabajo/timeline.json, se
montan solo los subtítulos y el vídeo queda igualmente terminado.

Salida: trabajo/montaje.mp4
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

TRANSPARENTE = "color=black@0.0"
SUPERMUESTREO = 2   # se amplía sobre el doble de tamaño: el zoom no da saltos


def _expresion_zoom(z, modo, duracion):
    """Curva del zoom. `it` es el tiempo dentro del trozo, en segundos."""
    dz = max(z - 1.0, 0.0)
    u = "(it/{0:.3f})".format(max(duracion, 0.05))
    # Un temblor mínimo, como de cámara en mano: sin esto el zoom parece
    # de diapositivas.
    temblor = "(1+0.012*sin(it*2.3)+0.008*sin(it*3.7+1.3))"
    if modo == "suave":
        # Arranca y frena despacio (3u²-2u³).
        curva = "(3*{u}*{u}-2*{u}*{u}*{u})".format(u=u)
    else:
        # Entra con un rebote pequeño y se asienta.
        curva = "(1-exp(-6*{u})*cos(7.5*{u}))".format(u=u)
    return "1+{0:.4f}*{1}*{2}".format(dz, curva, temblor)


def capa_zoom(indice, zoom, etiqueta_entrada):
    """Filtros de un zoom: recorta el trozo, lo amplía y lo alinea en el tiempo."""
    inicio = float(zoom["inicio"])
    fin = float(zoom["fin"])
    duracion = max(fin - inicio, 0.1)
    z = float(zoom.get("z", 1.15))
    expr = _expresion_zoom(z, zoom.get("modo", "resorte"), duracion)
    # El encuadre se va un poco al tercio alto: es donde está la cara.
    x = "iw/2-(iw/zoom/2)+7*sin(it*1.7)"
    y = "(ih-ih/zoom)*0.38+5*sin(it*1.3+2)"
    return (
        "[{ent}]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS,"
        "scale={W}:{H}:flags=lanczos,"
        "zoompan=z='{z}':x='{x}':y='{y}':d=1:s={w}x{h}:fps={fps},"
        "format=rgba,tpad=start_duration={a:.4f}:{t}[zoom{i}]"
    ).format(ent=etiqueta_entrada, a=inicio, b=fin, z=expr, x=x, y=y,
             W=c.ANCHO * SUPERMUESTREO, H=c.ALTO * SUPERMUESTREO,
             w=c.ANCHO, h=c.ALTO, fps=c.FPS, t=TRANSPARENTE, i=indice)


def componer(proyecto, calidad=17, refrescar=False):
    estado = c.cargar_proyecto(proyecto)
    salida = c.trabajo(estado, "montaje.mp4")
    if salida.is_file() and not refrescar:
        print("montaje.mp4 ya existe. Usa --refrescar para rehacerlo.")
        return salida

    master = c.trabajo(estado, "master.mp4")
    if not master.is_file():
        raise FileNotFoundError(
            "Falta trabajo/master.mp4. Corre antes:\n"
            "  python scripts/cortar.py \"{0}\"".format(estado["_carpeta"])
        )
    total = c.duracion(master)
    subs = c.leer_json(c.trabajo(estado, "subs.json"), {"grupos": []})
    linea = c.leer_json(c.trabajo(estado, "timeline.json"),
                        {"zooms": [], "capas": [], "fijas": []})

    zooms = [z for z in linea.get("zooms") or [] if z.get("fin", 0) > z.get("inicio", 0)]
    capas = list(linea.get("capas") or [])
    fijas = list(linea.get("fijas") or [])

    entradas = ["-i", str(master)]
    filtros = []
    indice = 1

    # El master se reparte en tantas copias como zooms haya, más la base.
    if zooms:
        salidas = "[base]" + "".join("[zc{0}]".format(i) for i in range(len(zooms)))
        filtros.append("[0:v]split={0}{1}".format(len(zooms) + 1, salidas))
        for i, z in enumerate(zooms):
            filtros.append(capa_zoom(i, z, "zc{0}".format(i)))
    else:
        filtros.append("[0:v]null[base]")

    # Capas visuales: secuencias de PNG generadas por capturar.py.
    etiquetas_capa = []
    for i, capa in enumerate(capas):
        patron = Path(estado["_carpeta"]) / "trabajo" / capa["secuencia"]
        primero = patron.parent / (patron.name + "-00000.png") if patron.suffix == "" \
            else patron
        if patron.suffix == "":
            patron = patron.parent / (patron.name + "-%05d.png")
        if not Path(str(primero)).is_file():
            print("  ! Falta la secuencia {0}: se salta esa capa.".format(
                capa["secuencia"]))
            continue
        entradas += ["-framerate", str(capa.get("fps", 30)),
                     "-start_number", "0", "-i", str(patron)]
        filtros.append(
            "[{k}:v]format=rgba,tpad=start_duration={a:.4f}:{t},fps={fps}[cap{i}]"
            .format(k=indice, a=float(capa.get("inicio", 0)), t=TRANSPARENTE,
                    fps=c.FPS, i=i))
        etiquetas_capa.append(("cap{0}".format(i), capa.get("x", 0),
                               capa.get("y", 0)))
        indice += 1

    # Imágenes o clips a pantalla completa, con entrada y salida suaves.
    etiquetas_fija = []
    for i, fija in enumerate(fijas):
        archivo = Path(fija["archivo"]).expanduser()
        if not archivo.is_absolute():
            archivo = c.RAIZ / archivo
        if not archivo.is_file():
            print("  ! No encuentro {0}: se salta.".format(archivo))
            continue
        inicio = float(fija.get("inicio", 0))
        dur = max(float(fija.get("fin", inicio + 2)) - inicio, 0.2)
        entradas += ["-i", str(archivo)]
        fundido = 0.18
        filtros.append(
            "[{k}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            "crop={W}:{H},format=rgba,loop=loop=-1:size=1:start=0,"
            "trim=0:{d:.4f},setpts=PTS-STARTPTS,"
            "fade=t=in:st=0:d={f}:alpha=1,fade=t=out:st={fo:.4f}:d={f}:alpha=1,"
            "tpad=start_duration={a:.4f}:{t},fps={fps}[fija{i}]"
            .format(k=indice, W=c.ANCHO, H=c.ALTO, d=dur, f=fundido,
                    fo=max(dur - fundido, 0.01), a=inicio, t=TRANSPARENTE,
                    fps=c.FPS, i=i))
        etiquetas_fija.append("fija{0}".format(i))
        indice += 1

    # Subtítulos: la última capa, para que ningún efecto los tape.
    lista_subs = c.trabajo(estado, "subs", "lista.txt")
    hay_subs = bool(subs.get("grupos")) and lista_subs.is_file()
    if hay_subs:
        entradas += ["-f", "concat", "-safe", "0", "-i", str(lista_subs)]
        filtros.append("[{k}:v]format=rgba,fps={fps}[subs]".format(
            k=indice, fps=c.FPS))
        indice += 1

    # Se van apilando las capas por orden.
    actual = "base"
    paso = 0

    def encadenar(etiqueta, x=0, y=0):
        nonlocal actual, paso
        filtros.append("[{0}][{1}]overlay={2}:{3}:eof_action=pass[mix{4}]".format(
            actual, etiqueta, x, y, paso))
        actual = "mix{0}".format(paso)
        paso += 1

    for i in range(len(zooms)):
        encadenar("zoom{0}".format(i))
    for etiqueta, x, y in etiquetas_capa:
        encadenar(etiqueta, x, y)
    for etiqueta in etiquetas_fija:
        encadenar(etiqueta)
    if hay_subs:
        encadenar("subs", 0, subs.get("y", 1300))

    filtros.append("[{0}]format=yuv420p[vout]".format(actual))

    args = entradas + ["-filter_complex", ";".join(filtros),
                       "-map", "[vout]"]
    if estado["origen_info"]["tiene_audio"]:
        args += ["-map", "0:a", "-c:a", "copy"]
    else:
        args += ["-an"]
    args += ["-t", "{0:.3f}".format(total),
             "-c:v", "libx264", "-preset", "medium", "-crf", str(calidad),
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(salida)]

    piezas = []
    if hay_subs:
        piezas.append("{0} grupos de subtítulos".format(len(subs["grupos"])))
    if zooms:
        piezas.append("{0} zooms".format(len(zooms)))
    if etiquetas_capa:
        piezas.append("{0} capas".format(len(etiquetas_capa)))
    if etiquetas_fija:
        piezas.append("{0} imágenes".format(len(etiquetas_fija)))
    print("Montando: {0}…".format(", ".join(piezas) or "solo el vídeo base"))
    c.correr_ffmpeg(args)

    print("  ✓ montaje.mp4  {0}".format(c.hhmmss(c.duracion(salida))))
    estado.setdefault("pasos", {})["componer"] = "ok"
    c.guardar_proyecto(estado)
    print("\nSiguiente paso: añadir los efectos de sonido y cerrar el vídeo")
    print("  python scripts/sonido.py \"{0}\"".format(estado["_carpeta"]))
    return salida


def main():
    ap = argparse.ArgumentParser(description="Monta subtítulos y efectos")
    ap.add_argument("proyecto")
    ap.add_argument("--calidad", type=int, default=17)
    ap.add_argument("--refrescar", action="store_true")
    a = ap.parse_args()
    try:
        componer(a.proyecto, a.calidad, a.refrescar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
