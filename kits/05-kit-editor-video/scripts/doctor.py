#!/usr/bin/env python3
"""Revisa que el kit puede trabajar en este ordenador.

Uso:
  python scripts/doctor.py             ver qué falta
  python scripts/doctor.py --instalar  instalar lo que se pueda desde Python
  python scripts/doctor.py --json      resumen para que lo lea Claude

Comprueba lo imprescindible (Python, ffmpeg, Pillow, transcripción) y lo
opcional (los visuales). Cada cosa que falte viene con el comando exacto
para arreglarla en este sistema operativo.
"""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

SISTEMA = platform.system()
MODELO_WHISPER = "small"

# ffmpeg se instala dentro del kit, sin permisos de administrador ni gestores de
# paquetes. El detalle está en instalar_ffmpeg.py.
ARREGLO_FFMPEG = "python scripts/instalar_ffmpeg.py"


class Punto:
    def __init__(self, nombre, estado, detalle="", arreglo="", clave=""):
        self.nombre = nombre
        self.estado = estado          # ok | aviso | falta
        self.detalle = detalle
        self.arreglo = arreglo
        self.clave = clave or nombre

    def a_dict(self):
        return {"nombre": self.nombre, "clave": self.clave,
                "estado": self.estado, "detalle": self.detalle,
                "arreglo": self.arreglo}


def _version_paquete(modulo, atributo="__version__"):
    try:
        mod = __import__(modulo)
        return str(getattr(mod, atributo, "instalado"))
    except ImportError:
        return None


def _codificadores():
    """Qué codificadores trae este ffmpeg. Sin libx264 no hay vídeo."""
    try:
        salida = c.correr([c.ffmpeg(), "-hide_banner", "-encoders"])
    except (c.FaltaDependencia, RuntimeError):
        return set()
    return {linea.split()[1] for linea in salida.splitlines()
            if linea.startswith(" ") and len(linea.split()) > 1}


