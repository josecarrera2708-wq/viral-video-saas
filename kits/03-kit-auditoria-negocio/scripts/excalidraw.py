#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de mapas de proceso para el Kit 03 · Auditoría de Negocio.

Lee una especificación en JSON (nodos + flechas colocados en una rejilla) y
escribe dos cosas a partir de ella:

  1. Un archivo .excalidraw con todos los diagramas, editable en
     https://excalidraw.com o con la extensión Excalidraw de VS Code.
  2. Un .svg por diagrama, limpio y sin dependencias, para incrustar dentro del
     informe HTML.

Los dos salen de la misma especificación, así que el dibujo editable y el del
informe no pueden acabar diciendo cosas distintas.

Solo usa la librería estándar de Python 3. No instala nada.

USO
    python3 scripts/excalidraw.py ESPEC.json --salida workspace/mi-informe
        → workspace/mi-informe.excalidraw
        → workspace/mi-informe-mapa-1.svg   (uno por diagrama, con su id)

    python3 scripts/excalidraw.py --validar workspace/mi-informe.excalidraw
        → comprueba que el archivo generado es correcto

FORMATO DE LA ESPECIFICACIÓN
    {
      "titulo": "Estudio Lúa",
      "diagramas": [
        {
          "id": "mapa-1",
          "titulo": "Cómo funciona hoy",
          "nodos": [
            {"id": "a", "texto": "Clienta llama", "tipo": "inicio",
             "estado": "neutro", "col": 0, "fila": 0},
            {"id": "b", "texto": "¿Hay alguien libre?", "tipo": "decision",
             "estado": "manual", "col": 1, "fila": 0}
          ],
          "flechas": [
            {"de": "a", "a": "b", "texto": "en horario"}
          ]
        }
      ]
    }

    tipo:   caja (por defecto) · decision · inicio · fin · nota
    estado: neutro (por defecto) · manual · fuga · auto · ok
            manual = lo hace una persona a mano
            fuga   = aquí se pierde un cliente, tiempo o dinero
            auto   = va solo (se usa en el mapa de cómo funcionaría)
            ok     = ya funciona bien hoy

    Campos opcionales de un nodo:  "ancho" (columnas que ocupa, por defecto 1)
    Campos opcionales de una flecha: "texto", "estilo" ("discontinua")
