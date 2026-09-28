#!/usr/bin/env python3
"""Convierte las plantillas HTML en secuencias de imágenes con transparencia.

Uso:  python scripts/capturar.py <carpeta-del-proyecto>

Lee trabajo/visuales.json, abre cada plantilla en un Chrome sin ventana y le
pide fotograma a fotograma que se coloque en un instante concreto. No se graba
la pantalla: se pide el fotograma 12 y se guarda el fotograma 12. Por eso el
resultado es idéntico siempre, aunque el ordenador vaya lento.

Formato de trabajo/visuales.json:
  {"visuales": [
     {"nombre": "rot1", "plantilla": "rotulo", "inicio": 1.4,
      "datos": {"texto": "Paso 1", "sub": "Instalar"}}
  ]}

Salida:
  trabajo/visuales/<nombre>-00000.png …
  trabajo/timeline.json   (con las capas ya colocadas, listas para componer)
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

FPS_CAPTURA = 30   # el motor lo sube a 60 al montar; a 60 aquí tarda el doble

# Dónde cae cada plantilla en el lienzo vertical. Pensado para no chocar con
# los subtítulos (que van sobre y=1300) ni con la interfaz de la red social.
COLOCACION = {
    "rotulo": {"x": 0, "y": 980},
    "titulo": {"x": 0, "y": 300},
    "mockup-terminal": {"x": 0, "y": 400},
    "mockup-movil": {"x": 0, "y": 190},
    "recap": {"x": 0, "y": 360},
    "cta": {"x": 0, "y": 540},
}

AYUDA_PLAYWRIGHT = (
    "Faltan los visuales (Playwright y su Chrome). Instálalos con:\n"
    "  python -m pip install playwright\n"
    "  python -m playwright install chromium\n"
    "Tarda un par de minutos la primera vez. Si no los quieres, el vídeo se "
    "monta igual sin rótulos ni mockups: sáltate este paso."
)


def plantillas_disponibles():
    return sorted(p.stem for p in c.PLANTILLAS.glob("*.html"))


def _abrir_navegador():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise c.FaltaDependencia(AYUDA_PLAYWRIGHT)
    try:
        pw = sync_playwright().start()
    except Exception as e:
        raise c.FaltaDependencia("{0}\n\nDetalle: {1}".format(AYUDA_PLAYWRIGHT, e))
    try:
        navegador = pw.chromium.launch(args=["--force-color-profile=srgb",
                                             "--disable-lcd-text"])
    except Exception as e:
        pw.stop()
        raise c.FaltaDependencia("{0}\n\nDetalle: {1}".format(AYUDA_PLAYWRIGHT, e))
    return pw, navegador


def capturar_una(navegador, visual, destino, fps=FPS_CAPTURA, solo_una=False):
    """Genera las imágenes de un visual. Devuelve su entrada para el timeline."""
    nombre_plantilla = visual.get("plantilla", "")
    archivo = c.PLANTILLAS / (nombre_plantilla + ".html")
    if not archivo.is_file():
        raise FileNotFoundError(
            "No existe la plantilla '{0}'. Las que hay: {1}".format(
                nombre_plantilla, ", ".join(plantillas_disponibles()))
        )
    nombre = c.slug(visual.get("nombre") or nombre_plantilla)
    datos = visual.get("datos") or {}

    pagina = navegador.new_page(viewport={"width": c.ANCHO, "height": c.ALTO},
                                device_scale_factor=1)
    try:
        errores = []
        pagina.on("pageerror", lambda e: errores.append(str(e)))
        pagina.goto(archivo.resolve().as_uri())
        # Sin esperar a las tipografías, los primeros fotogramas salen con la
        # letra del sistema y se ve el cambio.
        pagina.wait_for_function("document.fonts.status === 'loaded'", timeout=15000)
        pagina.wait_for_function("typeof window.cargar === 'function'", timeout=15000)
        lienzo = pagina.evaluate("() => window.LIENZO")
        pagina.set_viewport_size({"width": int(lienzo["ancho"]),
                                  "height": int(lienzo["alto"])})
        pagina.evaluate("d => window.cargar(d)", datos)
        duracion = float(pagina.evaluate("() => window.duracion()"))
        if errores:
            raise RuntimeError("La plantilla '{0}' ha dado un error:\n  {1}".format(
                nombre_plantilla, errores[0]))

        carpeta = Path(destino) / "visuales"
        carpeta.mkdir(parents=True, exist_ok=True)
        for viejo in carpeta.glob(nombre + "-*.png"):
            viejo.unlink()

        total = max(int(round(duracion * fps)), 1)
        if solo_una:
            # Vista rápida: un solo fotograma del medio, para revisar el diseño.
            pagina.evaluate("t => window.fotograma(t)", duracion * 0.55)
            ruta = carpeta / (nombre + "-previa.png")
            pagina.screenshot(path=str(ruta), omit_background=True)
            print("  {0}: previa en {1}".format(nombre, ruta.name))
            return None

        for i in range(total):
            pagina.evaluate("t => window.fotograma(t)", i / float(fps))
            pagina.screenshot(path=str(carpeta / "{0}-{1:05d}.png".format(nombre, i)),
                              omit_background=True)
        if errores:
            print("  ! {0}: {1}".format(nombre, errores[0]))

        colocacion = dict(COLOCACION.get(nombre_plantilla, {"x": 0, "y": 0}))
        if "x" in visual:
            colocacion["x"] = int(visual["x"])
        if "y" in visual:
            colocacion["y"] = int(visual["y"])
        print("  {0}: {1} fotogramas, {2:.2f} s, en y={3}".format(
            nombre, total, duracion, colocacion["y"]))
        return {
            "secuencia": "visuales/" + nombre,
            "inicio": round(float(visual.get("inicio", 0)), 3),
            "fps": fps,
            "x": colocacion["x"],
            "y": colocacion["y"],
            "_plantilla": nombre_plantilla,
            "_duracion": round(duracion, 3),
        }
    finally:
        pagina.close()


def generar(proyecto, solo=None, fps=FPS_CAPTURA, previa=False, limpiar=False):
    estado = c.cargar_proyecto(proyecto)
    carpeta_trabajo = Path(estado["_carpeta"]) / "trabajo"
    archivo = carpeta_trabajo / "visuales.json"
    datos = c.leer_json(archivo, None)
    if datos is None:
        c.escribir_json(archivo, {
            "_leeme": ("Rótulos, titulares y mockups del vídeo. 'inicio' son "
                       "segundos del vídeo ya cortado. Plantillas disponibles: "
                       + ", ".join(plantillas_disponibles())),
            "visuales": [],
        })
        print("No había visuales. He creado trabajo/visuales.json vacío:\n"
              "  {0}\n"
              "Añade ahí los rótulos que quieras y vuelve a correr este paso.\n"
              "El vídeo se puede montar igualmente sin visuales.".format(archivo))
        return []

    visuales = list(datos.get("visuales") or [])
    if solo:
        visuales = [v for v in visuales
                    if c.slug(v.get("nombre") or v.get("plantilla", "")) == c.slug(solo)]
        if not visuales:
            raise FileNotFoundError(
                "No hay ningún visual llamado '{0}' en visuales.json".format(solo))
    if not visuales:
        print("visuales.json no tiene ningún visual. Nada que capturar.")
        return []

    if limpiar and (carpeta_trabajo / "visuales").is_dir():
        shutil.rmtree(carpeta_trabajo / "visuales")

    print("Generando {0} visual(es) con Chrome…".format(len(visuales)))
    pw, navegador = _abrir_navegador()
    capas = []
    try:
        for visual in visuales:
            entrada = capturar_una(navegador, visual, carpeta_trabajo, fps, previa)
            if entrada:
                capas.append(entrada)
    finally:
        navegador.close()
        pw.stop()

    if previa:
        print("\nSiguiente paso: mira las imágenes de trabajo/visuales/ y, si te "
              "gustan, corre esto sin --previa.")
        return capas

    # Se respeta lo que ya hubiera en el timeline: los zooms no se tocan y las
    # capas que no se han vuelto a generar se quedan como estaban.
    archivo_linea = carpeta_trabajo / "timeline.json"
    linea = c.leer_json(archivo_linea, {"zooms": [], "capas": [], "fijas": []})
    nuevas = {ca["secuencia"] for ca in capas}
    linea["capas"] = [ca for ca in (linea.get("capas") or [])
                      if ca.get("secuencia") not in nuevas] + capas
    linea["capas"].sort(key=lambda ca: ca.get("inicio", 0))
    linea.setdefault("zooms", [])
    linea.setdefault("fijas", [])
    c.escribir_json(archivo_linea, linea)

    estado.setdefault("pasos", {})["capturar"] = "ok"
    c.guardar_proyecto(estado)
    print("\n{0} capas colocadas en trabajo/timeline.json".format(len(capas)))
    print("\nSiguiente paso: montar el vídeo con los visuales")
    print("  python scripts/componer.py \"{0}\" --refrescar".format(
        estado["_carpeta"]))
    return capas


def main():
    ap = argparse.ArgumentParser(description="Genera los visuales del vídeo")
    ap.add_argument("proyecto")
    ap.add_argument("--solo", help="generar solo el visual con ese nombre")
    ap.add_argument("--fps", type=int, default=FPS_CAPTURA)
    ap.add_argument("--previa", action="store_true",
                    help="una sola imagen de cada visual, para revisar el diseño")
    ap.add_argument("--limpiar", action="store_true",
                    help="borrar las imágenes anteriores")
    a = ap.parse_args()
    try:
        generar(a.proyecto, a.solo, a.fps, a.previa, a.limpiar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