def _carpeta_modelos():
    """Dónde deja faster-whisper los modelos que descarga."""
    import os
    base = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if base:
        raiz = Path(base)
        return raiz if raiz.name == "hub" else raiz / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def revisar():
    puntos = []

    # ── Python ──────────────────────────────────────────────────────────
    v = sys.version_info
    puntos.append(Punto(
        "Python", "ok" if v >= (3, 9) else "falta",
        "{0}.{1}.{2}".format(v.major, v.minor, v.micro),
        "" if v >= (3, 9) else "Necesitas Python 3.9 o más nuevo: "
                               "https://www.python.org/downloads/",
        clave="python"))

    # ── ffmpeg y ffprobe ────────────────────────────────────────────────
    arreglo_ffmpeg = ARREGLO_FFMPEG
    ruta_ffmpeg = c.buscar_binario("ffmpeg")
    ruta_ffprobe = c.buscar_binario("ffprobe")
    if ruta_ffmpeg and ruta_ffprobe:
        try:
            primera = c.correr([ruta_ffmpeg, "-version"]).splitlines()[0]
            version = primera.split(" ")[2] if len(primera.split(" ")) > 2 else "?"
        except RuntimeError:
            version = "?"
        puntos.append(Punto("ffmpeg", "ok", "{0} · {1}".format(version, ruta_ffmpeg),
                            clave="ffmpeg"))
        codis = _codificadores()
        faltan = [x for x in ("libx264", "aac") if x not in codis]
        puntos.append(Punto(
            "Codificadores de vídeo",
            "ok" if not faltan else "falta",
            "libx264 y aac disponibles" if not faltan
            else "falta " + " y ".join(faltan),
            "" if not faltan else
            "Tu ffmpeg viene recortado y no puede crear vídeo. Instala el "
            "completo:  " + arreglo_ffmpeg,
            clave="codificadores"))
    else:
        cual = "ffmpeg y ffprobe" if not (ruta_ffmpeg or ruta_ffprobe) else (
            "ffprobe" if ruta_ffmpeg else "ffmpeg")
        puntos.append(Punto("ffmpeg", "falta", "no encuentro " + cual,
                            arreglo_ffmpeg, clave="ffmpeg"))

    # ── Pillow: dibuja los subtítulos ───────────────────────────────────
    pil = _version_paquete("PIL", "__version__")
    puntos.append(Punto("Pillow (subtítulos)", "ok" if pil else "falta",
                        pil or "no instalado",
                        "" if pil else "python -m pip install --user Pillow",
                        clave="pillow"))
    if pil:
        try:
            c.fuente("titulo", 40, 700)
            puntos.append(Punto("Tipografías del kit", "ok",
                                "las tres cargan", clave="fuentes"))
        except Exception as e:
            puntos.append(Punto("Tipografías del kit", "falta", str(e)[:120],
                                "Vuelve a descargar el kit completo: falta la "
                                "carpeta assets/fuentes.", clave="fuentes"))
    else:
        puntos.append(Punto("Tipografías del kit", "aviso",
                            "sin Pillow no se pueden comprobar", clave="fuentes"))

    # ── transcripción ───────────────────────────────────────────────────
    fw = _version_paquete("faster_whisper")
    puntos.append(Punto("Transcripción (faster-whisper)",
                        "ok" if fw else "falta", fw or "no instalado",
                        "" if fw else "python -m pip install --user faster-whisper",
                        clave="whisper"))
    if fw:
        carpeta = _carpeta_modelos()
        descargado = list(carpeta.glob("models--Systran--faster-whisper-"
                                       + MODELO_WHISPER)) if carpeta.is_dir() else []
        puntos.append(Punto(
            "Modelo de voz '{0}'".format(MODELO_WHISPER),
            "ok" if descargado else "aviso",
            "descargado" if descargado else "se descargará al transcribir "
                                            "(unos 500 MB, solo la primera vez)",
            clave="modelo"))

    # ── visuales (opcional) ─────────────────────────────────────────────
    pw = _version_paquete("playwright")
    if not pw:
        puntos.append(Punto("Visuales (Playwright)", "aviso", "no instalado",
                            "python -m pip install --user playwright  y luego  "
                            "python -m playwright install chromium",
                            clave="playwright"))
    else:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                nav = p.chromium.launch()
                version = nav.version
                nav.close()
            puntos.append(Punto("Visuales (Playwright)", "ok",
                                "Chrome " + version, clave="playwright"))
        except Exception as e:
            puntos.append(Punto(
                "Visuales (Playwright)", "aviso",
                "instalado pero Chrome no arranca",
                "python -m playwright install chromium\n"
                "  Detalle: {0}".format(str(e).strip().splitlines()[0][:160]),
                clave="playwright"))

    # ── material del kit ────────────────────────────────────────────────
    sonidos = list(c.SFX.glob("*.mp3"))
    puntos.append(Punto("Efectos de sonido",
                        "ok" if len(sonidos) >= 10 else "aviso",
                        "{0} sonidos".format(len(sonidos)),
                        "" if len(sonidos) >= 10 else
                        "Vuelve a descargar el kit: falta assets/sfx.",
                        clave="sfx"))
    plantillas = list(c.PLANTILLAS.glob("*.html"))
    puntos.append(Punto("Plantillas visuales",
                        "ok" if len(plantillas) >= 4 else "aviso",
                        "{0} plantillas".format(len(plantillas)),
                        "" if len(plantillas) >= 4 else
                        "Vuelve a descargar el kit: falta la carpeta plantillas.",
                        clave="plantillas"))

    # ── sitio para trabajar ─────────────────────────────────────────────
    try:
        c.WORKSPACE.mkdir(parents=True, exist_ok=True)
        prueba = c.WORKSPACE / ".escritura"
        prueba.write_text("ok", encoding="utf-8")
        prueba.unlink()
        libre = shutil.disk_usage(c.WORKSPACE).free / (1024 ** 3)
        puntos.append(Punto(
            "Espacio en disco", "ok" if libre >= 5 else "aviso",
            "{0:.1f} GB libres".format(libre),
            "" if libre >= 5 else "Vas justo. Un vídeo de un minuto puede "
                                  "ocupar 2 GB mientras se monta.",
            clave="disco"))
    except OSError as e:
        puntos.append(Punto("Espacio en disco", "falta", str(e)[:120],
                            "No puedo escribir en la carpeta workspace del kit.",
                            clave="disco"))

    return puntos


