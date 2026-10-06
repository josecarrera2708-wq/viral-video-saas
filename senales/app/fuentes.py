"""Fuentes nuevas de wallets candidatas para el buscador (además de «antes de los listados» y «recién nacidas»).

 - kols(): traders famosos con nombre, de listas públicas (kolscan.io: top de 1, 7 y 30 días y su directorio).
 - financiadas(): compradoras grandes antes de un listado cuya wallet es NUEVA y la financió un exchange con un retiro
   de SOL (patrón de insider: alguien saca dinero de un exchange a una wallet limpia y compra antes del listado).
 - lanzamientos(): tokens que llegaron muy lejos en los últimos 60 días (pump.fun por capitalización + tendencias de
   Jupiter); sus compradores tempranos (no snipers) los saca el buscador con early_buyers.

Todas dejan las wallets en la tabla `leads` y el buscador las mide igual que las demás (buscador.score).
Las direcciones de las hot wallets de los exchanges NO están en el código (el repositorio es público): se guardan en
la base de datos (meta 'hot_wallets' = {dirección: exchange}).
"""
import json
import re
import time

from . import buscador as B
from . import db

ORIGIN = {"kol": "trader famoso", "fund": "financiada por exchange antes de un listado"}
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
