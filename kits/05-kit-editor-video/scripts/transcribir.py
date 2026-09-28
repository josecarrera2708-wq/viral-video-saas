#!/usr/bin/env python3
"""Transcribe el audio del vídeo con marca de tiempo en cada palabra.

Dos motores, misma salida:
  · whisper local (por defecto)  → gratis, sin claves, funciona sin internet
  · AssemblyAI (opcional)        → más preciso, necesita clave y sube el audio

Uso:  python scripts/transcribir.py <carpeta-del-proyecto> [--motor whisper|assemblyai]

Escribe trabajo/transcripcion.json:
  {"motor", "idioma", "palabras": [{"inicio", "fin", "texto", "prob"}], "frases": [...]}
Los tiempos van en segundos sobre el vídeo ORIGINAL, sin cortar.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comun as c

MODELO_POR_DEFECTO = "small"

# Le damos a whisper una muestra del estilo que esperamos: así puntúa y acentúa
# mejor, y escribe bien las palabras técnicas que salen en este tipo de vídeos.
PISTA_ESTILO = (
    "Vídeo en español sobre programación, inteligencia artificial y Claude Code. "
    "Habla de terminal, prompts, tokens, repositorio, API y modelos."
)


# ── audio para la transcripción ────────────────────────────────────────────


def extraer_voz(origen, destino):
    """Saca el audio a 16 kHz mono, que es lo que quieren los dos motores."""
    destino = Path(destino)
    if destino.is_file() and destino.stat().st_size > 1024:
        return destino
    c.correr_ffmpeg([
        "-i", str(origen), "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(destino),
    ])
    return destino


# ── motor 1: whisper en tu ordenador ───────────────────────────────────────


def _cargar_whisper(modelo):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise c.FaltaDependencia(
            "Falta whisper. Instálalo con:\n"
            "  python3 -m pip install faster-whisper\n"
            "O pide a Claude que corra el doctor del kit."
        )
    hilos = max(1, min(os.cpu_count() or 4, 8))
    return WhisperModel(modelo, device="cpu", compute_type="int8", cpu_threads=hilos)


def con_whisper(audio, modelo=MODELO_POR_DEFECTO, idioma=None):
    modelo_cargado = _cargar_whisper(modelo)
    # En los silencios CTranslate2 divide entre cero y numpy avisa. Es inofensivo
    # y llenaría la pantalla de ruido, así que lo callamos.
    warnings.filterwarnings("ignore", message=".*divide by zero.*")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        segmentos, info = modelo_cargado.transcribe(
            str(audio),
            language=idioma,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
            condition_on_previous_text=False,
            initial_prompt=PISTA_ESTILO,
            beam_size=5,
        )
        palabras, frases = [], []
        for seg in segmentos:
            texto = (seg.text or "").strip()
            if texto:
                frases.append({
                    "inicio": round(seg.start, 3),
                    "fin": round(seg.end, 3),
                    "texto": texto,
                })
            for p in seg.words or []:
                limpio = (p.word or "").strip()
                if limpio:
                    palabras.append({
                        "inicio": round(p.start, 3),
                        "fin": round(p.end, 3),
                        "texto": limpio,
                        "prob": round(float(p.probability), 3),
                    })
    return {
        "motor": "whisper-local ({0})".format(modelo),
        "idioma": info.language,
        "palabras": palabras,
        "frases": frases,
    }


# ── motor 2: AssemblyAI (opcional) ─────────────────────────────────────────

API_AAI = "https://api.assemblyai.com/v2"


def _clave_aai():
    """Busca la clave en el entorno o en .env.local. Nunca se pide por chat."""
    clave = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
    if clave:
        return clave
    env = c.RAIZ / ".env.local"
    if env.is_file():
        for linea in env.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("ASSEMBLYAI_API_KEY"):
                _, _, valor = linea.partition("=")
                return valor.strip().strip("'\"")
    return ""


def _pedir(ruta, clave, datos=None, metodo=None, tipo="application/json"):
    import urllib.error
    import urllib.request

    cuerpo = json.dumps(datos).encode() if isinstance(datos, dict) else datos
    pet = urllib.request.Request(
        API_AAI + ruta, data=cuerpo, method=metodo,
        headers={"authorization": clave, "content-type": tipo},
    )
    try:
        with urllib.request.urlopen(pet, timeout=300) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")[:300]
        if e.code in (401, 403):
            raise RuntimeError(
                "AssemblyAI rechaza la clave. Revísala en .env.local "
                "(ASSEMBLYAI_API_KEY) o usa el motor local: --motor whisper."
            )
        raise RuntimeError("AssemblyAI respondió {0}: {1}".format(e.code, detalle))
    except urllib.error.URLError as e:
        raise RuntimeError(
            "No hay conexión con AssemblyAI ({0}). Con --motor whisper "
            "funciona sin internet.".format(e.reason)
        )


def con_assemblyai(audio, idioma=None):
    clave = _clave_aai()
    if not clave:
        raise c.FaltaDependencia(
            "No hay clave de AssemblyAI. Añádela a .env.local así:\n"
            "  ASSEMBLYAI_API_KEY=tu-clave\n"
            "O transcribe en local, que no necesita clave: --motor whisper."
        )
    with open(audio, "rb") as f:
        subida = _pedir("/upload", clave, datos=f.read(),
                        tipo="application/octet-stream")
    peticion = {
        "audio_url": subida["upload_url"],
        "speech_model": "universal",
        "punctuate": True,
        "format_text": True,
    }
    if idioma:
        peticion["language_code"] = idioma
    else:
        peticion["language_detection"] = True
    tarea = _pedir("/transcript", clave, datos=peticion)
    ident = tarea["id"]
    print("  · AssemblyAI procesando…")
    for _ in range(300):
        time.sleep(3)
        estado = _pedir("/transcript/" + ident, clave, metodo="GET")
        if estado["status"] == "completed":
            break
        if estado["status"] == "error":
            raise RuntimeError("AssemblyAI falló: {0}".format(estado.get("error")))
    else:
        raise RuntimeError("AssemblyAI tarda demasiado. Prueba con --motor whisper.")

    palabras = [{
        "inicio": round(p["start"] / 1000.0, 3),
        "fin": round(p["end"] / 1000.0, 3),
        "texto": p["text"].strip(),
        "prob": round(float(p.get("confidence", 1.0)), 3),
    } for p in estado.get("words") or [] if p["text"].strip()]
    frases = [{
        "inicio": round(f["start"] / 1000.0, 3),
        "fin": round(f["end"] / 1000.0, 3),
        "texto": f["text"].strip(),
    } for f in (estado.get("utterances") or [])]
    if not frases and estado.get("text"):
        frases = [{"inicio": palabras[0]["inicio"] if palabras else 0.0,
                   "fin": palabras[-1]["fin"] if palabras else 0.0,
                   "texto": estado["text"].strip()}]
    return {
        "motor": "assemblyai",
        "idioma": estado.get("language_code") or idioma or "es",
        "palabras": palabras,
        "frases": frases,
    }


# ── entrada ────────────────────────────────────────────────────────────────


def transcribir(proyecto, motor=None, modelo=None, idioma=None, refrescar=False):
    estado = c.cargar_proyecto(proyecto)
    salida = c.trabajo(estado, "transcripcion.json")
    if salida.is_file() and not refrescar:
        previo = c.leer_json(salida)
        print("Ya estaba transcrito ({0} palabras, motor {1}).".format(
            len(previo["palabras"]), previo["motor"]))
        return previo

    origen = c.ruta_origen(estado)
    audio = extraer_voz(origen, c.trabajo(estado, "voz.wav"))
    motor = motor or estado.get("motor_transcripcion") or "whisper"
    idioma = idioma or estado.get("idioma") or None

    print("Transcribiendo con {0}…".format(motor))
    inicio = time.time()
    if motor.startswith("assembly"):
        datos = con_assemblyai(audio, idioma)
    else:
        datos = con_whisper(audio, modelo or estado.get("modelo_whisper")
                            or MODELO_POR_DEFECTO, idioma)
    datos["duracion_audio"] = round(c.duracion(audio), 3)
    c.escribir_json(salida, datos)

    estado["motor_transcripcion"] = datos["motor"]
    estado["idioma"] = datos["idioma"]
    estado.setdefault("pasos", {})["transcribir"] = "ok"
    c.guardar_proyecto(estado)

    print("  ✓ {0} palabras, {1} frases, idioma {2} ({3:.0f}s de proceso)".format(
        len(datos["palabras"]), len(datos["frases"]), datos["idioma"],
        time.time() - inicio))
    print("  → {0}".format(salida))
    return datos


def main():
    ap = argparse.ArgumentParser(description="Transcribe con tiempos por palabra")
    ap.add_argument("proyecto", help="carpeta del proyecto en workspace/")
    ap.add_argument("--motor", choices=["whisper", "assemblyai"], default=None)
    ap.add_argument("--modelo", default=None, help="tiny|base|small|medium|large-v3")
    ap.add_argument("--idioma", default=None, help="es, en… (vacío = detectar)")
    ap.add_argument("--refrescar", action="store_true", help="rehacer aunque exista")
    a = ap.parse_args()
    try:
        transcribir(a.proyecto, a.motor, a.modelo, a.idioma, a.refrescar)
    except (c.FaltaDependencia, RuntimeError, FileNotFoundError) as e:
        print("\n{0}".format(e), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
