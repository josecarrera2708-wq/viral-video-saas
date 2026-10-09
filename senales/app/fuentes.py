"""Fuentes nuevas de wallets candidatas para el buscador (además de «antes de los listados» y «recién nacidas»).

 - kols(): traders famosos con nombre, de listas públicas (kolscan.io: top de 1, 7 y 30 días y su directorio).
 - financiadas(): compradoras grandes antes de un listado cuya wallet es NUEVA y la financió un exchange con un retiro
   de SOL (patrón de insider: alguien saca dinero de un exchange a una wallet limpia y compra antes del listado).
 - lanzamientos(): tokens que llegaron muy lejos en los últimos 60 días (pump.fun por capitalización + tendencias de
   Jupiter); sus compradores tempranos (no snipers) los saca el buscador con early_buyers.
 - jupiter_leads(): listas «smart money» de Jupiter (smartMoney de 7 y 30 días) y los que más ganaron en los tokens que
   hicieron x5+ en 60 días (tabla `newborn`), cribadas SIN RPC con su actividad de Jupiter: fuera bots, las que compran
   de todo, lanzadoras, las que se encarecen >10% a 1 s, las inactivas y las ya medidas.

Todas dejan las wallets en la tabla `leads` y el buscador las mide igual que las demás (buscador.score).
Las direcciones de las hot wallets de los exchanges NO están en el código (el repositorio es público): se guardan en
la base de datos (meta 'hot_wallets' = {dirección: exchange}).
"""
import datetime
import json
import os
import re
import statistics
import time

from . import buscador as B
from . import db

ORIGIN = {"kol": "trader famoso", "fund": "financiada por exchange antes de un listado",
          "smart": "smart money de Jupiter", "x5": "top trader de tokens x5 (60 días)"}
KOLSCAN = "https://kolscan.io/leaderboard"
FUND_MIN_USD = 1000       # compra mínima antes del listado para mirar de dónde salió el dinero
FUND_MIN_X = 2.0          # x del precio de listado sobre su precio de compra
FUND_NEW_DAYS = 30        # «wallet nueva»: su primera transacción, como mucho 30 días antes de la compra
FUND_MIN_SOL = 5          # retiro mínimo desde el exchange
LAUNCH_DAYS = 60          # tokens nacidos en los últimos 60 días...
LAUNCH_MIN_MC = 1_000_000  # ...que valen al menos esto


def setup():
    db.x("create table if not exists leads(addr text primary key, src text, origin text, evidence text, found integer, prio real)")
    db.x("create table if not exists funding(addr text primary key, t integer, detail text)")
    # cribado de Jupiter: t = cuándo se cribó (null = pendiente), res = 'lead' o el motivo del descarte
    db.x("create table if not exists jup_crib(addr text primary key, src text, evidence text, found integer, t integer, res text, prio real)")
    db.x("create table if not exists jup_tok(mint text primary key, t integer, n integer)")   # tokens x5 ya consultados


def add_lead(addr, src, evidence, prio=0.0):
    db.x("insert or ignore into leads(addr, src, origin, evidence, found, prio) values(?,?,?,?,?,?)",
         (addr, src, ORIGIN[src], json.dumps(evidence, ensure_ascii=False), int(time.time()), prio))


# ---------- traders famosos ----------
def _page(url):
    for i in range(4):
        try:
            r = B.C.get(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"})
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        time.sleep(3 * (i + 1))
    return ""


def _next_data(url, key):
    """Lista incrustada en una página Next.js (self.__next_f.push) bajo la clave `key`."""
    parts = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)</script>', _page(url), re.S)
    txt = ""
    for p in parts:
        try:
            txt += json.loads('"' + p + '"')
        except ValueError:
            pass
    i = txt.find(f'"{key}":')
    if i < 0:
        return []
    try:
        arr, _ = json.JSONDecoder().raw_decode(txt[i + len(key) + 3:])
    except ValueError:
        return []
    return arr if isinstance(arr, list) else []


