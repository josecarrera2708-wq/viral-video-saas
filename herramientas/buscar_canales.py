#!/usr/bin/env python3
"""Buscador de canales de referencia en YouTube (sin API de pago, solo yt-dlp).

Subcomandos:
  buscar "<consulta>" [--n 40] [--periodo any|anio|mes|semana] [--orden vistas|relevancia] [--todas]
      Busca vídeos en YouTube. Por defecto: largos (>20 min) y ordenados por vistas.
      Imprime JSON con id, título, canal, channel_id, vistas y duración.

  canal <channel_id|@handle|url> [--n 40] [--refrescar]
      Estadísticas del canal: suscriptores, mediana de vistas, % de vídeos con más vistas
      que suscriptores, outliers (>=3x mediana) de los últimos 6 meses, duración típica.
      Usa caché en investigacion/canales/cache/.

  filtrar "<consulta>" [--n 40] [--periodo anio] [--min-subs 1000] [--max-subs 80000] [--hilos 3]
      buscar + canal para cada canal único + aplica los filtros del proyecto.
      Imprime los canales que pasan y, aparte, los descartados con el motivo.

Requiere: pip install yt-dlp
"""
import argparse
import json
import os
import random
import statistics
import subprocess
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(RAIZ, "investigacion", "canales", "cache")
SEIS_MESES = 183 * 86400

# Filtro "sp" de YouTube: orden (campo 1: 3 = vistas) + filtros (campo 2: fecha y duración >20 min)
SP = {
    ("vistas", "anio"): "CAMSBAgFGAI%3D",
    ("vistas", "mes"): "CAMSBAgEGAI%3D",
    ("vistas", "semana"): "CAMSBAgDGAI%3D",
    ("vistas", "any"): "CAMSAhgC",
    ("relevancia", "anio"): "EgQIBRgC",
    ("relevancia", "mes"): "EgQIBBgC",
    ("relevancia", "semana"): "EgQIAxgC",
    ("relevancia", "any"): "EgIYAg%3D%3D",
}


def ytdlp(args, timeout=180, intentos=3):
    for i in range(intentos):
        try:
            r = subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--quiet", "--no-warnings", "--ignore-errors"] + args,
                capture_output=True, text=True, timeout=timeout,
            )
            if r.stdout.strip():
                return r.stdout
            err = r.stderr.strip()[-300:]
        except subprocess.TimeoutExpired:
            err = "timeout"
        time.sleep(3 * (i + 1) + random.random() * 3)
    raise RuntimeError(f"yt-dlp falló: {err}")


def buscar(consulta, n=40, periodo="anio", orden="vistas", todas=False):
    q = urllib.parse.quote_plus(consulta)
    url = f"https://www.youtube.com/results?search_query={q}"
    if not todas:
        url += "&sp=" + SP[(orden, periodo)]
    out = ytdlp(["--flat-playlist", "--playlist-end", str(n), "-J", url])
    d = json.loads(out)
    res = []
    for e in d.get("entries") or []:
        if not e or e.get("ie_key") not in (None, "Youtube"):
            continue
        res.append({
            "id": e.get("id"),
            "titulo": e.get("title"),
            "canal": e.get("channel") or e.get("uploader"),
            "channel_id": e.get("channel_id"),
            "vistas": e.get("view_count"),
            "duracion_min": round((e.get("duration") or 0) / 60, 1),
        })
    return res


def _url_canal(c):
    if c.startswith("http"):
        base = c.rstrip("/")
        for suf in ("/videos", "/featured", "/shorts", "/streams"):
            if base.endswith(suf):
                base = base[: -len(suf)]
        return base + "/videos"
    if c.startswith("@"):
        return f"https://www.youtube.com/{c}/videos"
    return f"https://www.youtube.com/channel/{c}/videos"


