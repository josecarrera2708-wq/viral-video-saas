#!/usr/bin/env python3
"""Decide qué trozos del vídeo se quitan: silencios, muletillas y repeticiones.

Uso:  python scripts/plan_cortes.py <carpeta-del-proyecto> [opciones]

Cómo lo decide, en orden:
  1. Huecos entre palabras de la transcripción   → dónde puede haber silencio
  2. `silencedetect` de ffmpeg                   → dónde el silencio empieza y
     acaba de verdad, para no comerse el final de la palabra ni la respiración
  3. Muletillas ("eh", "em") con poca confianza
  4. Repeticiones: si dices una frase dos veces, se queda la última

Escribe trabajo/plan-cortes.json. Nada se toca del vídeo todavía: este paso
solo propone, y se puede revisar y editar a mano antes de cortar.
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

# Valores por defecto, pensados para hablar a cámara sin guion.
UMBRAL_SILENCIO = 0.55   # hueco a partir del cual se corta
PAUSA_MINIMA = 0.30      # huecos más cortos que esto no se tocan
PAUSA_OBJETIVO = 0.16    # a esto se comprimen las pausas medianas
PAD_ANTES = 0.10         # aire que se deja antes de la palabra siguiente
PAD_DESPUES = 0.12       # aire que se deja tras la palabra anterior
MINIMO_UTIL = 0.20       # un trozo más corto que esto no vale como plano
RUIDO_DB = -32           # por debajo de esto, ffmpeg lo considera silencio

# Muletillas que se quitan siempre que suenen dudosas.
MULETILLAS = {"eh", "ehm", "em", "emm", "mm", "mmm", "hm", "hmm", "ah", "uh",
              "aah", "ehh", "mhm"}
# Palabras reales que solo son muletilla si la transcripción no las tiene claras.
MULETILLAS_DUDOSAS = {"e", "a", "o", "y", "pues", "este", "esto", "bueno"}
PROB_MULETILLA = 0.40


def normaliza(texto):
    """Minúsculas, sin acentos y sin puntuación, para poder comparar palabras."""
    plano = unicodedata.normalize("NFD", texto.lower())
    plano = "".join(ch for ch in plano if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9ñ]+", "", plano.replace("ñ", "ñ"))


# ── señal 1 y 2: dónde hay silencio de verdad ──────────────────────────────


def detectar_silencios(audio, ruido=RUIDO_DB, minimo=0.22):
    """Silencios reales del audio, con ffmpeg. Devuelve [(inicio, fin)]."""
    proc = c.correr([
        c.ffmpeg(), "-nostdin", "-i", str(audio), "-af",
        "silencedetect=noise={0}dB:d={1}".format(ruido, minimo),
        "-f", "null", "-",
    ])
    return _leer_silencedetect(proc)


def _leer_silencedetect(texto):
    inicios = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", texto)]
    finales = [float(x) for x in re.findall(r"silence_end: (-?[\d.]+)", texto)]
    return [(max(a, 0.0), b) for a, b in zip(inicios, finales) if b > a]


def _silencio_dentro(hueco, silencios):
    """El silencio detectado que más ocupa el hueco entre dos palabras."""
    a, b = hueco
    mejor, solape_mejor = None, 0.0
    for s_a, s_b in silencios:
        solape = min(b, s_b) - max(a, s_a)
        if solape > solape_mejor:
            mejor, solape_mejor = (s_a, s_b), solape
    return mejor, solape_mejor


# ── señal 4: repeticiones (te has repetido, se queda la última) ─────────────


def buscar_repeticiones(palabras, ventana_maxima=6, huecos_permitidos=2,
                        separacion_maxima=6.0):
    """Encuentra tomas repetidas y devuelve [(desde_idx, hasta_idx, frase)].

    Si la frase «el primero es» aparece y vuelve a aparecer poco después, lo
    de en medio es un tropiezo: se marca para quitar desde la primera hasta
    la segunda, que es la buena.
    """
    tokens = [normaliza(p["texto"]) for p in palabras]
    fuera, i = [], 0
    while i < len(tokens):
        encontrado = None
        # Se prueba primero la frase más larga: si repetiste cinco palabras,
        # queremos quitar las cinco, no solo las dos primeras.
        for n in range(ventana_maxima, 1, -1):
            if i + n > len(tokens):
                continue
            base = tokens[i:i + n]
            if not all(base):
                continue
            for salto in range(0, huecos_permitidos + 1):
                j = i + n + salto
                if j + n > len(tokens):
                    break
                if tokens[j:j + n] != base:
                    continue
                if palabras[j]["inicio"] - palabras[i]["inicio"] > separacion_maxima:
                    continue
                encontrado = (i, j, " ".join(p["texto"] for p in palabras[i:j]))
                break
            if encontrado:
                break
        if encontrado:
            fuera.append(encontrado)
            i = encontrado[1]
        else:
            i += 1
    return fuera


# ── el plan ────────────────────────────────────────────────────────────────


def _fusionar(intervalos):
    """Une los trozos a quitar que se solapan o se tocan."""
    if not intervalos:
        return []
    orden = sorted(intervalos, key=lambda x: x["inicio"])
    salida = [dict(orden[0])]
    for actual in orden[1:]:
        ultimo = salida[-1]
        if actual["inicio"] <= ultimo["fin"] + 0.02:
            if actual["fin"] > ultimo["fin"]:
                ultimo["fin"] = actual["fin"]
            if actual["motivo"] not in ultimo["motivo"]:
                ultimo["motivo"] = "{0} + {1}".format(ultimo["motivo"], actual["motivo"])
        else:
            salida.append(dict(actual))
    return salida


def construir(palabras, total, silencios, opciones):
    """Devuelve la lista de trozos a quitar, ya ordenada y sin solapes."""
    quitar = []
    u = opciones

    if not palabras:
        # Sin voz solo se puede recortar el silencio de los extremos.
        for a, b in silencios:
            if b - a >= u["umbral"]:
                quitar.append({"inicio": a, "fin": b,
                               "motivo": "silencio {0:.2f}s".format(b - a)})
        return _fusionar(quitar)

    # Repeticiones primero: marcan las palabras que ya no cuentan para nada más.
    repetidas = set()
    if u["tomas"]:
        for desde, hasta, frase in buscar_repeticiones(palabras):
            ini = palabras[desde]["inicio"] - 0.08
            if desde > 0:
                ini = max(ini, palabras[desde - 1]["fin"] + u["pad_despues"])
            fin = max(palabras[hasta]["inicio"] - u["pad_antes"], ini + 0.05)
            quitar.append({
                "inicio": max(ini, 0.0), "fin": fin,
                "motivo": "toma repetida «{0}»".format(frase[:48]),
            })
            repetidas.update(range(desde, hasta))

    # Muletillas sueltas.
    if u["muletillas"]:
        for idx, p in enumerate(palabras):
            if idx in repetidas:
                continue
            token = normaliza(p["texto"])
            dudosa = token in MULETILLAS_DUDOSAS and p["prob"] < PROB_MULETILLA
            if token in MULETILLAS or dudosa:
                ini = p["inicio"] - 0.05
                if idx > 0:
                    ini = max(ini, palabras[idx - 1]["fin"] + u["pad_despues"] * 0.5)
                fin = p["fin"] + 0.05
                if idx + 1 < len(palabras):
                    fin = min(fin, palabras[idx + 1]["inicio"] - u["pad_antes"] * 0.5)
                if fin > ini:
                    quitar.append({"inicio": max(ini, 0.0), "fin": fin,
                                   "motivo": "muletilla «{0}»".format(p["texto"])})

    # Silencio de la cabeza y de la cola.
    primera, ultima = palabras[0], palabras[-1]
    if primera["inicio"] > u["umbral"]:
        quitar.append({
            "inicio": 0.0,
            "fin": max(primera["inicio"] - u["pad_antes"], 0.0),
            "motivo": "silencio inicial {0:.2f}s".format(primera["inicio"]),
        })
    if total - ultima["fin"] > u["umbral"]:
        quitar.append({
            "inicio": min(ultima["fin"] + u["pad_despues"], total),
            "fin": total,
            "motivo": "silencio final {0:.2f}s".format(total - ultima["fin"]),
        })

    # Huecos entre palabras.
    for anterior, siguiente in zip(palabras, palabras[1:]):
        hueco = siguiente["inicio"] - anterior["fin"]
        if hueco < u["pausa_minima"]:
            continue
        ini_bruto = anterior["fin"] + u["pad_despues"]
        fin_bruto = siguiente["inicio"] - u["pad_antes"]

        if hueco >= u["umbral"]:
            # Ajustamos al silencio real para no cortar la respiración ni la
            # cola de la palabra: el oído nota mucho más un corte a destiempo.
            sil, solape = _silencio_dentro((anterior["fin"], siguiente["inicio"]),
                                           silencios)
            if sil and solape > hueco * 0.35:
                ini_bruto = max(ini_bruto, sil[0])
                fin_bruto = min(fin_bruto, sil[1])
            if fin_bruto - ini_bruto > 0.05:
                quitar.append({
                    "inicio": ini_bruto, "fin": fin_bruto,
                    "motivo": "silencio {0:.2f}s".format(hueco),
                })
        elif u["micropausas"]:
            # Pausa mediana: no se quita entera, se acorta. Da ritmo sin que
            # parezca que hablas atropellado.
            sobra = hueco - u["pausa_objetivo"]
            if sobra > 0.08:
                centro = (anterior["fin"] + siguiente["inicio"]) / 2.0
                quitar.append({
                    "inicio": centro - sobra / 2.0, "fin": centro + sobra / 2.0,
                    "motivo": "pausa acortada {0:.2f}s".format(hueco),
                })

    return _fusionar(quitar)


def a_segmentos(quitar, total):
    """Pasa de «lo que se quita» a la lista completa de trozos con su acción."""
    segmentos, cursor = [], 0.0
    for hueco in quitar:
        ini = max(min(hueco["inicio"], total), 0.0)
        fin = max(min(hueco["fin"], total), 0.0)
        if fin <= cursor:
            continue
        ini = max(ini, cursor)
        if ini - cursor >= MINIMO_UTIL:
            segmentos.append({"inicio": round(cursor, 3), "fin": round(ini, 3),
                              "accion": "mantener"})
        elif ini > cursor and segmentos and segmentos[-1]["accion"] == "quitar":
            # Trozo demasiado corto entre dos cortes: no es un plano, es un
            # parpadeo. Se va con el corte anterior.
            segmentos[-1]["fin"] = round(ini, 3)
        elif ini > cursor:
            segmentos.append({"inicio": round(cursor, 3), "fin": round(ini, 3),
                              "accion": "mantener"})
        segmentos.append({"inicio": round(ini, 3), "fin": round(fin, 3),
                          "accion": "quitar", "motivo": hueco["motivo"]})
        cursor = fin
    if total - cursor > 0.01:
        segmentos.append({"inicio": round(cursor, 3), "fin": round(total, 3),
                          "accion": "mantener"})
    return [s for s in segmentos if s["fin"] - s["inicio"] > 0.005]


def mapa_tiempos(segmentos):
    """[(inicio_original, fin_original, desplazamiento)] de los trozos que se quedan."""
    mapa, offset = [], 0.0
    for s in segmentos:
        if s["accion"] != "mantener":
            continue
        mapa.append([s["inicio"], s["fin"], round(offset, 3)])
        offset += s["fin"] - s["inicio"]
    return mapa, round(offset, 3)


def planificar(proyecto, **kw):
    estado = c.cargar_proyecto(proyecto)
    total = float(estado["origen_info"]["duracion"])
    trans = c.leer_json(c.trabajo(estado, "transcripcion.json"),
                        {"palabras": [], "frases": []})
    palabras = trans.get("palabras") or []

    audio = c.trabajo(estado, "voz.wav")
    silencios = detectar_silencios(audio) if audio.is_file() else []

    opciones = {
        "umbral": kw.get("umbral") or UMBRAL_SILENCIO,
        "pausa_minima": kw.get("pausa_minima") or PAUSA_MINIMA,
        "pausa_objetivo": kw.get("pausa_objetivo") or PAUSA_OBJETIVO,
        "pad_antes": PAD_ANTES,
        "pad_despues": PAD_DESPUES,
        "tomas": kw.get("tomas", True),
        "muletillas": kw.get("muletillas", True),
        "micropausas": kw.get("micropausas", True),
    }

    quitar = construir(palabras, total, silencios, opciones)
    segmentos = a_segmentos(quitar, total)
    mapa, final = mapa_tiempos(segmentos)

    plan = {
        "duracion_origen": round(total, 3),
        "duracion_final": final,
        "opciones": opciones,
        "silencios_detectados": len(silencios),
        "segmentos": segmentos,
        "mapa": mapa,
    }
    salida = c.escribir_json(c.trabajo(estado, "plan-cortes.json"), plan)
    estado.setdefault("pasos", {})["plan_cortes"] = "ok"
    c.guardar_proyecto(estado)

    quitados = [s for s in segmentos if s["accion"] == "quitar"]
    print("Plan de cortes: {0} → {1} ({2} cortes, -{3:.0f}%)".format(
        c.hhmmss(total), c.hhmmss(final), len(quitados),
        100 * (1 - final / total) if total else 0))
    for s in quitados:
        print("  quitar {0} → {1}  ({2:.2f}s)  {3}".format(
            c.hhmmss(s["inicio"]), c.hhmmss(s["fin"]),
            s["fin"] - s["inicio"], s.get("motivo", "")))
    print("  → {0}".format(salida))
    print("\nSiguiente paso: aplicar los cortes y pasar a vertical")
    print("  python scripts/cortar.py \"{0}\"".format(estado["_carpeta"]))
    return plan


def main():
    ap = argparse.ArgumentParser(description="Propone los cortes del vídeo")
    ap.add_argument("proyecto")
    ap.add_argument("--umbral", type=float, default=None,
                    help="silencio mínimo que se corta (por defecto 0.55s)")
    ap.add_argument("--sin-tomas", action="store_true",
                    help="no quitar repeticiones")
    ap.add_argument("--sin-muletillas", action="store_true")
    ap.add_argument("--sin-micropausas", action="store_true",
                    help="dejar las pausas cortas tal cual")
    a = ap.parse_args()
    try:
        planificar(a.proyecto, umbral=a.umbral, tomas=not a.sin_tomas,
                   muletillas=not a.sin_muletillas,
                   micropausas=not a.sin_micropausas)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