def kols():
    """Top de kolscan (beneficio en SOL de 1, 7 y 30 días) y su directorio. Primero las que más ganan en 30 días con
    pocas operaciones (las selectivas); las del directorio sin cifras, al final. Devuelve cuántas se añadieron."""
    n = 0
    best = {}
    for r in _next_data(KOLSCAN, "initLeaderboard"):
        a = r.get("wallet_address")
        if not a:
            continue
        tf = {1: "1d", 7: "7d", 30: "30d"}.get(r.get("timeframe"), str(r.get("timeframe")))
        e = best.setdefault(a, {"name": r.get("name"), "twitter": r.get("twitter")})
        e[f"sol_{tf}"] = r.get("profit")
        e[f"ops_{tf}"] = (r.get("wins") or 0) + (r.get("losses") or 0)
        e[f"ganadas_{tf}"] = r.get("wins")
    for a, e in best.items():
        profit, ops = e.get("sol_30d") or e.get("sol_7d") or 0, e.get("ops_30d") or e.get("ops_7d") or 1
        if profit and profit > 0:
            add_lead(a, "kol", e, prio=profit / max(1.0, ops / 30))   # beneficio por operación diaria
            n += 1
    for r in _next_data("https://kolscan.io/", "initialData"):
        a = r.get("wallet_address") or r.get("wallet")
        if a and a not in best:
            add_lead(a, "kol", {"name": r.get("name"), "twitter": r.get("twitter"), "directorio": True}, prio=0)
            n += 1
    return n


# ---------- financiadas por un exchange ----------
def funding(addr):
    """De dónde salió el dinero de la wallet: su primera transacción con SOL entrante y quién se lo mandó.
    Solo para wallets jóvenes (≤ 3000 firmas). Coste: 1-3 getSignaturesForAddress + ≤3 getTransaction."""
    row = db.q("select detail from funding where addr=?", (addr,), one=True)
    if row:
        return json.loads(row["detail"])
    sigs, before = [], None
    for _ in range(3):
        p = {"limit": 1000}
        if before:
            p["before"] = before
        s = B.rpc("getSignaturesForAddress", [addr, p])
        if s is None:
            return {"error": "rpc"}       # no se guarda: se reintenta en otra vuelta
        sigs += s
        if len(s) < 1000:
            break
        before = s[-1]["signature"]
    else:
        res = {"vieja": True, "firmas": len(sigs)}
        db.x("insert or replace into funding(addr, t, detail) values(?,?,?)", (addr, int(time.time()), json.dumps(res)))
        return res
    ok = [x for x in sigs if not x.get("err") and x.get("blockTime")]
    res = {"firmas": len(sigs), "primera": ok[-1]["blockTime"] if ok else None}
    hot = db.get("hot_wallets") or {}
    for x in reversed(ok[-3:]):          # sus 3 primeras transacciones, de la más antigua a la más nueva
        p = B.chain.parse_tx(B.rpc("getTransaction", [x["signature"], {"encoding": "json", "maxSupportedTransactionVersion": 1}]))
        got = (p or {}).get("sol", {}).get(addr, 0)
        if got <= 0.05:
            continue
        src = min(((k, v) for k, v in p["sol"].items() if k != addr), key=lambda kv: kv[1], default=(None, 0))
        if src[0] and src[1] < -0.05:
            res.update(de=src[0], exchange=hot.get(src[0]), sol=round(got, 2), t=p["t"])
            break
    db.x("insert or replace into funding(addr, t, detail) values(?,?,?)", (addr, int(time.time()), json.dumps(res)))
    return res


def financiadas(limit=10):
    """Compradoras de ≥ FUND_MIN_USD antes de un listado que llegó a ≥ x2 (una sola vez basta), con la wallet nueva y
    financiada por un exchange. Mira como mucho `limit` wallets por vuelta. Devuelve cuántas se añadieron."""
    if not db.get("hot_wallets"):
        return 0
    rows = db.q("select p.addr, p.mint, p.usd, p.x, p.t, s.sym, s.exch from prelist p join scan_tokens s on s.mint=p.mint "
                "where p.usd>=? and p.x>=? and p.addr not in (select addr from funding) and p.addr not in (select addr from leads) "
                "and p.addr not in (select addr from candidates) and p.addr not in (select addr from wallets) "
                "order by p.x * p.usd desc limit ?", (FUND_MIN_USD, FUND_MIN_X, limit))
    n = 0
    for r in rows:
        f = funding(r["addr"])
        if f.get("exchange") and f.get("sol", 0) >= FUND_MIN_SOL and f.get("primera") and \
                0 <= r["t"] - f["primera"] <= FUND_NEW_DAYS * 86400:
            add_lead(r["addr"], "fund", {"exchange": f["exchange"], "sol": f["sol"], "token": r["sym"], "listado": r["exch"],
                                         "compra_usd": r["usd"], "x": r["x"], "dias_antes": round((r["t"] - f["primera"]) / 86400, 1)},
                     prio=r["x"])
            n += 1
    return n