def canal(c, n=40, refrescar=False):
    os.makedirs(CACHE, exist_ok=True)
    clave = c.replace("/", "_").replace(":", "_")[-80:]
    ruta = os.path.join(CACHE, clave + ".json")
    if not refrescar and os.path.exists(ruta) and time.time() - os.path.getmtime(ruta) < 3 * 86400:
        with open(ruta) as f:
            return json.load(f)
    out = ytdlp(["--flat-playlist", "--playlist-end", str(n),
                 "--extractor-args", "youtubetab:approximate_date", "-J", _url_canal(c)])
    d = json.loads(out)
    ahora = time.time()
    vids = []
    for e in d.get("entries") or []:
        if not e:
            continue
        vids.append({
            "id": e.get("id"),
            "titulo": e.get("title"),
            "vistas": e.get("view_count") or 0,
            "duracion_min": round((e.get("duration") or 0) / 60, 1),
            "fecha": time.strftime("%Y-%m-%d", time.gmtime(e["timestamp"])) if e.get("timestamp") else None,
            "_ts": e.get("timestamp"),
        })
    subs = d.get("channel_follower_count")
    vistas = [v["vistas"] for v in vids if v["vistas"]]
    med = statistics.median(vistas) if vistas else 0
    durs = [v["duracion_min"] for v in vids if v["duracion_min"]]
    recientes = [v for v in vids if v["_ts"] and ahora - v["_ts"] <= SEIS_MESES]
    outliers = [v for v in recientes if med and v["vistas"] >= 3 * med]
    fechas = [v["_ts"] for v in vids if v["_ts"]]
    res = {
        "canal": d.get("channel") or d.get("uploader"),
        "channel_id": d.get("channel_id"),
        "handle": d.get("uploader_id"),
        "url": f"https://www.youtube.com/channel/{d.get('channel_id')}",
        "suscriptores": subs,
        "videos_analizados": len(vids),
        "mediana_vistas": int(med),
        "max_vistas": max(vistas) if vistas else 0,
        "pct_videos_vistas_mayor_que_subs": round(100 * sum(1 for x in vistas if subs and x > subs) / len(vistas)) if vistas and subs else None,
        "ratio_mediana_subs": round(med / subs, 2) if subs else None,
        "duracion_mediana_min": round(statistics.median(durs), 1) if durs else None,
        "pct_videos_25_45_min": round(100 * sum(1 for x in durs if 25 <= x <= 45) / len(durs)) if durs else None,
        "pct_videos_20_min_o_mas": round(100 * sum(1 for x in durs if x >= 20) / len(durs)) if durs else None,
        "videos_ultimos_6_meses": len(recientes),
        "vistas_ultimos_6_meses": sum(v["vistas"] for v in recientes),
        "outliers_6_meses": [{k: v[k] for k in ("titulo", "vistas", "duracion_min", "fecha", "id")} for v in sorted(outliers, key=lambda v: -v["vistas"])][:8],
        "ultimo_video": time.strftime("%Y-%m-%d", time.gmtime(max(fechas))) if fechas else None,
        "video_mas_antiguo_analizado": time.strftime("%Y-%m-%d", time.gmtime(min(fechas))) if fechas else None,
        "top_videos": [{k: v[k] for k in ("titulo", "vistas", "duracion_min", "fecha", "id")} for v in sorted(vids, key=lambda v: -v["vistas"])][:6],
        "ultimos_titulos": [v["titulo"] for v in vids[:10]],
        "descripcion": (d.get("description") or "")[:400],
    }
    tmp = ruta + f".{os.getpid()}.tmp"
    with open(tmp, "w") as f:
        json.dump(res, f, ensure_ascii=False)
    os.replace(tmp, ruta)
    return res


def motivos_descarte(s, min_subs, max_subs):
    m = []
    subs = s.get("suscriptores")
    if subs is None:
        m.append("suscriptores ocultos")
    elif not (min_subs <= subs <= max_subs):
        m.append(f"suscriptores {subs}")
    if not s.get("outliers_6_meses"):
        m.append("sin outliers en 6 meses")
    if (s.get("pct_videos_20_min_o_mas") or 0) < 40:
        m.append(f"videos cortos (mediana {s.get('duracion_mediana_min')} min)")
    if (s.get("ratio_mediana_subs") or 0) < 0.3 and (s.get("pct_videos_vistas_mayor_que_subs") or 0) < 30:
        m.append("visitas dependen de la audiencia")
    return m


def filtrar(consulta, n=40, periodo="anio", min_subs=1000, max_subs=80000, hilos=3, orden="vistas"):
    vids = buscar(consulta, n=n, periodo=periodo, orden=orden)
    canales = {}
    for v in vids:
        if v["channel_id"] and v["channel_id"] not in canales:
            canales[v["channel_id"]] = v

    def uno(cid):
        time.sleep(random.random() * 2)
        try:
            return canal(cid)
        except Exception as e:  # noqa: BLE001
            return {"channel_id": cid, "error": str(e)}

    with ThreadPoolExecutor(max_workers=hilos) as ex:
        stats = list(ex.map(uno, canales))
    pasan, descartes = [], []
    for s in stats:
        if "error" in s:
            descartes.append({"channel_id": s["channel_id"], "motivo": s["error"][:120]})
            continue
        m = motivos_descarte(s, min_subs, max_subs)
        if m:
            descartes.append({"canal": s["canal"], "subs": s["suscriptores"], "motivo": "; ".join(m)})
        else:
            s = dict(s)
            s.pop("descripcion", None)
            s["video_encontrado"] = canales[s["channel_id"]]["titulo"] if s.get("channel_id") in canales else None
            pasan.append(s)
    return {"consulta": consulta, "videos_encontrados": len(vids), "canales_unicos": len(canales),
            "pasan": pasan, "descartados": descartes}


def main():
    p = argparse.ArgumentParser()
    sp = p.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("buscar")
    b.add_argument("consulta")
    b.add_argument("--n", type=int, default=40)
    b.add_argument("--periodo", default="anio", choices=["any", "anio", "mes", "semana"])
    b.add_argument("--orden", default="vistas", choices=["vistas", "relevancia"])
    b.add_argument("--todas", action="store_true", help="sin filtro de duración/fecha")
    c = sp.add_parser("canal")
    c.add_argument("canal")
    c.add_argument("--n", type=int, default=40)
    c.add_argument("--refrescar", action="store_true")
    f = sp.add_parser("filtrar")
    f.add_argument("consulta")
    f.add_argument("--n", type=int, default=40)
    f.add_argument("--periodo", default="anio", choices=["any", "anio", "mes", "semana"])
    f.add_argument("--orden", default="vistas", choices=["vistas", "relevancia"])
    f.add_argument("--min-subs", type=int, default=1000)
    f.add_argument("--max-subs", type=int, default=80000)
    f.add_argument("--hilos", type=int, default=3)
    a = p.parse_args()
    if a.cmd == "buscar":
        r = buscar(a.consulta, a.n, a.periodo, a.orden, a.todas)
    elif a.cmd == "canal":
        r = canal(a.canal, a.n, a.refrescar)
    else:
        r = filtrar(a.consulta, a.n, a.periodo, a.min_subs, a.max_subs, a.hilos, a.orden)
    print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