"""

import argparse
import hashlib
import json
import math
import os
import sys
import textwrap

# ---------------------------------------------------------------------------
# Geometría de la rejilla
# ---------------------------------------------------------------------------

COL_ANCHO = 340          # separación horizontal entre columnas
FILA_ALTO = 180          # separación vertical entre filas
CAJA_ANCHO = 220
CAJA_ALTO = 92
DIAMANTE_ANCHO = 230
DIAMANTE_ALTO = 116
ELIPSE_ANCHO = 200
ELIPSE_ALTO = 84
NOTA_ANCHO = 230
NOTA_ALTO = 92

MARGEN = 60              # margen exterior del lienzo
ALTO_TITULO = 70         # espacio reservado para el título de cada diagrama
ALTO_LEYENDA = 64        # espacio reservado para la leyenda
SEPARACION_DIAGRAMAS = 140

TAM_TEXTO = 16
ALTO_LINEA = 21
TAM_TEXTO_FLECHA = 13
TAM_TITULO = 28
CARACTERES_POR_LINEA = 23

ANCHO_CARACTER_FLECHA = 6.9   # ancho aproximado de un carácter en las etiquetas
RELLENO_ETIQUETA = 6.0        # aire a cada lado del texto de una flecha

# ---------------------------------------------------------------------------
# Colores por estado
# ---------------------------------------------------------------------------

COLORES = {
    "neutro": {"trazo": "#1f2933", "fondo": "#f4f5f7", "etiqueta": "Paso normal"},
    "manual": {"trazo": "#b26a00", "fondo": "#fdf3e3", "etiqueta": "Lo hace una persona a mano"},
    "fuga":   {"trazo": "#c0392b", "fondo": "#fbeae7", "etiqueta": "Aquí se pierde cliente, tiempo o dinero"},
    "auto":   {"trazo": "#2f6fb2", "fondo": "#e8f1fa", "etiqueta": "Va solo, sin que nadie lo toque"},
    "ok":     {"trazo": "#1e8f5a", "fondo": "#e7f6ee", "etiqueta": "Ya funciona bien"},
}

TIPOS = ("caja", "decision", "inicio", "fin", "nota")
ESTADOS = tuple(COLORES.keys())

SELLO_TIEMPO = 1753600000000     # fijo: los archivos generados son reproducibles


class ErrorEspec(Exception):
    """La especificación de entrada tiene un problema que hay que corregir."""


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _num(semilla, tope=2147483647):
    """Entero estable derivado de un texto (ids y semillas reproducibles)."""
    digest = hashlib.md5(semilla.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % tope


def _ident(semilla):
    return hashlib.md5(semilla.encode("utf-8")).hexdigest()[:16]


def envolver(texto, ancho=CARACTERES_POR_LINEA):
    """Parte el texto en líneas respetando los saltos que ya trae escritos."""
    lineas = []
    for parrafo in str(texto).split("\n"):
        parrafo = parrafo.strip()
        if not parrafo:
            continue
        lineas.extend(textwrap.wrap(parrafo, width=ancho) or [parrafo])
    return lineas or [""]


def medidas(tipo):
    if tipo == "decision":
        return DIAMANTE_ANCHO, DIAMANTE_ALTO
    if tipo in ("inicio", "fin"):
        return ELIPSE_ANCHO, ELIPSE_ALTO
    if tipo == "nota":
        return NOTA_ANCHO, NOTA_ALTO
    return CAJA_ANCHO, CAJA_ALTO


def forma_excalidraw(tipo):
    if tipo == "decision":
        return "diamond"
    if tipo in ("inicio", "fin"):
        return "ellipse"
    return "rectangle"


def escapar(texto):
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# Validación y colocación
# ---------------------------------------------------------------------------

def validar_espec(espec):
    if not isinstance(espec, dict):
        raise ErrorEspec("La especificación debe ser un objeto JSON.")
    diagramas = espec.get("diagramas")
    if not isinstance(diagramas, list) or not diagramas:
        raise ErrorEspec("Falta la lista 'diagramas' o está vacía.")

    ids_diagrama = set()
    for i, diagrama in enumerate(diagramas, start=1):
        etiqueta = "diagrama %d" % i
        if not isinstance(diagrama, dict):
            raise ErrorEspec("El %s no es un objeto JSON." % etiqueta)

        did = diagrama.get("id") or "mapa-%d" % i
        diagrama["id"] = str(did)
        if diagrama["id"] in ids_diagrama:
            raise ErrorEspec("Hay dos diagramas con el id '%s'." % diagrama["id"])
        ids_diagrama.add(diagrama["id"])

        nodos = diagrama.get("nodos")
        if not isinstance(nodos, list) or not nodos:
            raise ErrorEspec("El %s ('%s') no tiene nodos." % (etiqueta, diagrama["id"]))

        vistos, celdas = set(), {}
        for nodo in nodos:
            if not isinstance(nodo, dict):
                raise ErrorEspec("Hay un nodo que no es un objeto JSON en '%s'." % diagrama["id"])
            for campo in ("id", "texto"):
                if not str(nodo.get(campo, "")).strip():
                    raise ErrorEspec(
                        "En '%s' hay un nodo sin '%s': %s" % (diagrama["id"], campo, json.dumps(nodo, ensure_ascii=False)))
            nid = str(nodo["id"])
            if nid in vistos:
                raise ErrorEspec("En '%s' hay dos nodos con el id '%s'." % (diagrama["id"], nid))
            vistos.add(nid)

            nodo["tipo"] = str(nodo.get("tipo") or "caja")
            if nodo["tipo"] not in TIPOS:
                raise ErrorEspec("Tipo de nodo desconocido '%s' en el nodo '%s'. Válidos: %s."
                                 % (nodo["tipo"], nid, ", ".join(TIPOS)))
            nodo["estado"] = str(nodo.get("estado") or "neutro")
            if nodo["estado"] not in ESTADOS:
                raise ErrorEspec("Estado desconocido '%s' en el nodo '%s'. Válidos: %s."
                                 % (nodo["estado"], nid, ", ".join(ESTADOS)))

            for campo, defecto in (("col", 0), ("fila", 0)):
                valor = nodo.get(campo, defecto)
                if not isinstance(valor, int) or valor < 0:
                    raise ErrorEspec("El nodo '%s' tiene '%s' inválido (%r): debe ser un entero >= 0."
                                     % (nid, campo, valor))
                nodo[campo] = valor

            celda = (nodo["col"], nodo["fila"])
            if celda in celdas:
                raise ErrorEspec(
                    "En '%s' los nodos '%s' y '%s' están en la misma casilla col=%d fila=%d: se dibujarían encima."
                    % (diagrama["id"], celdas[celda], nid, celda[0], celda[1]))
            celdas[celda] = nid

        flechas = diagrama.get("flechas") or []
        if not isinstance(flechas, list):
            raise ErrorEspec("Las 'flechas' de '%s' deben ser una lista." % diagrama["id"])
        for flecha in flechas:
            if not isinstance(flecha, dict):
                raise ErrorEspec("Hay una flecha que no es un objeto JSON en '%s'." % diagrama["id"])
            for extremo in ("de", "a"):
                if str(flecha.get(extremo, "")) not in vistos:
                    raise ErrorEspec(
                        "En '%s' una flecha apunta a '%s', que no es ningún nodo de este diagrama."
                        % (diagrama["id"], flecha.get(extremo)))
            if flecha["de"] == flecha["a"]:
                raise ErrorEspec("En '%s' hay una flecha que sale y entra en el mismo nodo ('%s')."
                                 % (diagrama["id"], flecha["de"]))
        diagrama["flechas"] = flechas
    return espec


def colocar(espec):
    """Calcula la geometría de todos los diagramas. Devuelve una lista de planos."""
    planos = []
    desplazamiento_y = 0.0

    for diagrama in espec["diagramas"]:
        nodos, cajas = diagrama["nodos"], {}
        max_col = max(n["col"] + int(n.get("ancho", 1)) - 1 for n in nodos)
        max_fila = max(n["fila"] for n in nodos)

        origen_y = desplazamiento_y + ALTO_TITULO
        for nodo in nodos:
            ancho_base, alto_base = medidas(nodo["tipo"])
            columnas = max(1, int(nodo.get("ancho", 1)))

            # El centro de un nodo depende SOLO de su casilla, nunca de su forma:
            # así los nodos de una misma columna comparten eje vertical y los de
            # una misma fila comparten eje horizontal. Si no, las flechas rectas
            # se convierten en codos y entran por donde no deben.
            centro_x = (MARGEN + nodo["col"] * COL_ANCHO + CAJA_ANCHO / 2.0
                        + (columnas - 1) * COL_ANCHO / 2.0)
            centro_y = origen_y + nodo["fila"] * FILA_ALTO + CAJA_ALTO / 2.0

            # El texto manda sobre el tamaño: una forma nunca recorta lo que dice.
            # Las elipses necesitan más margen porque la curva come las esquinas.
            es_elipse = nodo["tipo"] in ("inicio", "fin")
            por_linea = (18 if es_elipse else CARACTERES_POR_LINEA) + (columnas - 1) * 24
            lineas = envolver(nodo["texto"], por_linea)
            holgura_alto = 44 if es_elipse else 30
            holgura_ancho = 90 if es_elipse else 34
            ancho = max(ancho_base + (columnas - 1) * COL_ANCHO,
                        max(len(l) for l in lineas) * 8.4 + holgura_ancho)
            alto = max(alto_base, len(lineas) * ALTO_LINEA + holgura_alto)

            cajas[nodo["id"]] = {
                "nodo": nodo,
                "x": centro_x - ancho / 2.0,
                "y": centro_y - alto / 2.0,
                "ancho": ancho,
                "alto": alto,
                "cx": centro_x,
                "cy": centro_y,
                "lineas": lineas,
            }

        alto_contenido = max(c["y"] + c["alto"] for c in cajas.values()) - origen_y
        ancho_contenido = max(c["x"] + c["ancho"] for c in cajas.values()) - MARGEN
        planos.append({
            "diagrama": diagrama,
            "cajas": cajas,
            "titulo_y": desplazamiento_y + 8,
            "origen_y": origen_y,
            "ancho": MARGEN * 2 + ancho_contenido,
            "alto": ALTO_TITULO + alto_contenido + ALTO_LEYENDA,
            "desplazamiento_y": desplazamiento_y,
        })
        desplazamiento_y += ALTO_TITULO + alto_contenido + ALTO_LEYENDA + SEPARACION_DIAGRAMAS

    return planos


def ruta_flecha(origen, destino):
    """Puntos absolutos de una flecha entre dos cajas, en ángulo recto si hace falta."""
    dx = destino["cx"] - origen["cx"]
    dy = destino["cy"] - origen["cy"]
    hueco = 6.0

    if abs(dy) < 1:                                    # misma fila: lado a lado
        if dx >= 0:
            inicio = (origen["x"] + origen["ancho"] + hueco, origen["cy"])
            fin = (destino["x"] - hueco, destino["cy"])
        else:
            inicio = (origen["x"] - hueco, origen["cy"])
            fin = (destino["x"] + destino["ancho"] + hueco, destino["cy"])
        return [inicio, fin]

    if abs(dx) < 1:                                    # misma columna: arriba/abajo
        if dy >= 0:
            inicio = (origen["cx"], origen["y"] + origen["alto"] + hueco)
            fin = (destino["cx"], destino["y"] - hueco)
        else:
            inicio = (origen["cx"], origen["y"] - hueco)
            fin = (destino["cx"], destino["y"] + destino["alto"] + hueco)
        return [inicio, fin]

    # Diagonal: sale por arriba o por abajo, gira, y entra por un lado.
    if dy >= 0:
        inicio = (origen["cx"], origen["y"] + origen["alto"] + hueco)
    else:
        inicio = (origen["cx"], origen["y"] - hueco)
    if dx >= 0:
        fin = (destino["x"] - hueco, destino["cy"])
    else:
        fin = (destino["x"] + destino["ancho"] + hueco, destino["cy"])
    return [inicio, (inicio[0], fin[1]), fin]


def punto_medio(puntos):
    if len(puntos) == 2:
        return ((puntos[0][0] + puntos[1][0]) / 2.0, (puntos[0][1] + puntos[1][1]) / 2.0)
    return puntos[1]


def ancla_etiqueta(puntos):
    """Dónde poner el texto de una flecha, y si el tramo va en horizontal.

    En un tramo horizontal la etiqueta va encima de la línea; en uno vertical,
    a la derecha. Si no se distingue, el texto acaba tachado por su propia flecha.
    """
    if len(puntos) == 2:
        a, b = puntos
        medio = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        return medio, abs(b[1] - a[1]) < abs(b[0] - a[0])
    # Codo: se etiqueta el primer tramo, que siempre es vertical.
    a, b = puntos[0], puntos[1]
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0), False


def caja_etiqueta(texto, puntos):
    """Cómo y dónde escribir el texto de una flecha, sin pisar ninguna forma.

    En un tramo horizontal la etiqueta solo puede ocupar el hueco entre las dos
    formas: si se parte más ancha que ese hueco, las palabras acaban debajo de
    una caja y no se leen. Se parte a la medida del hueco y crece hacia arriba,
    que ahí no hay nada. En un tramo vertical va a la derecha de la línea.

    Devuelve (lineas, x, y, ancho, alineacion).
    """
    (mx, my), horizontal = ancla_etiqueta(puntos)

    if horizontal:
        hueco = abs(puntos[-1][0] - puntos[0][0]) - 2 * RELLENO_ETIQUETA
        por_linea = max(7, int(hueco / ANCHO_CARACTER_FLECHA))
    else:
        por_linea = 16

    lineas = envolver(texto, por_linea)
    ancho = max(len(l) for l in lineas) * ANCHO_CARACTER_FLECHA + 2 * RELLENO_ETIQUETA
    alto = len(lineas) * (TAM_TEXTO_FLECHA + 5)

    if horizontal:
        return lineas, mx - ancho / 2.0, my - alto - 8, ancho, "center"
    return lineas, mx + 12, my - alto / 2.0, ancho, "left"


def _segmento_cruza_caja(p1, p2, caja, holgura=4.0):
    """Comprueba si el segmento p1-p2 atraviesa el rectángulo de una caja.

    Solo se usan segmentos horizontales o verticales, así que basta con
    comparar intervalos: no hace falta geometría general.
    """
    izq = caja["x"] - holgura
    der = caja["x"] + caja["ancho"] + holgura
    arr = caja["y"] - holgura
    aba = caja["y"] + caja["alto"] + holgura

    if abs(p1[1] - p2[1]) < 0.5:                       # horizontal
        if not (arr < p1[1] < aba):
            return False
        x0, x1 = sorted((p1[0], p2[0]))
        return x0 < der and x1 > izq
    if abs(p1[0] - p2[0]) < 0.5:                       # vertical
        if not (izq < p1[0] < der):
            return False
        y0, y1 = sorted((p1[1], p2[1]))
        return y0 < aba and y1 > arr
    return False


def avisos_de_dibujo(planos):
    """Detecta flechas que pasan por encima de cajas ajenas.

    No es un error fatal: el archivo se genera igual. Pero significa que la
    colocación en la rejilla se puede mejorar (mover un nodo de columna o de
    fila casi siempre lo arregla), así que se avisa para poder corregirlo.
    """
    avisos = []
    for plano in planos:
        diagrama = plano["diagrama"]
        for flecha in diagrama["flechas"]:
            origen, destino = flecha["de"], flecha["a"]
            puntos = ruta_flecha(plano["cajas"][origen], plano["cajas"][destino])
            for nid, caja in plano["cajas"].items():
                if nid in (origen, destino):
                    continue
                for i in range(len(puntos) - 1):
                    if _segmento_cruza_caja(puntos[i], puntos[i + 1], caja):
                        avisos.append(
                            "En '%s' la flecha %s → %s pasa por encima del nodo '%s'. "
                            "Mueve alguno de los tres de columna o de fila."
                            % (diagrama["id"], origen, destino, nid))
                        break
    return avisos


# ---------------------------------------------------------------------------
# Salida: .excalidraw
# ---------------------------------------------------------------------------

def _base(elemento_id, tipo, x, y, ancho, alto, trazo, fondo, grupo=None):
    return {
        "id": elemento_id,
        "type": tipo,
        "x": round(x, 2),
        "y": round(y, 2),
        "width": round(ancho, 2),
        "height": round(alto, 2),
        "angle": 0,
        "strokeColor": trazo,
        "backgroundColor": fondo,
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [grupo] if grupo else [],
        "frameId": None,
        "roundness": None,
        "seed": _num(elemento_id + "s"),
        "version": 1,
        "versionNonce": _num(elemento_id + "n"),
        "isDeleted": False,
        "boundElements": [],
        "updated": SELLO_TIEMPO,
        "link": None,
        "locked": False,
    }


def _texto(elemento_id, x, y, ancho, lineas, color, grupo=None,
           tam=TAM_TEXTO, alineacion="center", negrita_como_titulo=False):
    contenido = "\n".join(lineas)
    alto = len(lineas) * (tam + 5)
    elemento = _base(elemento_id, "text", x, y, ancho, alto, color, "transparent", grupo)
    elemento.update({
        "text": contenido,
        "originalText": contenido,
        "fontSize": tam,
        "fontFamily": 1 if not negrita_como_titulo else 1,
        "textAlign": alineacion,
        "verticalAlign": "top",
        "containerId": None,
        "lineHeight": 1.25,
        "autoResize": False,
        "baseline": tam,
    })
    return elemento


def construir_excalidraw(espec, planos):
    elementos = []

    for plano in planos:
        diagrama = plano["diagrama"]
        pref = diagrama["id"]

        # Título del diagrama
        titulo = diagrama.get("titulo") or pref
        elementos.append(_texto(
            _ident(pref + "-titulo"), MARGEN, plano["titulo_y"],
            plano["ancho"] - MARGEN * 2, [titulo], "#1f2933",
            tam=TAM_TITULO, alineacion="left", negrita_como_titulo=True))

        # Nodos
        for nid, caja in plano["cajas"].items():
            nodo = caja["nodo"]
            color = COLORES[nodo["estado"]]
            grupo = "grupo-" + _ident(pref + nid)
            forma_id = _ident(pref + nid + "-forma")

            forma = _base(forma_id, forma_excalidraw(nodo["tipo"]),
                          caja["x"], caja["y"], caja["ancho"], caja["alto"],
                          color["trazo"], color["fondo"], grupo)
            if nodo["tipo"] == "nota":
                forma["strokeStyle"] = "dashed"
                forma["roundness"] = {"type": 3}
            elif nodo["tipo"] == "caja":
                forma["roundness"] = {"type": 3}
            elif nodo["tipo"] == "decision":
                forma["roundness"] = {"type": 2}
            caja["forma_id"] = forma_id
            elementos.append(forma)

            alto_texto = len(caja["lineas"]) * (TAM_TEXTO + 5)
            elementos.append(_texto(
                _ident(pref + nid + "-texto"),
                caja["x"] + 10, caja["cy"] - alto_texto / 2.0,
                caja["ancho"] - 20, caja["lineas"], color["trazo"], grupo))

        # Flechas
        indice = 0
        for flecha in diagrama["flechas"]:
            indice += 1
            origen, destino = plano["cajas"][flecha["de"]], plano["cajas"][flecha["a"]]
            puntos = ruta_flecha(origen, destino)
            base_x, base_y = puntos[0]
            relativos = [[round(px - base_x, 2), round(py - base_y, 2)] for px, py in puntos]
            xs = [p[0] for p in relativos]
            ys = [p[1] for p in relativos]

            color_flecha = COLORES.get(flecha.get("estado") or "neutro", COLORES["neutro"])["trazo"]
            flecha_id = _ident("%s-flecha-%s-%s-%d" % (pref, flecha["de"], flecha["a"], indice))
            elemento = _base(flecha_id, "arrow", base_x, base_y,
                             max(xs) - min(xs), max(ys) - min(ys),
                             color_flecha, "transparent")
            elemento.update({
                "points": relativos,
                "lastCommittedPoint": None,
                "startBinding": {"elementId": origen["forma_id"], "focus": 0, "gap": 6},
                "endBinding": {"elementId": destino["forma_id"], "focus": 0, "gap": 6},
                "startArrowhead": None,
                "endArrowhead": "arrow",
                "elbowed": False,
            })
            if flecha.get("estilo") == "discontinua":
                elemento["strokeStyle"] = "dashed"
            elementos.append(elemento)

            # Enlace recíproco: la caja tiene que conocer la flecha
            for extremo in (origen, destino):
                for el in elementos:
                    if el["id"] == extremo["forma_id"]:
                        el["boundElements"].append({"id": flecha_id, "type": "arrow"})
                        break

            etiqueta = str(flecha.get("texto", "")).strip()
            if etiqueta:
                lineas, ex, ey, ancho_etiqueta, alineacion = caja_etiqueta(etiqueta, puntos)
                elementos.append(_texto(
                    _ident(flecha_id + "-etiqueta"), ex, ey,
                    ancho_etiqueta, lineas, color_flecha,
                    tam=TAM_TEXTO_FLECHA, alineacion=alineacion))

        # Leyenda del diagrama
        usados = []
        for caja in plano["cajas"].values():
            if caja["nodo"]["estado"] not in usados:
                usados.append(caja["nodo"]["estado"])
        if usados:
            y_leyenda = plano["origen_y"] + max(c["y"] + c["alto"] for c in plano["cajas"].values()) \
                        - plano["origen_y"] + 46
            x_leyenda = MARGEN
            for i, estado in enumerate(usados):
                color = COLORES[estado]
                cuadro_id = _ident(pref + "-leyenda-" + estado)
                elementos.append(_base(cuadro_id, "rectangle", x_leyenda, y_leyenda, 22, 16,
                                       color["trazo"], color["fondo"]))
                elementos[-1]["roundness"] = {"type": 3}
                elementos.append(_texto(
                    _ident(cuadro_id + "-t"), x_leyenda + 28, y_leyenda - 2, 320,
                    [color["etiqueta"]], "#52606d", tam=TAM_TEXTO_FLECHA, alineacion="left"))
                x_leyenda += 40 + len(color["etiqueta"]) * 7.2

    return {
        "type": "excalidraw",
        "version": 2,
        "source": "kit-auditoria-negocio",
        "elements": elementos,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }


# ---------------------------------------------------------------------------
# Salida: .svg
# ---------------------------------------------------------------------------

def construir_svg(plano, titulo_negocio=""):
    diagrama = plano["diagrama"]
    cajas = plano["cajas"]

    minx = min(c["x"] for c in cajas.values()) - MARGEN
    maxx = max(c["x"] + c["ancho"] for c in cajas.values()) + MARGEN
    miny = plano["titulo_y"] - 20
    maxy = max(c["y"] + c["alto"] for c in cajas.values()) + ALTO_LEYENDA + 20

    partes = []
    colores_usados = []
    for caja in cajas.values():
        estado = caja["nodo"]["estado"]
        if estado not in colores_usados:
            colores_usados.append(estado)
    trazos = sorted({COLORES[e]["trazo"] for e in colores_usados} | {COLORES["neutro"]["trazo"]})

    marcadores = "".join(
        '<marker id="punta-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        'markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="%s"/></marker>'
        % (trazo.lstrip("#"), trazo) for trazo in trazos)

    partes.append('<defs>%s</defs>' % marcadores)
    partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="#ffffff"/>'
                  % (minx, miny, maxx - minx, maxy - miny))

    # Título
    titulo = diagrama.get("titulo") or diagrama["id"]
    partes.append('<text x="%.1f" y="%.1f" class="titulo">%s</text>'
                  % (minx + MARGEN, plano["titulo_y"] + 30, escapar(titulo)))

    # Flechas primero, para que las cajas queden encima
    for i, flecha in enumerate(diagrama["flechas"], start=1):
        origen, destino = cajas[flecha["de"]], cajas[flecha["a"]]
        puntos = ruta_flecha(origen, destino)
        trazo = COLORES.get(flecha.get("estado") or "neutro", COLORES["neutro"])["trazo"]
        d = " ".join("%s %.1f %.1f" % ("M" if j == 0 else "L", px, py)
                     for j, (px, py) in enumerate(puntos))
        guiones = ' stroke-dasharray="7 5"' if flecha.get("estilo") == "discontinua" else ""
        partes.append('<path d="%s" fill="none" stroke="%s" stroke-width="2"%s '
                      'marker-end="url(#punta-%s)"/>'
                      % (d, trazo, guiones, trazo.lstrip("#")))
        etiqueta = str(flecha.get("texto", "")).strip()
        if etiqueta:
            # Misma colocación que en el .excalidraw: un solo cálculo para los dos
            # formatos, así el dibujo editable y el del informe no se separan.
            lineas, caja_x, caja_y, ancho_caja, alineacion = caja_etiqueta(etiqueta, puntos)
            alto_caja = len(lineas) * (TAM_TEXTO_FLECHA + 5)
            if alineacion == "center":
                texto_x, ancla = caja_x + ancho_caja / 2.0, "middle"
            else:
                texto_x, ancla = caja_x + RELLENO_ETIQUETA, "start"
            partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="3" '
                          'fill="#ffffff" fill-opacity="0.92"/>'
                          % (caja_x, caja_y, ancho_caja, alto_caja))
            for k, linea in enumerate(lineas):
                partes.append('<text x="%.1f" y="%.1f" class="etiqueta" text-anchor="%s" '
                              'fill="%s">%s</text>'
                              % (texto_x, caja_y + 13 + k * (TAM_TEXTO_FLECHA + 5),
                                 ancla, trazo, escapar(linea)))

    # Nodos
    for caja in cajas.values():
        nodo = caja["nodo"]
        color = COLORES[nodo["estado"]]
        x, y, w, h = caja["x"], caja["y"], caja["ancho"], caja["alto"]
        if nodo["tipo"] == "decision":
            puntos = "%.1f,%.1f %.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
                x + w / 2, y, x + w, y + h / 2, x + w / 2, y + h, x, y + h / 2)
            partes.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="2"/>'
                          % (puntos, color["fondo"], color["trazo"]))
        elif nodo["tipo"] in ("inicio", "fin"):
            partes.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" fill="%s" '
                          'stroke="%s" stroke-width="2"/>'
                          % (caja["cx"], caja["cy"], w / 2, h / 2, color["fondo"], color["trazo"]))
        else:
            guiones = ' stroke-dasharray="6 4"' if nodo["tipo"] == "nota" else ""
            partes.append('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" rx="10" fill="%s" '
                          'stroke="%s" stroke-width="2"%s/>'
                          % (x, y, w, h, color["fondo"], color["trazo"], guiones))

        lineas = caja["lineas"]
        primera = caja["cy"] - (len(lineas) - 1) * ALTO_LINEA / 2.0 + 5
        for k, linea in enumerate(lineas):
            partes.append('<text x="%.1f" y="%.1f" class="nodo" fill="%s">%s</text>'
                          % (caja["cx"], primera + k * ALTO_LINEA, color["trazo"], escapar(linea)))

    # Leyenda
    y_leyenda = max(c["y"] + c["alto"] for c in cajas.values()) + 40
    x_leyenda = minx + MARGEN
    for estado in colores_usados:
        color = COLORES[estado]
        partes.append('<rect x="%.1f" y="%.1f" width="22" height="15" rx="3" fill="%s" '
                      'stroke="%s" stroke-width="1.5"/>'
                      % (x_leyenda, y_leyenda, color["fondo"], color["trazo"]))
        partes.append('<text x="%.1f" y="%.1f" class="leyenda">%s</text>'
                      % (x_leyenda + 29, y_leyenda + 12, escapar(color["etiqueta"])))
        x_leyenda += 44 + len(color["etiqueta"]) * 6.9

    estilos = (
        "text{font-family:ui-sans-serif,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif}"
        ".titulo{font-size:26px;font-weight:700;fill:#1f2933}"
        ".nodo{font-size:15px;text-anchor:middle}"
        ".etiqueta{font-size:12.5px;text-anchor:middle}"
        ".leyenda{font-size:12.5px;fill:#52606d}"
    )

    descripcion = "%s%s" % (titulo, (" — " + titulo_negocio) if titulo_negocio else "")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%.1f %.1f %.1f %.1f" '
        'preserveAspectRatio="xMidYMid meet" role="img" aria-label="%s">'
        '<title>%s</title><style>%s</style>%s</svg>'
        % (minx, miny, maxx - minx, maxy - miny, escapar(descripcion),
           escapar(descripcion), estilos, "".join(partes))
    )


# ---------------------------------------------------------------------------
# Validación del archivo generado
# ---------------------------------------------------------------------------

def validar_archivo(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        datos = json.load(f)

    problemas = []
    if datos.get("type") != "excalidraw":
        problemas.append("El campo 'type' debería ser 'excalidraw' y es %r." % datos.get("type"))
    if datos.get("version") != 2:
        problemas.append("El campo 'version' debería ser 2 y es %r." % datos.get("version"))

    elementos = datos.get("elements")
    if not isinstance(elementos, list) or not elementos:
        problemas.append("No hay elementos en el archivo.")
        elementos = []

    obligatorios = ("id", "type", "x", "y", "width", "height", "angle", "strokeColor",
                    "backgroundColor", "seed", "version", "versionNonce", "isDeleted")
    ids = {}
    for el in elementos:
        for campo in obligatorios:
            if campo not in el:
                problemas.append("Elemento %s (%s): falta el campo '%s'."
                                 % (el.get("id", "?"), el.get("type", "?"), campo))
        for campo in ("x", "y", "width", "height"):
            valor = el.get(campo)
            if isinstance(valor, (int, float)) and not math.isfinite(valor):
                problemas.append("Elemento %s: '%s' no es un número finito." % (el.get("id"), campo))
        if el.get("id") in ids:
            problemas.append("Id repetido: %s" % el.get("id"))
        ids[el.get("id")] = el
        if el.get("type") == "text" and not str(el.get("text", "")).strip():
            problemas.append("Elemento de texto %s vacío." % el.get("id"))
        if el.get("type") == "arrow":
            puntos = el.get("points")
            if not isinstance(puntos, list) or len(puntos) < 2:
                problemas.append("La flecha %s no tiene al menos 2 puntos." % el.get("id"))

    for el in elementos:
        if el.get("type") != "arrow":
            continue
        for extremo in ("startBinding", "endBinding"):
            enlace = el.get(extremo)
            if not enlace:
                continue
            destino = enlace.get("elementId")
            if destino not in ids:
                problemas.append("La flecha %s tiene %s hacia un elemento inexistente (%s)."
                                 % (el.get("id"), extremo, destino))
                continue
            recibidos = [b.get("id") for b in (ids[destino].get("boundElements") or [])]
            if el.get("id") not in recibidos:
                problemas.append("Falta el enlace recíproco: %s no aparece en boundElements de %s."
                                 % (el.get("id"), destino))

    formas = sum(1 for el in elementos if el.get("type") in ("rectangle", "diamond", "ellipse"))
    flechas = sum(1 for el in elementos if el.get("type") == "arrow")
    textos = sum(1 for el in elementos if el.get("type") == "text")

    print("Archivo: %s" % ruta)
    print("Elementos: %d (formas %d · flechas %d · textos %d)"
          % (len(elementos), formas, flechas, textos))
    if problemas:
        print("\nProblemas encontrados (%d):" % len(problemas))
        for p in problemas:
            print("  - %s" % p)
        return 1
    print("Sin problemas: el archivo se puede abrir en Excalidraw.")
    return 0


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main(argv=None):
    analizador = argparse.ArgumentParser(
        description="Genera los mapas de proceso (.excalidraw + .svg) de una auditoría de negocio.",
        epilog="Ejemplo: python3 scripts/excalidraw.py espec.json --salida workspace/informe")
    analizador.add_argument("espec", nargs="?", help="Archivo JSON con la especificación de los diagramas.")
    analizador.add_argument("--salida", help="Ruta base de salida, sin extensión.")
    analizador.add_argument("--validar", metavar="ARCHIVO",
                            help="Comprueba un .excalidraw ya generado y sale.")
    args = analizador.parse_args(argv)

    if args.validar:
        return validar_archivo(args.validar)

    if not args.espec or not args.salida:
        analizador.error("hacen falta la especificación y --salida (o bien --validar).")

    try:
        with open(args.espec, "r", encoding="utf-8") as f:
            espec = json.load(f)
    except json.JSONDecodeError as e:
        print("La especificación no es JSON válido: %s (línea %d, columna %d)"
              % (e.msg, e.lineno, e.colno), file=sys.stderr)
        return 2

    try:
        espec = validar_espec(espec)
    except ErrorEspec as e:
        print("Especificación incorrecta: %s" % e, file=sys.stderr)
        return 2

    planos = colocar(espec)

    avisos = avisos_de_dibujo(planos)
    if avisos:
        print("Avisos de colocación (%d) — el archivo se genera igual, pero se lee peor:" % len(avisos))
        for aviso in avisos:
            print("  - %s" % aviso)

    escena = construir_excalidraw(espec, planos)

    base = args.salida
    carpeta = os.path.dirname(os.path.abspath(base))
    if carpeta and not os.path.isdir(carpeta):
        os.makedirs(carpeta, exist_ok=True)

    ruta_excalidraw = base + ".excalidraw"
    with open(ruta_excalidraw, "w", encoding="utf-8") as f:
        json.dump(escena, f, ensure_ascii=False, indent=2)
    print("Escrito: %s (%d elementos)" % (ruta_excalidraw, len(escena["elements"])))

    for plano in planos:
        ruta_svg = "%s-%s.svg" % (base, plano["diagrama"]["id"])
        with open(ruta_svg, "w", encoding="utf-8") as f:
            f.write(construir_svg(plano, espec.get("titulo", "")))
        print("Escrito: %s" % ruta_svg)

    return validar_archivo(ruta_excalidraw)


if __name__ == "__main__":
    sys.exit(main())