# ---------- tokens que llegaron muy lejos (60 días) ----------
def lanzamientos(pages=22):
    """Tokens de pump.fun nacidos en los últimos LAUNCH_DAYS días que valen ≥ LAUNCH_MIN_MC (la lista de pump.fun va
    ordenada por capitalización: unas 1000 monedas). Se añaden a la tabla `newborn` del buscador, que saca sus
    compradores tempranos. Devuelve cuántos tokens nuevos."""
    n, start = 0, time.time() - LAUNCH_DAYS * 86400
    for i in range(pages):
        lst = B.get("https://frontend-api-v3.pump.fun/coins", offset=i * 50, limit=50, sort="market_cap", order="DESC",
                    includeNsfw="false")
        if not isinstance(lst, list) or not lst:
            break
        for c in lst:
            t0 = (c.get("created_timestamp") or 0) / 1000
            if t0 >= start and (c.get("usd_market_cap") or c.get("market_cap") or 0) >= LAUNCH_MIN_MC and c.get("mint"):
                supply = (c.get("total_supply") or 1e15) / 1e6       # pump.fun: 6 decimales
                before = db.q("select 1 from newborn where mint=?", (c["mint"],), one=True)
                db.x("insert or ignore into newborn(mint, sym, t0, supply, done, buyers) values(?,?,?,?,0,0)",
                     (c["mint"], c.get("symbol") or c["mint"][:5], int(t0), supply))
                n += not before
        time.sleep(1.1)   # pump.fun: unas 60 peticiones por minuto
    return n


# ---------- Jupiter: smart money y top traders de tokens x5 (cribado SIN RPC) ----------
JUP = "https://datapi.jup.ag/"
JUP_GAP = 0.3             # s entre peticiones a Jupiter (en serie, ~3/s); con 429 espera 5, 10, 15... s
JUP_SMART = (("smartMoney", "7d"), ("smartMoney", "30d"))   # whale, topPnl e influencer casi no dan wallets cercanas
JUP_CRIB_MAX = int(os.environ.get("SENALES_JUP_CRIB", 150))  # wallets cribadas por llamada (el resto, en la siguiente)
JUP_MAX_SECS = 20 * 60    # tope de tiempo por llamada
JUP_TOKENS_SECS = 6 * 60  # tope de tiempo para consultar tokens x5 nuevos (top-pnl-per-asset tarda 1-6 s por token)
JUP_PAGES = 4             # páginas de actividad (~100 operaciones cada una) como mucho por wallet
JUP_TAPE_N = (8, 16)      # compras suyas cuya subida a 1 s se mira en la cinta (1 petición cada una): 8 y, si la
                          # mediana queda entre 5 y 25%, hasta 16 (con 6, una buena ya medida daba 12%; con 16, 5%)
JUP_RECRIB_DAYS = 14      # una descartada que vuelve a salir en las listas se vuelve a cribar pasado este tiempo
X5_MIN_BOUGHT, X5_MAX_BUYS, X5_MIN_PNL = 100, 25, 100   # top trader: compró ≥ 100 $, en ≤ 25 compras, y ganó ≥ +100%
LANZ_S, LANZ_MAX = 10, 25  # lanzadora: más del 25% de sus compras a ≤ 10 s de crearse el token (no copiable)
SUBE_1S_MAX = 10          # si el precio sube más de un 10% en 1 s tras su compra, copiarla no da (la siguen otros bots)
# puntuación de cribado (pizarra/datos/score.py, AUC 0,69-0,73): ln(% de cercanas del origen / 1%) + puntos por rasgos
JUP_PRIOR = {"smart": 2.1, "x5": 1.8}   # smartMoney 8,1% de cercanas, top traders x5 6,2% (prelist 5,5%: 1,7)
NON_TOKENS = B.chain.QUOTE | {"So11111111111111111111111111111111111111111"}
_jlast = [0.0]
JCALLS = [0]


