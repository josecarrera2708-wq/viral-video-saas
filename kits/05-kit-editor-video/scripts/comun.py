#!/usr/bin/env python3
"""Utilidades compartidas del motor de edición.

Todo el motor pasa por aquí: localizar ffmpeg, leer datos de un vídeo,
cargar las tipografías del kit y guardar el estado del proyecto.
Funciona igual en Mac y en Windows: nada de comandos de shell, solo Python.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BIN = RAIZ / "bin"
ASSETS = RAIZ / "assets"
FUENTES = ASSETS / "fuentes"
SFX = ASSETS / "sfx"
PLANTILLAS = RAIZ / "plantillas"
WORKSPACE = RAIZ / "workspace"

# Lienzo vertical de destino (TikTok / Reels / Shorts)
ANCHO, ALTO = 1080, 1920
FPS = 60

ES_WINDOWS = platform.system() == "Windows"

# ── binarios externos ───────────────────────────────────────────────────────

# Sitios donde suele quedar ffmpeg cuando no está en el PATH. La carpeta bin/
# del propio kit va primero: ahí deja el wizard la copia portátil que descarga
# cuando el ordenador no tiene ffmpeg. Así se instala sin permisos de
# administrador y sin tocar nada del sistema.
_CANDIDATOS = {
    "Darwin": [str(BIN), "/opt/homebrew/bin", "/usr/local/bin",
               str(Path.home() / "bin")],
    "Windows": [
        str(BIN),
        r"C:\ffmpeg\bin",
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links"),
        str(Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "ffmpeg" / "bin"),
    ],
    "Linux": [str(BIN), "/usr/bin", "/usr/local/bin", "/snap/bin"],
}


_cache_binarios = {}


def _arranca(ruta):
    """Comprueba que el ejecutable realmente corre en esta máquina.

    Existir no basta: se ven instalaciones a medias y binarios compilados
    para otro procesador (un ffprobe de Intel en un Mac con chip Apple da
    'Bad CPU type'). Si no arranca, es como si no estuviera.
    """
    try:
        proc = subprocess.run(
            [str(ruta), "-version"], capture_output=True, timeout=20,
        )
        return proc.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def buscar_binario(nombre):
    """Devuelve la ruta de un ejecutable que funciona, o None."""
    if nombre in _cache_binarios:
        return _cache_binarios[nombre]
    sufijo = ".exe" if ES_WINDOWS else ""
    vistos, candidatos = set(), []
    # La copia del kit va antes que la del sistema a propósito: si está, es
    # porque la descargó el wizard, que además comprobó que trae los
    # codificadores. Un ffmpeg recortado del sistema no la puede tapar.
    for carpeta in [str(BIN)] + os.environ.get("PATH", "").split(
            os.pathsep) + _CANDIDATOS.get(platform.system(), []):
        if not carpeta or carpeta in vistos:
            continue
        vistos.add(carpeta)
        ruta = Path(carpeta) / (nombre + sufijo)
        if ruta.is_file():
            candidatos.append(str(ruta))
    elegido = next((c for c in candidatos if _arranca(c)), None)
    _cache_binarios[nombre] = elegido
    return elegido


class FaltaDependencia(RuntimeError):
    """Falta un programa necesario. El mensaje ya explica cómo instalarlo."""


def _exigir(nombre):
    ruta = buscar_binario(nombre)
    if ruta:
        return ruta
    raise FaltaDependencia(
        "No encuentro '{0}', el programa que trabaja con el vídeo.\n"
        "Se instala solo, sin permisos de administrador, con:\n"
        "  python scripts/instalar_ffmpeg.py".format(nombre)
    )


def ffmpeg():
    return _exigir("ffmpeg")


def ffprobe():
    return _exigir("ffprobe")


def correr(cmd, entrada=None, silencioso=True):
    """Ejecuta un comando y devuelve su salida. Si falla, explica por qué."""
    cmd = [str(c) for c in cmd]
    proc = subprocess.run(
        cmd, input=entrada, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        cola = (proc.stderr or proc.stdout or "").strip().splitlines()
        detalle = "\n".join(cola[-12:]) if cola else "(sin mensaje de error)"
        raise RuntimeError(
            "Falló:  {0}\n{1}".format(" ".join(cmd[:3]) + " …", detalle)
        )
    if not silencioso and proc.stderr:
        print(proc.stderr, file=sys.stderr)
    return proc.stdout


def correr_ffmpeg(args, descripcion=""):
    """ffmpeg con log mínimo. `args` no incluye el binario ni -y."""
    salida = correr([ffmpeg(), "-y", "-nostdin", "-v", "error"] + list(args))
    if descripcion:
        print("  ✓ {0}".format(descripcion))
    return salida


# ── datos de un vídeo ──────────────────────────────────────────────────────


def info_media(archivo):
    """Devuelve {duracion, ancho, alto, fps, tiene_audio, rotacion}."""
    crudo = correr([
        ffprobe(), "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(archivo),
    ])
    datos = json.loads(crudo)
    video = next((s for s in datos["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in datos["streams"] if s["codec_type"] == "audio"), None)
    info = {
        "duracion": float(datos["format"].get("duration", 0) or 0),
        "tiene_audio": audio is not None,
        "ancho": 0, "alto": 0, "fps": 0.0, "rotacion": 0,
    }
    if video:
        info["ancho"] = int(video.get("width", 0))
        info["alto"] = int(video.get("height", 0))
        num, _, den = (video.get("r_frame_rate") or "0/1").partition("/")
        try:
            info["fps"] = round(float(num) / float(den or 1), 3)
        except (ValueError, ZeroDivisionError):
            info["fps"] = 0.0
        # Vídeo de móvil: la rotación viene en metadatos, no en las dimensiones.
        for lado in video.get("side_data_list", []) or []:
            if "rotation" in lado:
                info["rotacion"] = int(lado["rotation"]) % 360
        # Si está rotado 90/270, el tamaño real que ve el reproductor va girado.
        if info["rotacion"] in (90, 270):
            info["ancho"], info["alto"] = info["alto"], info["ancho"]
    return info


def duracion(archivo):
    return info_media(archivo)["duracion"]


# ── tipografías del kit ────────────────────────────────────────────────────

_ARCHIVOS_FUENTE = {
    "titulo": FUENTES / "SpaceGrotesk-variable.ttf",   # subtítulos y números
    "mega": FUENTES / "Inter-variable.ttf",            # titulares grandes
    "mono": FUENTES / "JetBrainsMono-variable.ttf",    # terminal y etiquetas
}
_cache_fuentes = {}


def fuente(familia, tamano, peso=700):
    """Carga una tipografía del kit con el grosor pedido (100-900)."""
    from PIL import ImageFont  # import local: el doctor corre sin Pillow

    clave = (familia, tamano, peso)
    if clave in _cache_fuentes:
        return _cache_fuentes[clave]
    ruta = _ARCHIVOS_FUENTE.get(familia)
    if ruta is None or not ruta.is_file():
        raise FaltaDependencia(
            "Falta la tipografía '{0}' en assets/fuentes. Descarga el kit "
            "completo otra vez.".format(familia)
        )
    tipo = ImageFont.truetype(str(ruta), tamano)
    try:
        ejes = [a["name"].decode() if isinstance(a["name"], bytes) else a["name"]
                for a in tipo.get_variation_axes()]
        valores = []
        for nombre in ejes:
            valores.append(peso if nombre.lower().startswith("weight") else None)
        # Los ejes que no sean el grosor se quedan en su valor por defecto.
        defectos = [a["default"] for a in tipo.get_variation_axes()]
        valores = [v if v is not None else d for v, d in zip(valores, defectos)]
        tipo.set_variation_by_axes(valores)
    except Exception:
        pass  # fuente estática o FreeType sin soporte: se usa tal cual
    _cache_fuentes[clave] = tipo
    return tipo


# ── proyecto ───────────────────────────────────────────────────────────────

NOMBRE_ESTADO = "proyecto.json"


def carpeta_proyecto(ruta):
    """Acepta la carpeta del proyecto o su proyecto.json."""
    p = Path(ruta).expanduser().resolve()
    return p.parent if p.name == NOMBRE_ESTADO else p


_SIN_DEFECTO = object()   # para poder pedir None como valor por defecto


def leer_json(archivo, por_defecto=_SIN_DEFECTO):
    """Lee un JSON. Sin valor por defecto, la falta del archivo es un error."""
    archivo = Path(archivo)
    if not archivo.is_file():
        if por_defecto is _SIN_DEFECTO:
            raise FileNotFoundError("No existe {0}".format(archivo))
        return por_defecto
    return json.loads(archivo.read_text(encoding="utf-8"))


def escribir_json(archivo, datos):
    archivo = Path(archivo)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(
        json.dumps(datos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return archivo


def cargar_proyecto(ruta):
    carpeta = carpeta_proyecto(ruta)
    archivo = carpeta / NOMBRE_ESTADO
    if not archivo.is_file():
        raise FileNotFoundError(
            "No hay ningún proyecto en {0} (falta {1}). Empieza con "
            "nuevo.py \"<vídeo>\".".format(carpeta, NOMBRE_ESTADO)
        )
    estado = leer_json(archivo)
    estado["_carpeta"] = str(carpeta)
    return estado


def ruta_origen(estado):
    """El vídeo original del proyecto, comprobando que siga estando ahí.

    Los pasos que releen el original (transcribir, encuadre, cortar) pasan por
    aquí: si el archivo se movió o se renombró después de crear el proyecto, el
    error lo explica en vez de dejar que ffmpeg diga 'No such file'.
    """
    origen = Path(estado.get("origen", ""))
    if not origen.is_file():
        raise FileNotFoundError(
            "No encuentro el vídeo original en {0}. Corrige 'origen' en "
            "proyecto.json.".format(origen)
        )
    return origen


def guardar_proyecto(estado):
    carpeta = Path(estado["_carpeta"])
    copia = {k: v for k, v in estado.items() if not k.startswith("_")}
    escribir_json(carpeta / NOMBRE_ESTADO, copia)
    return carpeta / NOMBRE_ESTADO


def trabajo(estado, *partes):
    """Ruta dentro de la carpeta de archivos intermedios del proyecto."""
    ruta = Path(estado["_carpeta"]) / "trabajo"
    for parte in partes:
        ruta = ruta / parte
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def slug(texto, maximo=40):
    import re
    limpio = re.sub(r"[^a-z0-9]+", "-", texto.lower().strip())
    limpio = re.sub(r"-+", "-", limpio).strip("-")
    return (limpio or "video")[:maximo]


def hhmmss(segundos):
    segundos = max(float(segundos), 0.0)
    m, s = divmod(segundos, 60)
    return "{0:d}:{1:05.2f}".format(int(m), s)
