#!/usr/bin/env python3
"""Efectos de sonido y volumen final. Este paso cierra el vídeo.

Uso:  python scripts/sonido.py <carpeta-del-proyecto>

Hace dos cosas:
  1. Iguala el volumen de la voz a -14 LUFS, que es el nivel al que suenan
     TikTok, Instagram y YouTube. Si no se hace, el vídeo se oye más bajo
     que el resto del feed y la gente pasa de largo.
  2. Mezcla los efectos de sonido que haya en trabajo/sfx.json.

Si ese archivo no existe se propone una mezcla sobria (un barrido corto en
los saltos largos) y se guarda para que se pueda retocar y volver a correr.

Salida:  <carpeta-del-proyecto>/<nombre>-vertical.mp4   ← el vídeo terminado
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

LUFS_OBJETIVO = -14.0    # nivel de las redes sociales
PICO_MAXIMO = -1.5       # margen para que no sature al recomprimir
MAX_EVENTOS = 60         # más que esto es ruido, no edición
GAP_PARA_BARRIDO = 0.70  # silencio quitado a partir del cual el salto se nota
MAX_BARRIDOS = 12


def catalogo():
    datos = c.leer_json(c.SFX / "sonidos.json", {})
    return {k: v for k, v in datos.items() if not k.startswith("_")}


# ── volumen de la voz ──────────────────────────────────────────────────────


def medir_voz(archivo):
    """Mide el volumen real de la voz. Devuelve None si no se puede medir.

    Se hace en dos pasadas a propósito: en una sola, loudnorm va corrigiendo
    a ciegas mientras avanza y la voz sube y baja. Midiendo primero, la
    corrección es un único ajuste parejo de principio a fin.
    """
    cmd = [c.ffmpeg(), "-nostdin", "-hide_banner", "-i", str(archivo),
           "-map", "0:a:0",
           "-af", "loudnorm=I={0}:TP={1}:LRA=11:print_format=json".format(
               LUFS_OBJETIVO, PICO_MAXIMO),
           "-f", "null", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.SubprocessError):
        return None
    bloques = re.findall(r"\{[^{}]*input_i[^{}]*\}", proc.stderr or "", re.S)
    if not bloques:
        return None
    try:
        medido = json.loads(bloques[-1])
        return {k: medido[k] for k in
                ("input_i", "input_tp", "input_lra", "input_thresh")}
    except (ValueError, KeyError):
        return None


def filtro_voz(medida):
    base = "loudnorm=I={0}:TP={1}:LRA=11".format(LUFS_OBJETIVO, PICO_MAXIMO)
    if medida:
        base += (":measured_I={input_i}:measured_TP={input_tp}"
                 ":measured_LRA={input_lra}:measured_thresh={input_thresh}"
                 ":linear=true".format(**medida))
    return base


# ── efectos ────────────────────────────────────────────────────────────────


def eventos_por_defecto(estado, total):
    """Propone un barrido corto en cada salto largo, y nada más.

    Un efecto en cada corte cansa; en los saltos largos ayuda a entender
    que ahí faltaba algo.
    """
    plan = c.leer_json(c.trabajo(estado, "plan-cortes.json"), None)
    if not plan or not plan.get("mapa"):
        return []
    mapa = plan["mapa"]
    saltos = []
    for i in range(1, len(mapa)):
        quitado = mapa[i][0] - mapa[i - 1][1]
        momento = mapa[i][2]
        if quitado >= GAP_PARA_BARRIDO and 0.2 < momento < total - 0.2:
            saltos.append((quitado, momento))
    # Si hay muchos, se queda con los saltos más largos: son los que más se ven.
    saltos.sort(key=lambda s: -s[0])
    return [{"sonido": "whoosh-short", "t": round(momento, 3),
             "ganancia": 0.24,
             "nota": "salto de {0:.1f} s".format(quitado)}
            for quitado, momento in sorted(saltos[:MAX_BARRIDOS],
                                           key=lambda s: s[1])]


def preparar(eventos, cat, total):
    """Valida los efectos y calcula en qué milisegundo entra cada uno."""
    listos, avisos = [], []
    for ev in eventos:
        nombre = str(ev.get("sonido", "")).strip()
        ficha = cat.get(nombre)
        if not ficha:
            avisos.append("no existe el sonido '{0}'".format(nombre))
            continue
        archivo = c.SFX / ficha["archivo"]
        if not archivo.is_file():
            avisos.append("falta el archivo {0}".format(ficha["archivo"]))
            continue
        t = float(ev.get("t", 0))
        if t < 0 or t > total:
            avisos.append("'{0}' cae en {1:.2f} s, fuera del vídeo "
                          "({2:.2f} s)".format(nombre, t, total))
            continue
        dur = float(ficha.get("duracion", 1.0))
        if ev.get("alinear", ficha.get("alinear", "inicio")) == "final":
            arranque = t - dur
            if arranque < 0:
                avisos.append("'{0}' necesita {1:.1f} s de carrerilla y solo "
                              "hay {2:.1f} s: entra recortado".format(
                                  nombre, dur, t))
                arranque = 0.0
        else:
            arranque = t
        listos.append({
            "sonido": nombre,
            "archivo": archivo,
            "retardo": int(round(arranque * 1000)),
            "ganancia": max(float(ev.get("ganancia",
                                         ficha.get("ganancia", 0.35))), 0.0),
            "t": t,
        })
    listos.sort(key=lambda e: e["retardo"])
    if len(listos) > MAX_EVENTOS:
        avisos.append("hay {0} efectos; se usan los {1} primeros".format(
            len(listos), MAX_EVENTOS))
        listos = listos[:MAX_EVENTOS]
    return listos, avisos


# ── montaje del audio ──────────────────────────────────────────────────────


FORMATO = "aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo"


def cerrar(proyecto, refrescar=False, sin_efectos=False, sin_nivelar=False):
    estado = c.cargar_proyecto(proyecto)
    carpeta = Path(estado["_carpeta"])
    montaje = c.trabajo(estado, "montaje.mp4")
    if not montaje.is_file():
        raise FileNotFoundError(
            "Falta trabajo/montaje.mp4. Corre antes:\n"
            "  python scripts/componer.py \"{0}\"".format(carpeta)
        )
    salida = carpeta / (carpeta.name + "-vertical.mp4")
    if salida.is_file() and not refrescar:
        print("Ya existe {0}. Usa --refrescar para rehacerlo.".format(salida.name))
        return salida

    total = c.duracion(montaje)
    tiene_voz = c.info_media(montaje)["tiene_audio"]

    archivo_sfx = c.trabajo(estado, "sfx.json")
    datos_sfx = c.leer_json(archivo_sfx, None)
    if datos_sfx is None:
        propuesta = eventos_por_defecto(estado, total)
        c.escribir_json(archivo_sfx, {
            "_leeme": ("Efectos de sonido del vídeo. 't' son segundos del vídeo "
                       "montado. 'ganancia' es el volumen (1.0 = original). Los "
                       "nombres disponibles están en assets/sfx/sonidos.json. "
                       "Cambia lo que quieras y vuelve a correr sonido.py "
                       "con --refrescar."),
            "eventos": propuesta,
        })
        datos_sfx = {"eventos": propuesta}
        if propuesta:
            print("Propuesta de efectos guardada en trabajo/sfx.json "
                  "({0} efectos).".format(len(propuesta)))

    eventos = [] if sin_efectos else list(datos_sfx.get("eventos") or [])
    listos, avisos = preparar(eventos, catalogo(), total)
    for aviso in avisos:
        print("  ! {0}".format(aviso))

    # Caso simple: nada que mezclar y nada que nivelar.
    if not listos and (not tiene_voz or sin_nivelar):
        c.correr_ffmpeg(["-i", str(montaje), "-c", "copy",
                         "-movflags", "+faststart", str(salida)])
        return _terminar(estado, salida, 0, tiene_voz)

    medida = None
    if tiene_voz and not sin_nivelar:
        print("Midiendo el volumen de la voz…")
        medida = medir_voz(montaje)
        if medida:
            print("  la voz está en {0:.1f} LUFS; se lleva a {1:.0f}".format(
                float(medida["input_i"]), LUFS_OBJETIVO))
        else:
            print("  ! No he podido medirla; se nivela al vuelo, que es "
                  "algo peor pero funciona.")

    entradas = ["-i", str(montaje)]
    filtros, mezclar = [], []

    if tiene_voz:
        cadena = "[0:a]" + FORMATO
        if not sin_nivelar:
            cadena += "," + filtro_voz(medida) + "," + FORMATO
        filtros.append(cadena + "[voz]")
        mezclar.append("voz")
    elif listos:
        # Sin voz hay que inventar un silencio de base: amix necesita algo
        # que marque la duración.
        filtros.append("anullsrc=r=48000:cl=stereo,atrim=0:{0:.3f}[voz]".format(
            total))
        mezclar.append("voz")

    for i, ev in enumerate(listos):
        entradas += ["-i", str(ev["archivo"])]
        cadena = "[{0}:a]{1},volume={2:.3f}".format(i + 1, FORMATO,
                                                    ev["ganancia"])
        if ev["retardo"] > 0:
            cadena += ",adelay={0}|{0}".format(ev["retardo"])
        filtros.append(cadena + "[e{0}]".format(i))
        mezclar.append("e{0}".format(i))

    if len(mezclar) > 1:
        filtros.append("{0}amix=inputs={1}:normalize=0:dropout_transition=0"
                       "[cruda]".format("".join("[" + m + "]" for m in mezclar),
                                        len(mezclar)))
        ultimo = "cruda"
    else:
        ultimo = mezclar[0]
    # El limitador es la red de seguridad: los efectos sumados a la voz
    # pueden pasarse de 0 dB y ahí es donde cruje el audio.
    filtros.append("[{0}]alimiter=limit=0.95:level=disabled,{1}[aout]".format(
        ultimo, FORMATO))

    print("Cerrando el vídeo: {0} efectos de sonido…".format(len(listos)))
    c.correr_ffmpeg(entradas + [
        "-filter_complex", ";".join(filtros),
        "-map", "0:v", "-map", "[aout]",
        "-t", "{0:.3f}".format(total),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-movflags", "+faststart", str(salida),
    ])
    return _terminar(estado, salida, len(listos), tiene_voz)


def _terminar(estado, salida, n_efectos, tiene_voz):
    info = c.info_media(salida)
    megas = salida.stat().st_size / 1048576.0
    estado.setdefault("pasos", {})["sonido"] = "ok"
    estado["salida"] = str(salida)
    c.guardar_proyecto(estado)

    print("\n✓ Vídeo terminado")
    print("  {0}".format(salida))
    print("  {0}x{1} · {2} · {3:.1f} MB · {4}".format(
        info["ancho"], info["alto"], c.hhmmss(info["duracion"]), megas,
        "con audio" if tiene_voz else "sin audio"))
    if n_efectos:
        print("  {0} efectos de sonido mezclados".format(n_efectos))
    print("\nSiguiente paso: ábrelo y míralo entero antes de publicarlo.")
    print("  Si quieres cambiar algo:")
    print("    · subtítulos mal escritos → trabajo/correcciones.json")
    print("    · cortes de más o de menos → plan_cortes.py --umbral")
    print("    · efectos de sonido        → trabajo/sfx.json")
    return salida


def main():
    ap = argparse.ArgumentParser(description="Mezcla el sonido y cierra el vídeo")
    ap.add_argument("proyecto")
    ap.add_argument("--refrescar", action="store_true")
    ap.add_argument("--sin-efectos", action="store_true",
                    dest="sin_efectos", help="solo nivelar la voz")
    ap.add_argument("--sin-nivelar", action="store_true",
                    dest="sin_nivelar", help="no tocar el volumen de la voz")
    a = ap.parse_args()
    try:
        cerrar(a.proyecto, a.refrescar, a.sin_efectos, a.sin_nivelar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