def jup(path, **params):
    """GET a datapi.jup.ag, en serie (≥ JUP_GAP s entre peticiones) y con reintentos (429: 5, 10, 15... s; 5xx: 2, 4... s)."""
    for i in range(6):
        w = JUP_GAP - (time.time() - _jlast[0])
        if w > 0:
            time.sleep(w)
        _jlast[0] = time.time()
        JCALLS[0] += 1
        try:
            r = B.C.get(JUP + path, params=params or None)
            if r.status_code == 429:
                time.sleep(5 * (i + 1))
                continue
            if r.status_code >= 500:
                time.sleep(2 * (i + 1))
                continue
            return r.json() if r.status_code == 200 else None
        except Exception:
            time.sleep(2 * (i + 1))
    return None


def _ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def _rasgos(addr, ut, full):
    """Rasgos baratos de sus operaciones de Jupiter (como pizarra/datos/crib1.py): por día, primeras compras ≥ 100 $..."""
    tt = [_ts(x["blockTime"]) for x in ut]
    span = max((max(tt) - min(tt)) / 86400, 1 / 24)
    by = {}
    for x, t in zip(ut, tt):
        by.setdefault(x["assetId"], []).append((t, x["type"], x.get("usdVolume") or 0, x.get("price") or 0,
                                                 x.get("profit") or 0, x.get("cost") or 0, x.get("txHash")))
    first = {}                                   # token -> (su primera compra, si fue ≥ 100 $; todas sus operaciones)
    for m, ev in by.items():
        ev.sort()
        b = [v for v in ev if v[1] == "buy"]
        if b and b[0][2] >= 100:
            first[m] = (b[0], ev)
    holds, v2 = [], 0
    for b, ev in first.values():
        s = [v for v in ev if v[1] == "sell" and v[0] >= b[0]]
        holds.append(s[0][0] - b[0] if s else 10 ** 7)
        v2 += bool(b[3]) and any(v[3] >= 2 * b[3] for v in s)
    prof = sum(v[4] for ev in by.values() for v in ev if v[1] == "sell")
    cost = sum(v[5] for ev in by.values() for v in ev if v[1] == "sell")
    md = lambda v: round(statistics.median(v), 1) if v else None
    f = {"ops": len(ut), "paginas_llenas": full, "dias": round(span, 2), "tx_dia": round(len(ut) / span, 1),
         "tokens": len(first), "tokens_dia": round(len(first) / span, 2),
         "dias_sin_operar": round((time.time() - max(tt)) / 86400, 2),
         "compra_med_usd": md([b[2] for b, _ in first.values()]), "aguanta_med_s": md(holds),
         "vende_a_2x_pct": round(100 * v2 / len(first)) if first else None,
         "pnl_pct": round(100 * prof / cost) if cost else None}
    # sus primeras compras ≥ 100 $, de la más nueva a la más antigua: (token, t, precio de mercado, firma)
    buys = sorted(((m, b[0], b[3], b[6]) for m, (b, _) in first.items()), key=lambda z: -z[1])
    return f, buys


def _lanzamientos_pct(f, buys):
    """% de sus compras hechas a ≤ LANZ_S s de crearse el token, % de pump.fun y edad mediana del token al comprar
    (v1/assets: 50 tokens en 1 petición)."""
    ms = [m for m, *_ in buys[:50]]
    if not ms:
        return
    info = {x["id"]: x for x in (jup("v1/assets", ids=",".join(ms)) or {}).get("assets") or [] if x.get("id")}
    secs, pump = [], 0
    for m, t, *_ in buys[:50]:
        x = info.get(m) or {}
        pump += "pump" in (x.get("launchpad") or "") or m.endswith("pump")
        c = (x.get("firstPool") or {}).get("createdAt") or x.get("createdAt")
        if c:
            secs.append(t - _ts(c))
    f["pct_pump"] = round(100 * pump / len(ms))
    f["seg_lanz_med"] = round(statistics.median(secs)) if secs else None
    f["pct_lanz"] = round(100 * sum(1 for s in secs if s <= LANZ_S) / len(secs)) if secs else None


