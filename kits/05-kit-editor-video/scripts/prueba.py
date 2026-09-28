#!/usr/bin/env python3
"""Prueba de instalación: fabrica un vídeo y lo edita de principio a fin.

Uso:
  python scripts/prueba.py            hacer la prueba
  python scripts/prueba.py --json     resultado para que lo lea Claude
  python scripts/prueba.py --limpiar  borrar el proyecto de prueba

Esto es lo que decide si el kit está bien instalado. No comprueba que los
programas existan (eso lo hace doctor.py): comprueba que **hacen su trabajo**.
Fabrica un vídeo horizontal con voz de verdad y silencios metidos a propósito,
y lo pasa por toda la cadena: transcribir, decidir los cortes, pasar a vertical,
dibujar los subtítulos, montar y mezclar el sonido.

La voz la pone el propio ordenador: Mac y Windows traen un lector de textos de
serie. Si este ordenador no tiene ninguno, la prueba sigue con tonos y avisa de
que la transcripción se ha quedado sin comprobar.

Al final dice qué ha salido bien y qué no, con el vídeo terminado para verlo.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

# El nombre pasa por slug() como cualquier proyecto: así la carpeta que se crea
# es exactamente la que este script espera encontrar después.
NOMBRE = c.slug("prueba-del-kit")
MATERIAL = NOMBRE + "-material"

# Tres frases con pausas largas entre ellas. La segunda lleva un tropiezo a
# propósito (dice dos veces lo mismo seguido, como cuando repites una toma):
# así la prueba también comprueba que el kit se queda con la segunda.
FRASES = [
    "Esto es la prueba de instalación del kit de edición.",
    "El vídeo se corta, el vídeo se corta solo.",
    "Si ves este vídeo con subtítulos, está todo listo.",
]
SILENCIO = 1.30      # segundos de silencio entre frases: el kit debe cortarlos
ANCHO_CRUDO, ALTO_CRUDO = 1920, 1080
FPS_CRUDO = 30

# Lectores de textos que vienen de serie en cada sistema, con una voz española.
VOCES_MAC = ["Monica", "Mónica", "Paulina", "Jorge", "Diego", "Juan", "Marisol"]


class Fallo(RuntimeError):
    """La prueba no ha podido terminar. El mensaje explica dónde se ha roto."""


# ── fabricar el vídeo de prueba ────────────────────────────────────────────


def _voz_mac(texto, destino):
    voces = c.correr(["say", "-v", "?"]) if shutil.which("say") else ""
    elegida = next((v for v in VOCES_MAC if v in voces), None)
    if not elegida:
        # Sin voz española, con la del sistema: whisper detectará el idioma.
        elegida = None
    cmd = ["say"]
    if elegida:
        cmd += ["-v", elegida]
    aiff = destino.with_suffix(".aiff")
    c.correr(cmd + ["-o", str(aiff), texto])
    return aiff, ("es" if elegida else None)


def _voz_windows(texto, destino):
    # System.Speech viene con Windows; escribe directamente un WAV.
    guion = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$es = $s.GetInstalledVoices() | Where-Object "
        "{ $_.VoiceInfo.Culture.TwoLetterISOLanguageName -eq 'es' } | "
        "Select-Object -First 1; "
        "if ($es) { $s.SelectVoice($es.VoiceInfo.Name) }; "
        "$s.SetOutputToWaveFile('" + str(destino) + "'); "
        "$s.Speak('" + texto.replace("'", "''") + "'); "
        "$s.Dispose(); "
        "if ($es) { 'es' } else { 'otro' }"
    )
    salida = c.correr(["powershell", "-NoProfile", "-Command", guion])
    return destino, ("es" if "es" in salida else None)


def _voz_linux(texto, destino):
    if not shutil.which("espeak-ng") and not shutil.which("espeak"):
        raise Fallo("sin lector de textos")
    programa = shutil.which("espeak-ng") or shutil.which("espeak")
    c.correr([programa, "-v", "es", "-w", str(destino), texto])
    return destino, "es"


def hablar(texto, destino):
    """Convierte un texto en un archivo de audio. Devuelve (archivo, idioma)."""
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            return _voz_mac(texto, destino)
        if sistema == "Windows":
            return _voz_windows(texto, destino)
        return _voz_linux(texto, destino)
    except (RuntimeError, OSError) as e:
        raise Fallo(str(e))


def fabricar_video(carpeta):
    """Deja en carpeta/crudo.mp4 un vídeo horizontal con voz y silencios.

    Devuelve (ruta, idioma o None). Si el idioma es None, el audio no lleva voz
    reconocible y la transcripción no se puede dar por comprobada.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    piezas, idioma, con_voz = [], None, True

    for i, frase in enumerate(FRASES):
        crudo = carpeta / "voz{0}.raw".format(i)
        try:
            archivo, idioma_voz = hablar(frase, crudo.with_suffix(".wav"))
            idioma = idioma or idioma_voz
        except Fallo:
            con_voz = False
            break
        # Todo al mismo formato: el pegado exige que las piezas sean iguales.
        limpio = carpeta / "voz{0}-ok.wav".format(i)
        c.correr_ffmpeg(["-i", str(archivo), "-ac", "2", "-ar", "48000",
                         "-c:a", "pcm_s16le", str(limpio)])
        piezas.append(limpio)

    silencio = carpeta / "silencio.wav"
    c.correr_ffmpeg(["-f", "lavfi", "-i",
                     "anullsrc=r=48000:cl=stereo", "-t", str(SILENCIO),
                     "-c:a", "pcm_s16le", str(silencio)])

    if not con_voz:
        # Sin lector de textos: dos pitidos separados por silencio. Se comprueba
        # todo menos la transcripción.
        tono = carpeta / "tono.wav"
        c.correr_ffmpeg(["-f", "lavfi", "-i",
                         "sine=frequency=320:duration=1.6:sample_rate=48000",
                         "-ac", "2", "-c:a", "pcm_s16le", str(tono)])
        piezas = [tono, tono]
        idioma = None

    orden = [silencio]
    for pieza in piezas:
        orden += [pieza, silencio]

    lista = carpeta / "pegar.txt"
    lista.write_text(
        "".join("file '{0}'\n".format(p.as_posix()) for p in orden),
        encoding="utf-8")
    pista = carpeta / "pista.wav"
    c.correr_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(lista),
                     "-c", "copy", str(pista)])

    # Imagen: el patrón de pruebas de ffmpeg, que se mueve. Al ser horizontal
    # obliga al kit a recortar a vertical de verdad.
    crudo = carpeta / "crudo.mp4"
    c.correr_ffmpeg([
        "-f", "lavfi", "-i", "testsrc2=size={0}x{1}:rate={2}".format(
            ANCHO_CRUDO, ALTO_CRUDO, FPS_CRUDO),
        "-i", str(pista), "-shortest",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        str(crudo)])

    for basura in list(carpeta.glob("voz*")) + [silencio, lista,
                                               carpeta / "tono.wav", pista]:
        if basura.exists():
            basura.unlink()
    return crudo, idioma