# ── instalación ────────────────────────────────────────────────────────────


def instalar(puntos):
    """Instala todo lo que falte: ffmpeg dentro del kit y los paquetes de Python."""
    estado = {p.clave: p.estado for p in puntos}
    if estado.get("ffmpeg") != "ok" or estado.get("codificadores") == "falta":
        import instalar_ffmpeg
        try:
            instalar_ffmpeg.asegurar(forzar=estado.get("codificadores") == "falta")
        except c.FaltaDependencia as e:
            print("\n{0}\n".format(e))
            return False
        print()

    paquetes = {"pillow": "Pillow", "whisper": "faster-whisper",
                "playwright": "playwright"}
    pendientes = [paquetes[p.clave] for p in puntos
                  if p.clave in paquetes and p.estado != "ok"]
    hecho = []
    if pendientes:
        print("Instalando: {0}…".format(", ".join(pendientes)))
        print("(la primera vez tarda unos minutos)")
        cmd = [sys.executable, "-m", "pip", "install", "--user", "--upgrade"] \
            + pendientes
        proc = subprocess.run(cmd)
        if proc.returncode != 0:
            # Algunos Python del sistema no dejan --user; sin él suele ir.
            print("\nReintento sin --user…")
            proc = subprocess.run([sys.executable, "-m", "pip", "install",
                                   "--upgrade"] + pendientes)
        if proc.returncode != 0:
            print("\nNo he podido instalar los paquetes de Python. "
                  "Cópiame el error de arriba.")
            return False
        hecho += pendientes

    if "playwright" in [p.lower() for p in hecho] or _version_paquete("playwright"):
        print("\nDescargando el Chrome de los visuales…")
        proc = subprocess.run([sys.executable, "-m", "playwright", "install",
                               "chromium"])
        if proc.returncode != 0:
            print("Chrome no se ha descargado. Los visuales no funcionarán, "
                  "pero el resto del kit sí.")
        else:
            hecho.append("Chrome")

    if not hecho:
        print("No había nada que instalar desde Python.")
    return True


# ── salida ─────────────────────────────────────────────────────────────────

ICONO = {"ok": "✓", "aviso": "!", "falta": "✗"}


def imprimir(puntos):
    print("Revisión del kit  ·  {0} {1}\n".format(SISTEMA, platform.release()))
    ancho = max(len(p.nombre) for p in puntos)
    for p in puntos:
        print("  {0} {1}  {2}".format(ICONO[p.estado], p.nombre.ljust(ancho),
                                      p.detalle))
    faltan = [p for p in puntos if p.estado == "falta"]
    avisos = [p for p in puntos if p.estado == "aviso" and p.arreglo]

    if faltan:
        print("\nFalta esto para poder editar:")
        for p in faltan:
            print("  · {0}\n      {1}".format(p.nombre, p.arreglo))
    if avisos:
        print("\nOpcional, el kit funciona sin ello:")
        for p in avisos:
            print("  · {0}\n      {1}".format(p.nombre, p.arreglo))
    if not faltan:
        print("\n✓ Todo listo. El kit puede editar vídeo en este ordenador.")
        if avisos:
            print("  (sin los visuales solo faltarán rótulos y mockups)")
    return 0 if not faltan else 1


def main():
    ap = argparse.ArgumentParser(description="Revisa el kit")
    ap.add_argument("--json", action="store_true", dest="como_json")
    ap.add_argument("--instalar", action="store_true",
                    help="instalar los paquetes de Python que falten")
    a = ap.parse_args()

    puntos = revisar()
    if a.instalar:
        instalar(puntos)
        print("\nVuelvo a revisar…\n")
        c._cache_binarios.clear()
        puntos = revisar()

    if a.como_json:
        print(json.dumps({
            "sistema": SISTEMA,
            "listo": all(p.estado != "falta" for p in puntos),
            "visuales": next((p.estado == "ok" for p in puntos
                              if p.clave == "playwright"), False),
            "puntos": [p.a_dict() for p in puntos],
        }, indent=2, ensure_ascii=False))
        return 0
    return imprimir(puntos)


if __name__ == "__main__":
    sys.exit(main())