def _sube_1s(buys):
    """Mediana (%) de cuánto más caro está el token 1 s después de sus últimas compras: mediana de las 3 primeras
    operaciones de la cinta de Jupiter desde t + 1 s (como verifica.py) frente a su precio (el de mercado)."""
    jumps = []
    for m, t, price, sig in [b for b in buys if b[2] and b[1] < time.time() - 120][:JUP_TAPE_N[1]]:
        if len(jumps) >= JUP_TAPE_N[0] and not 5 <= 100 * (statistics.median(jumps) - 1) <= 25:
            break                          # con 8 ya está claro
        d = jup(f"v1/txs/{m}", dir="asc", fromTs=int((t + 1) * 1000))
        xs = sorted((_ts(x["timestamp"]), x["usdPrice"]) for x in (d or {}).get("txs") or []
                    if not x.get("isMev") and x.get("isValidPrice") is not False and (x.get("usdPrice") or 0) > 0
                    and x.get("txHash") != sig and t + 1 <= _ts(x["timestamp"]) < t + 91)[:3]
        if xs:
            jumps.append(statistics.median(p for _, p in xs) / price)
    return round(100 * (statistics.median(jumps) - 1), 1) if jumps else None


def _puntos(f):
    """Puntos de la puntuación de cribado (pizarra/datos/score.py, sin los rasgos de compra antes de listado)."""
    p, why = 0.0, []
    for ok, v, w in (((f.get("pnl_pct") or -999) >= 15, 1, "pnl>=15%"),
                     ((f.get("vende_a_2x_pct") or 0) >= 15, 1, "vende a x2>=15%"),
                     (f["tokens_dia"] <= 2, 1, "<=2 tokens/día"),
                     (f.get("pct_pump") is not None and f["pct_pump"] <= 50, 1, "<=50% pump.fun"),
                     ((f.get("aguanta_med_s") or 0) >= 3600, 1, "aguanta>=1 h"),
                     ((f.get("seg_lanz_med") or 0) >= 3600, 1, "compra tokens de >1 h"),
                     ((f.get("compra_med_usd") or 0) >= 250, 0.5, "compra>=250$"),
                     (f["tokens_dia"] * (60 if f["paginas_llenas"] else min(60, f["dias"])) < B.PASS["n"], -2, "n60<15")):
        if ok:
            p += v
            why.append(w)
    return p, why


def jup_crib(addr):
    """Criba una wallet SIN RPC: 1 página de su actividad en Jupiter (pnl-activity, ~100 operaciones; 2 si tiene pocas
    compras y hasta JUP_PAGES si la primera es una ráfaga que parece bot), 1 petición de v1/assets y 8-16 de la cinta.
    Los descartes baratos van primero. Devuelve (motivo del descarte o None, rasgos, (puntos, por qué))."""
    ut, off, full, f, buys = [], None, False, None, []
    for pg in range(JUP_PAGES):
        d = jup("v1/pnl-activity", **({"address": addr, "offset": off} if off else {"address": addr}))
        e = (d or {}).get(addr)
        if e is None:
            if not pg:
                return "sin respuesta de Jupiter", {}, 0
            break
        ut += [x for x in e.get("userTrades") or [] if x.get("assetId") not in NON_TOKENS
               and x.get("type") in ("buy", "sell") and x.get("blockTime")]
        off = e.get("next")
        full = bool(off) and bool(e.get("userTrades"))
        if not ut:
            return "sin operaciones en Jupiter", {}, 0
        f, buys = _rasgos(addr, ut, full)
        if not full:
            break
        # una página puede cubrir solo unas horas: si con ella parece bot o compra de todo, puede ser una ráfaga
        burst = f["dias"] < 3 and (f["tx_dia"] > B.SELECT_TX_DAY or f["tokens_dia"] > B.MAX_TOKENS_DAY)
        # pocas compras en la 1.ª página: una más para tener muestra de la subida a 1 s (y rasgos menos ruidosos)
        few = not pg and f["tokens"] < JUP_TAPE_N[0] and f["dias_sin_operar"] <= 7
        if not (burst or few):
            break
    if f["dias_sin_operar"] > 7:
        return "inactiva más de 7 días", f, 0
    if f["tx_dia"] > B.SELECT_TX_DAY:
        return "bot (más de 150 operaciones al día)", f, 0
    if f["tokens_dia"] > B.MAX_TOKENS_DAY:
        return "más de 15 tokens al día con compras de 100 $ o más", f, 0
    if not full and f["tokens"] < B.PASS["n"]:
        return "menos de 15 compras de 100 $ o más en todo su historial", f, 0
    if full and f["tokens_dia"] * 60 < B.PASS["n"] / 3:   # (con 15 se perdería una buena: ~14 estimadas)
        return "menos de 5 compras de 100 $ o más en 60 días (estimadas)", f, 0
    _lanzamientos_pct(f, buys)
    if (f.get("pct_lanz") or 0) > LANZ_MAX:
        return "lanzadora (más del 25% de sus compras a 10 s o menos de crear el token)", f, 0
    f["sube_1s"] = _sube_1s(buys)
    if (f["sube_1s"] or 0) > SUBE_1S_MAX:
        return "el precio sube más de un 10% a 1 s de su compra", f, 0
    p, why = _puntos(f)
    return None, f, (p, why)