# ── correr la cadena ───────────────────────────────────────────────────────


def paso(titulo, cmd, avisos=None):
    """Ejecuta un paso del kit. Devuelve (ok, segundos, salida)."""
    t0 = time.time()
    proc = subprocess.run([sys.executable] + cmd, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    tardado = time.time() - t0
    salida = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0:
        cola = "\n".join(salida.strip().splitlines()[-14:])
        raise Fallo("{0}\n\n{1}".format(titulo, cola))
    print("  ✓ {0}  ({1:.1f} s)".format(titulo, tardado))
    return tardado, salida


def correr(carpeta_kit=None, con_visuales=True):
    inicio = time.time()
    carpeta = c.WORKSPACE / NOMBRE
    if carpeta.exists():
        shutil.rmtree(carpeta)
    temporal = c.WORKSPACE / MATERIAL
    if temporal.exists():
        shutil.rmtree(temporal)

    resultado = {"pasos": [], "avisos": [], "transcripcion_comprobada": False,
                 "visuales_comprobados": False}

    print("Prueba de instalación del kit\n")
    print("1 · Fabrico un vídeo de prueba con voz y silencios…")
    crudo, idioma = fabricar_video(temporal)
    info = c.info_media(crudo)
    print("  ✓ vídeo de prueba: {0}x{1}, {2:.1f} s{3}".format(
        info["ancho"], info["alto"], info["duracion"],
        "" if idioma else ", sin voz (este ordenador no tiene lector de textos)"))
    if not idioma:
        resultado["avisos"].append(
            "Este ordenador no tiene lector de textos, así que la prueba ha ido "
            "con tonos en vez de voz. Todo lo demás queda comprobado; la "
            "transcripción se comprobará con tu primer vídeo de verdad.")

    print("\n2 · Paso el vídeo por toda la cadena del kit…")
    ruta = str(carpeta)
    guion = str(Path(__file__).resolve().parent)

    def s(nombre):
        return str(Path(guion) / nombre)

    _, salida_nuevo = paso("proyecto creado",
                           [s("nuevo.py"), str(crudo), "--nombre", NOMBRE,
                            "--forzar"])
    orden = [("voz transcrita", [s("transcribir.py"), ruta]
              + (["--idioma", idioma] if idioma else [])),
             ("cortes decididos", [s("plan_cortes.py"), ruta]),
             ("vídeo en vertical", [s("cortar.py"), ruta]),
             ("subtítulos dibujados", [s("subtitulos.py"), ruta])]
    for titulo, cmd in orden:
        tardado, _ = paso(titulo, cmd)
        resultado["pasos"].append({"paso": titulo, "segundos": round(tardado, 1)})

    if con_visuales:
        # Un rótulo, para comprobar la cadena de los visuales completa.
        c.escribir_json(carpeta / "trabajo" / "visuales.json", {
            "visuales": [{"nombre": "prueba", "plantilla": "rotulo",
                          "inicio": 0.6,
                          "datos": {"texto": "Instalación", "sub": "correcta",
                                    "visible": 1.4}}]})
        try:
            paso("rótulo generado", [s("capturar.py"), ruta])
            resultado["visuales_comprobados"] = True
        except Fallo as e:
            print("  ! rótulos y mockups: no disponibles (es opcional)")
            resultado["avisos"].append(
                "Los visuales (rótulos y mockups) no funcionan en este "
                "ordenador. El resto del kit sí. Detalle: "
                + str(e).splitlines()[-1][:200])

    for titulo, cmd in [("montaje con subtítulos", [s("componer.py"), ruta]),
                        ("sonido mezclado", [s("sonido.py"), ruta])]:
        tardado, _ = paso(titulo, cmd)
        resultado["pasos"].append({"paso": titulo, "segundos": round(tardado, 1)})

    # ── comprobar el resultado, no solo que no ha dado error ──────────────
    print("\n3 · Reviso el vídeo terminado…")
    estado = c.cargar_proyecto(carpeta)
    final = Path(estado.get("salida") or "")
    if not final.is_file():
        raise Fallo("La cadena ha terminado sin errores pero no encuentro el "
                    "vídeo final.")

    info_final = c.info_media(final)
    problemas = []
    if (info_final["ancho"], info_final["alto"]) != (c.ANCHO, c.ALTO):
        problemas.append("el vídeo final mide {0}x{1} y debería medir {2}x{3}"
                         .format(info_final["ancho"], info_final["alto"],
                                 c.ANCHO, c.ALTO))
    if not info_final["tiene_audio"]:
        problemas.append("el vídeo final se ha quedado sin sonido")
    if info_final["duracion"] < 1.0:
        problemas.append("el vídeo final dura {0:.1f} s: algo se ha perdido"
                         .format(info_final["duracion"]))
    if info_final["duracion"] >= info["duracion"] - 0.5:
        problemas.append("no se ha recortado ningún silencio (el vídeo final "
                         "dura lo mismo que el original)")

    subs = c.leer_json(carpeta / "trabajo" / "subs.json", {})
    grupos = subs.get("grupos") or []
    if idioma:
        if not grupos:
            problemas.append("la transcripción no ha encontrado ninguna "
                             "palabra en un audio que sí lleva voz")
        else:
            resultado["transcripcion_comprobada"] = True

    # La frase con tropiezo debería haberse quedado en una sola toma. Esto no
    # se exige: depende de que la voz del ordenador se entienda bien. Si sale,
    # se dice, porque es la parte que más sorprende a quien prueba el kit.
    plan = c.leer_json(carpeta / "trabajo" / "plan-cortes.json", {})
    tomas = [s for s in (plan.get("segmentos") or [])
             if "toma repetida" in (s.get("motivo") or "")]
    resultado["toma_repetida_detectada"] = bool(tomas)

    print("  ✓ {0}x{1}, {2:.2f} s (el original duraba {3:.2f} s)".format(
        info_final["ancho"], info_final["alto"], info_final["duracion"],
        info["duracion"]))
    print("  ✓ sonido: {0}".format("sí" if info_final["tiene_audio"] else "no"))
    if grupos:
        muestra = " · ".join(" ".join(g.get("palabras") or []) for g in grupos[:3])
        print("  ✓ {0} grupos de subtítulos. Los primeros: {1}".format(
            len(grupos), muestra))
    if tomas:
        print("  ✓ toma repetida quitada: {0}".format(
            tomas[0]["motivo"].split("«")[-1].rstrip("»")))

    if problemas:
        raise Fallo("El vídeo ha salido, pero mal:\n  · "
                    + "\n  · ".join(problemas))

    resultado.update({
        "ok": True,
        "video": str(final),
        "duracion_original": round(info["duracion"], 2),
        "duracion_final": round(info_final["duracion"], 2),
        "grupos_subtitulos": len(grupos),
        "muestra_subtitulos": " ".join(
            " ".join(g.get("palabras") or []) for g in grupos[:6]),
        "segundos_totales": round(time.time() - inicio, 1),
        "carpeta": str(carpeta),
    })

    # El vídeo fabricado NO se borra aquí a propósito: mientras el proyecto de
    # prueba siga en workspace/, su 'origen' tiene que existir para poder repetir
    # cualquier paso a mano. Lo borra --limpiar, junto con el proyecto.
    return resultado


def limpiar():
    borrado = []
    for carpeta in (c.WORKSPACE / NOMBRE, c.WORKSPACE / MATERIAL):
        if carpeta.exists():
            shutil.rmtree(carpeta)
            borrado.append(carpeta.name)
    print("Borrado: {0}".format(", ".join(borrado)) if borrado
          else "No había nada de la prueba que borrar.")


def main():
    ap = argparse.ArgumentParser(description="Prueba la instalación del kit")
    ap.add_argument("--json", action="store_true", dest="como_json")
    ap.add_argument("--limpiar", action="store_true",
                    help="borrar el proyecto de prueba")
    ap.add_argument("--sin-visuales", action="store_true", dest="sin_visuales")
    a = ap.parse_args()

    if a.limpiar:
        limpiar()
        return 0

    try:
        resultado = correr(con_visuales=not a.sin_visuales)
    except (Fallo, c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        if a.como_json:
            print(json.dumps({"ok": False, "error": str(e)}, indent=2,
                             ensure_ascii=False))
        else:
            print("\n✗ La prueba se ha parado aquí:\n\n{0}".format(e),
                  file=sys.stderr)
            print("\nCópiale a Claude este mensaje entero: con eso sabe qué "
                  "arreglar.", file=sys.stderr)
        return 1

    if a.como_json:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        return 0

    print("\n✓ El kit funciona en este ordenador. "
          "Prueba completa en {0:.0f} s.".format(resultado["segundos_totales"]))
    for aviso in resultado["avisos"]:
        print("\n! {0}".format(aviso))
    print("\nEl vídeo de prueba está en:\n  {0}".format(resultado["video"]))
    print("\nCuando lo hayas visto se puede borrar:\n"
          "  python scripts/prueba.py --limpiar")
    return 0


if __name__ == "__main__":
    sys.exit(main())
