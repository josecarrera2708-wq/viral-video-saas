#!/usr/bin/env python3
"""Instala ffmpeg dentro del propio kit, sin tocar nada del ordenador.

Uso:
  python scripts/instalar_ffmpeg.py            instalar si falta
  python scripts/instalar_ffmpeg.py --forzar   volver a descargar
  python scripts/instalar_ffmpeg.py --json     resultado para que lo lea Claude

ffmpeg es el programa que corta, recomprime y mezcla el vídeo: sin él el kit no
puede hacer nada. Lo normal sería instalarlo en el sistema (con Homebrew en Mac o
winget en Windows), pero eso pide contraseña de administrador o un gestor de
paquetes que puede no estar. Así que aquí se hace de otra forma: se descarga una
copia suelta de ffmpeg y ffprobe y se deja en la carpeta `bin/` del kit.

Ventajas de hacerlo así:
  · no pide contraseña ni permisos de administrador
  · no cambia nada fuera de la carpeta del kit (se borra borrando `bin/`)
  · funciona igual en Mac (Intel y Apple) y en Windows
  · no depende del PATH: el kit mira su propio `bin/` antes que nada

Son unos 20 MB comprimidos por programa, 40 MB en total. Se descargan una vez.
"""
from __future__ import annotations

import argparse
import gzip
import json
import platform
import shutil
import stat
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

# Compilaciones sueltas de ffmpeg, un archivo por programa y por procesador.
# Se fija una versión concreta a propósito: "la última" cambia sin avisar y un
# día dejaría de funcionar sin que nadie hubiera tocado el kit.
VERSION = "b6.1.1"
BASE = ("https://github.com/eugeneware/ffmpeg-static/releases/download/"
        + VERSION + "/")

# (sistema, procesador) → sufijo del archivo que hay que descargar
PLATAFORMAS = {
    ("Darwin", "arm64"): "darwin-arm64",     # Mac con chip Apple (M1 y siguientes)
    ("Darwin", "x86_64"): "darwin-x64",      # Mac con Intel
    ("Windows", "AMD64"): "win32-x64",
    ("Windows", "x86_64"): "win32-x64",
    ("Linux", "x86_64"): "linux-x64",
    ("Linux", "aarch64"): "linux-arm64",
}

# Si la descarga no es posible, esto es lo que hay que decirle al usuario.
ALTERNATIVA = {
    "Darwin": ("Instalar ffmpeg en el sistema con Homebrew:\n"
               "  brew install ffmpeg\n"
               "(si no tienes Homebrew, en brew.sh está el instalador; pide la "
               "contraseña del ordenador)"),
    "Windows": ("Instalar ffmpeg en el sistema con winget, que ya viene en "
                "Windows:\n"
                "  winget install --id Gyan.FFmpeg -e "
                "--accept-source-agreements"),
    "Linux": "sudo apt install -y ffmpeg",
}


def _plataforma():
    sistema = platform.system()
    maquina = platform.machine()
    sufijo = PLATAFORMAS.get((sistema, maquina))
    if sufijo:
        return sufijo
    # Windows de 32 bits o un procesador raro: no hay compilación preparada.
    raise c.FaltaDependencia(
        "No tengo una copia de ffmpeg preparada para este ordenador "
        "({0} {1}).\n{2}".format(sistema, maquina,
                                 ALTERNATIVA.get(sistema, "Instala ffmpeg.")))


def _barra(hechos, total, ancho=28):
    if not total:
        return "{0:.1f} MB".format(hechos / 1e6)
    lleno = int(ancho * hechos / total)
    return "[{0}{1}] {2:.0f}%".format("#" * lleno, "·" * (ancho - lleno),
                                      100 * hechos / total)


def descargar(url, destino, etiqueta):
    """Descarga un .gz y lo deja descomprimido y ejecutable en destino."""
    peticion = urllib.request.Request(
        url, headers={"User-Agent": "kit-editor-video"})
    trozos, hechos, ultimo = [], 0, 0.0
    with urllib.request.urlopen(peticion, timeout=60) as respuesta:
        total = int(respuesta.headers.get("Content-Length") or 0)
        while True:
            trozo = respuesta.read(262144)
            if not trozo:
                break
            trozos.append(trozo)
            hechos += len(trozo)
            ahora = time.time()
            if ahora - ultimo > 0.6:
                ultimo = ahora
                sys.stdout.write("\r  {0}  {1}".format(
                    etiqueta, _barra(hechos, total)))
                sys.stdout.flush()
    sys.stdout.write("\r  {0}  {1}\n".format(etiqueta, _barra(hechos, hechos)))

    crudo = gzip.decompress(b"".join(trozos))
    # Se escribe con otro nombre y se renombra al final: si la descarga se corta
    # a medias no queda un ffmpeg roto ocupando el sitio del bueno.
    temporal = destino.with_suffix(destino.suffix + ".parcial")
    temporal.write_bytes(crudo)
    temporal.chmod(temporal.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
                   | stat.S_IXOTH)
    if destino.exists():
        destino.unlink()
    temporal.rename(destino)
    return len(crudo)