def _x5_traders(stats):
    """Los que más ganaron en los tokens de `newborn` (≥ 1 M$ de capitalización nacidos en los últimos 60 días: desde
    el lanzamiento, x5 de sobra), 1 petición por token y una sola vez por token (cuando ya tiene 1 día); primero los
    más nuevos. Lo que no da tiempo a consultar (JUP_TOKENS_SECS) queda para la siguiente llamada."""
    now, out, done = time.time(), {}, 0
    toks = db.q("select mint, sym from newborn where t0 >= ? and t0 <= ? and mint not in (select mint from jup_tok) "
                "order by t0 desc", (int(now - LAUNCH_DAYS * 86400), int(now - 86400)))
    for tk in toks:
        if time.time() - now > JUP_TOKENS_SECS:
            break
        done += 1
        d = jup("v1/top-pnl-per-asset", assetId=tk["mint"])
        if d is None:
            continue                       # sin respuesta: se reintenta en la próxima llamada
        n = 0
        for a, h in (d.get("holderPnl") or {}).items():
            if (h.get("boughtValue") or 0) < X5_MIN_BOUGHT or (h.get("totalBuys") or 0) > X5_MAX_BUYS \
                    or (h.get("totalPnlPercentage") or 0) < X5_MIN_PNL:
                continue
            e = out.setdefault(a, {"mints": [], "tokens": [], "pnl_usd": 0})
            e["mints"].append(tk["mint"])
            e["tokens"].append(tk["sym"])
            e["pnl_usd"] += round(h.get("totalPnl") or 0)
            n += 1
        db.x("insert or replace into jup_tok(mint, t, n) values(?,?,?)", (tk["mint"], int(now), n))
    stats["tokens_x5"], stats["tokens_x5_pendientes"] = done, len(toks) - done
    return out


def jupiter_leads(max_wallets=JUP_CRIB_MAX, max_secs=JUP_MAX_SECS):
    """Smart money de Jupiter (smartMoney 7 y 30 días) y top traders de tokens x5 de 60 días, cribados SIN RPC; las que
    pasan van a `leads` (src 'smart' / 'x5', prio = puntuación de cribado). Lo cribado se guarda en `jup_crib` y no se
    repite; lo que no da tiempo a cribar queda pendiente para la siguiente llamada. Devuelve cuántas se añadieron."""
    t0, c0, now = time.time(), JCALLS[0], int(time.time())
    stats = {}
    known = {r["addr"] for r in db.q("select addr from candidates union select addr from wallets")}
    queued = {r["addr"] for r in db.q("select addr from leads")}
    prev = {r["addr"]: r for r in db.q("select addr, src, evidence, t, res from jup_crib")}
    found = {}
    for cat, win in JUP_SMART:
        for x in (jup("smart-money/v1/top", category=cat, window=win, limit=200) or {}).get("wallets") or []:
            a = x.get("walletId")
            if a:
                e = found.setdefault(a, {"src": "smart", "listas": [], "ultima": x.get("lastActiveAt")})
                e["listas"].append(f"{cat} {win}")
                e[f"pnl_usd_{win}"], e[f"ops_{win}"] = round(x.get("pnlUsd") or 0), x.get("txnCount")
                e[f"acierto_{win}"] = round(x.get("winRate") or 0, 2)
    stats["smart"] = len(found)
    x5 = _x5_traders(stats)
    stats["x5"] = len(x5)
    for a, e in x5.items():
        found.setdefault(a, {"src": "x5"}).update(e, tokens_x5=len(e["mints"]))
    for a, e in found.items():
        if a in known or a in queued:
            k = "ya medidas" if a in known else "ya en la cola"
            stats[k] = stats.get(k, 0) + 1
            continue
        p = prev.get(a)
        if p and p["t"] and (p["res"] == "lead" or p["t"] > now - JUP_RECRIB_DAYS * 86400):
            continue                     # ya cribada hace poco
        if p and not p["t"]:             # pendiente: se juntan los tokens x5 de la vez anterior
            old = json.loads(p["evidence"] or "{}")
            for k in ("mints", "tokens"):
                e[k] = list(dict.fromkeys((old.get(k) or []) + (e.get(k) or [])))
            if e.get("mints"):
                e["tokens_x5"] = len(e["mints"])
            if old.get("src") == "smart":
                e["src"] = "smart"
        db.x("insert into jup_crib(addr, src, evidence, found, t, res, prio) values(?,?,?,?,null,null,null) "
             "on conflict(addr) do update set src=excluded.src, evidence=excluded.evidence, t=null, res=null",
             (a, e["src"], json.dumps(e, ensure_ascii=False), now))
    # pendientes: primero smart money (más listas, más beneficio), después top traders x5 (más tokens, más beneficio)
    todo = [dict(r, ev=json.loads(r["evidence"] or "{}")) for r in db.q(
        "select addr, src, evidence from jup_crib where t is null and addr not in (select addr from candidates) "
        "and addr not in (select addr from wallets) and addr not in (select addr from leads)")]
    todo.sort(key=lambda r: (r["src"] != "smart", -len(r["ev"].get("listas") or []), -(r["ev"].get("tokens_x5") or 0),
                             -max(r["ev"].get("pnl_usd_30d") or 0, r["ev"].get("pnl_usd_7d") or 0, r["ev"].get("pnl_usd") or 0)))
    n = cribadas = 0
    motivos = {}
    for r in todo:
        if cribadas >= max_wallets or time.time() - t0 > max_secs:
            break
        a, ev = r["addr"], r["ev"]
        if ev.get("ultima") and time.time() - _ts(ev["ultima"]) > 7 * 86400:
            why, f, pts = "inactiva más de 7 días", {}, 0      # la lista ya lo dice: sin gastar peticiones
        else:
            try:
                why, f, pts = jup_crib(a)
            except Exception as ex:       # una wallet rara no para la llamada (y se reintenta en la siguiente)
                B.log("jup_crib", a[:8], type(ex).__name__, ex)
                continue
        cribadas += 1
        if why == "sin respuesta de Jupiter":
            motivos[why] = motivos.get(why, 0) + 1
            continue                      # se reintenta en la próxima llamada
        prio = None
        if why is None:
            prio = round(JUP_PRIOR[r["src"]] + pts[0], 2)
            add_lead(a, r["src"], dict(ev, criba=f, puntos=pts[1]), prio=prio)
            n += 1
        motivos[why or "pasan"] = motivos.get(why or "pasan", 0) + 1
        db.x("update jup_crib set t=?, res=?, prio=?, evidence=? where addr=?",
             (int(time.time()), why or "lead", prio, json.dumps(dict(ev, criba=f), ensure_ascii=False), a))
    stats.update(cribadas=cribadas, pendientes=len(todo) - cribadas, motivos=motivos, peticiones=JCALLS[0] - c0,
                 segundos=round(time.time() - t0), t=now)
    db.put("jup_leads", stats)
    B.log("Jupiter:", json.dumps(stats, ensure_ascii=False))
    return n