def asegurar(forzar=False, silencioso=False):
    """Deja ffmpeg y ffprobe funcionando. Devuelve un resumen de lo que hizo."""
    def decir(*a):
        if not silencioso:
            print(*a)

    c._cache_binarios.clear()
    if not forzar:
        ya = {n: c.buscar_binario(n) for n in ("ffmpeg", "ffprobe")}
        if all(ya.values()):
            decir("ffmpeg ya funciona en este ordenador:")
            decir("  " + ya["ffmpeg"])
            return {"instalado": False, "motivo": "ya estaba",
                    "ffmpeg": ya["ffmpeg"], "ffprobe": ya["ffprobe"]}

    sufijo = _plataforma()
    extension = ".exe" if c.ES_WINDOWS else ""
    c.BIN.mkdir(parents=True, exist_ok=True)

    decir("Descargando ffmpeg para {0}. Son unos 40 MB, una sola vez.".format(
        sufijo))
    descargados = {}
    for nombre in ("ffmpeg", "ffprobe"):
        destino = c.BIN / (nombre + extension)
        try:
            tamano = descargar(BASE + nombre + "-" + sufijo + ".gz", destino,
                               nombre)
        except (urllib.error.URLError, OSError, EOFError) as e:
            raise c.FaltaDependencia(
                "No he podido descargar {0}.\n"
                "Detalle: {1}\n\n"
                "Puede ser la conexión, o una red de empresa que bloquea "
                "GitHub. Otra vía:\n{2}".format(
                    nombre, e, ALTERNATIVA.get(platform.system(), "")))
        descargados[nombre] = (destino, tamano)

    # Existir no es funcionar: se comprueba que arranca de verdad antes de
    # decir que está instalado.
    c._cache_binarios.clear()
    resultado = {}
    for nombre, (destino, tamano) in descargados.items():
        if not c._arranca(destino):
            raise c.FaltaDependencia(
                "He descargado {0} pero este ordenador no lo deja arrancar.\n"
                "Prueba la otra vía:\n{1}".format(
                    nombre, ALTERNATIVA.get(platform.system(), "")))
        resultado[nombre] = str(destino)
        decir("  ✓ {0} listo ({1:.0f} MB)".format(nombre, tamano / 1e6))

    version = "?"
    try:
        primera = c.correr([resultado["ffmpeg"], "-version"]).splitlines()[0]
        version = primera.split(" ")[2]
    except (RuntimeError, IndexError):
        pass

    # Sin estos dos codificadores no se puede crear vídeo ni sonido.
    faltan = []
    try:
        encoders = c.correr([resultado["ffmpeg"], "-hide_banner", "-encoders"])
        faltan = [x for x in ("libx264", "aac") if x not in encoders]
    except RuntimeError:
        pass
    if faltan:
        raise c.FaltaDependencia(
            "La copia descargada no trae {0}. Es raro; prueba la otra vía:\n"
            "{1}".format(" ni ".join(faltan),
                         ALTERNATIVA.get(platform.system(), "")))

    decir("\nffmpeg {0} instalado dentro del kit, en la carpeta bin/.".format(
        version))
    decir("No se ha cambiado nada del ordenador: borrando esa carpeta "
          "desaparece.")
    return {"instalado": True, "version": version, "plataforma": sufijo,
            "ffmpeg": resultado["ffmpeg"], "ffprobe": resultado["ffprobe"]}


def borrar():
    """Quita la copia del kit. Útil para probar el wizard desde cero."""
    if c.BIN.is_dir():
        shutil.rmtree(c.BIN)
        print("Borrada la carpeta bin/ del kit.")
    else:
        print("No había nada que borrar.")


def main():
    ap = argparse.ArgumentParser(description="Instala ffmpeg dentro del kit")
    ap.add_argument("--forzar", action="store_true",
                    help="descargar aunque ya haya un ffmpeg que funcione")
    ap.add_argument("--json", action="store_true", dest="como_json")
    ap.add_argument("--borrar", action="store_true",
                    help="quitar la copia del kit")
    a = ap.parse_args()

    if a.borrar:
        borrar()
        return 0
    try:
        resumen = asegurar(a.forzar, silencioso=a.como_json)
    except c.FaltaDependencia as e:
        if a.como_json:
            print(json.dumps({"ok": False, "error": str(e)},
                             indent=2, ensure_ascii=False))
        else:
            print("\n{0}".format(e), file=sys.stderr)
        return 1
    if a.como_json:
        resumen["ok"] = True
        print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
