"""Buscador de wallets (se lanza cada 4 horas con systemd: python -m app.buscador).

Repite por lotes el estudio que hicimos a mano:
 1. Nuevos listados de memecoins de Solana en Gate, Bitget, KuCoin, MEXC, OKX y BingX (últimos 60 días).
 2. Quién compró cada token en las 96 h antes del listado (operaciones de Jupiter) y a qué x llegó en el listado.
 3. Wallets que repiten acierto (compraron antes y el token llegó a x2+) en 2 o más listados (primero las que más).
 4. Fuera bots (cientos de operaciones al día) y wallets inactivas.
 5. Se mide cada wallet en sus últimas compras de OTROS tokens (fuera de muestra), con velas de 1 minuto:
    cuánto habría dado copiarla (10 USDT por compra, vendiendo cuando vende, sin stop y con stop del 30 y 50%),
    la x hasta el máximo y el método del usuario (vender el 50% en cada x2).
 6. Pasan las selectivas (≤15 tokens nuevos al día) con más del 40% de acierto (x2) que dan +15% o más copiándolas,
    en al menos 15 compras. Aparecen en la app (pestaña Buscador) y llega un aviso.
Todo es reanudable: lo ya hecho se guarda en la base de datos y no se repite.
"""
import collections
import datetime
import itertools
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import cex, chain, db

UA = chain.UA
DAYS = 60                 # listados de los últimos N días (Jupiter guarda unos 3 meses de operaciones)
TOKENS_PER_RUN = int(os.environ.get("SENALES_TOKENS", 12))   # listados nuevos que se procesan en cada vuelta
WALLETS_PER_RUN = int(os.environ.get("SENALES_WALLETS", 12))  # wallets que se miden en cada vuelta
MIN_BUY_USD = 500         # compra mínima antes del listado para contar como acierto
MIN_X = 2.0               # x mínima al llegar el listado
MIN_HITS = int(os.environ.get("SENALES_MIN_HITS", 2))        # aciertos mínimos para medir la wallet
MAX_TX_DAY = 300          # más que esto = bot
SELECT_TX_DAY = 150       # más que esto = compra de todo (gana por volumen, no por elegir bien): se descarta sin medir
MAX_TOKENS_DAY = 15       # selectiva: como mucho 15 tokens nuevos al día de media
PASS = {"n": 15, "pct_x2": 40, "best": 15, "robust": 5, "won": 40}
# corte: ≥15 compras medidas, más del 40% llegan a x2, copiarla da ≥ +15% contando cada token por igual,
# sigue dando ≥ +5% sin su mejor token (que no dependa de un golpe de suerte), gana en ≥40% de los tokens
# y es selectiva (≤ MAX_TOKENS_DAY tokens nuevos al día)
# Segunda categoría: wallets que compran tokens recién nacidos a MC muy bajo
NEW_DAYS = 10             # tokens nacidos en los últimos N días...
NEW_MIN_MC = 1_000_000    # ...que ya valen al menos esto
EARLY_MC = 100_000        # «MC muy bajo»: compras hechas antes de que el token valiera esto
EARLY_X = 5               # acierto: después el token llegó a x5 desde su precio de compra
NEW_PER_RUN = int(os.environ.get("SENALES_NEW", 8))           # tokens recién nacidos que se procesan en cada vuelta
ORIGIN = {"list": "compra antes de los listados", "new": "compra recién nacidas a MC muy bajo"}
C = httpx.Client(headers=UA, timeout=30, follow_redirects=True)
CACHE = os.path.join(db.DATA, "cache")   # historiales y velas ya descargados: si la vuelta se corta, no se repiten
os.makedirs(CACHE, exist_ok=True)


def cached(name, max_age, fn):
    """Devuelve lo guardado en CACHE/name si tiene menos de max_age segundos; si no, lo calcula y lo guarda."""
    path = os.path.join(CACHE, name)
    try:
        if time.time() - os.path.getmtime(path) < max_age:
            with open(path) as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    v = fn()
    with open(path + ".tmp", "w") as f:
        json.dump(v, f)
    os.replace(path + ".tmp", path)
    return v


def log(*a):
    print(datetime.datetime.utcnow().strftime("%H:%M:%S"), *a, flush=True)


def get(url, **params):
    for i in range(5):
        try:
            r = C.get(url, params=params or None)
            if r.status_code == 429:
                time.sleep(10 * (i + 1))
                continue
            return r.json()
        except Exception:
            time.sleep(2 * (i + 1))
    return None


# ---------- 1. listados ----------
def listings():
    snap = cex.snapshot()                      # Gate, Bitget, KuCoin y MEXC por contrato
    L = collections.defaultdict(dict)          # mint -> {exchange: t}
    for m, v in snap["mints"].items():
        for ex, t in v.items():
            if t > 0:
                L[m][ex] = t
    sym2mint = snap["sym2mint"]
    start = time.time() - DAYS * 86400
    try:
        known = {r["mint"] for r in db.q("select mint from scan_tokens")}
        for sym, ca in snap["mexc"].items():   # MEXC no da la fecha de alta: se mira la primera vela diaria
            if ca in known or ca in L:
                continue
            k = get("https://api.mexc.com/api/v3/klines", symbol=sym, interval="1d", startTime=int(start * 1000), limit=1000)
            if isinstance(k, list) and k and k[0][0] / 1000 > start + 86400:
                L[ca]["mexc"] = k[0][0] / 1000
            time.sleep(0.12)
    except Exception as e:
        log("mexc", e)

    def uniq(sym):
        s = sym2mint.get(sym.upper())
        return next(iter(s)) if s and len(s) == 1 else None
    try:
        for i in (get("https://www.okx.com/api/v5/public/instruments", instType="SPOT") or {}).get("data") or []:
            if i.get("quoteCcy") == "USDT" and i.get("listTime"):
                m = uniq(i["baseCcy"])
                if m:
                    L[m]["okx"] = min(L[m].get("okx", 9e12), int(i["listTime"]) / 1000)
    except Exception as e:
        log("okx", e)
    try:
        for s in ((get("https://open-api.bingx.com/openApi/spot/v1/common/symbols") or {}).get("data") or {}).get("symbols") or []:
            base, _, qq = s.get("symbol", "").rpartition("-")
            if qq == "USDT" and s.get("timeOnline"):
                m = uniq(base)
                if m:
                    L[m]["bingx"] = min(L[m].get("bingx", 9e12), s["timeOnline"] / 1000)
    except Exception as e:
        log("bingx", e)
    inv = {m: k for k, v in sym2mint.items() for m in v}
    now = time.time()
    out = []
    for m, v in L.items():
        t = min(v.values())
        if start < t < now - 86400:
            ex = min(v, key=v.get)
            out.append((m, inv.get(m, m[:5]), ex, int(t)))
    return out


# ---------- 2. compradores antes del listado ----------
def jup_page(mint, to_ms):
    d = get(f"https://datapi.jup.ag/v1/txs/{mint}", dir="desc", toTs=to_ms)
    return (d or {}).get("txs") or []


def ts(x):
    return datetime.datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")).timestamp()


def chunk(mint, a, b):
    out, to, n = {}, int(b * 1000), 0
    while n < 300:
        tx = jup_page(mint, to)
        n += 1
        if not tx:
            break
        for x in tx:
            out[x["txHash"] + x["type"] + str(x.get("amount"))] = x
        last = min(ts(x) for x in tx)
        if last < a:
            break
        nt = int(last * 1000)
        to = nt if nt < to else to - 1000
    return [x for x in out.values() if a <= ts(x) < b]


def prelist_buyers(mint, T):
    w0, w1 = T - 96 * 3600, T - 3600
    edges = [(w0 + i * 1800, min(w1, w0 + (i + 1) * 1800)) for i in range(int((w1 - w0) // 1800) + 1) if w0 + i * 1800 < w1]
    with ThreadPoolExecutor(4) as ex:
        txs = [x for r in ex.map(lambda e: chunk(mint, *e), edges) for x in r]
    txs = [x for x in txs if not x.get("isMev") and (x.get("usdPrice") or 0) > 0]
    if not txs:
        return {}
    pend = max(txs, key=ts)["usdPrice"]          # precio justo antes del listado
    agg = collections.defaultdict(lambda: [0.0, 0.0, None])
    for x in txs:
        if x["type"] == "buy" and x["usdVolume"] >= 200:
            a = agg[x["traderAddress"]]
            a[0] += x["usdVolume"]
            a[1] += x["usdVolume"] / x["usdPrice"]
            a[2] = ts(x) if a[2] is None else min(a[2], ts(x))
    return {o: {"usd": round(u), "x": round(pend / (u / q), 2), "t": int(t0)} for o, (u, q, t0) in agg.items() if q > 0}


# ---------- 3b. compradores de tokens recién nacidos ----------
def newborn_winners():
    """Tokens de Solana nacidos hace ≤NEW_DAYS días que ya valen ≥NEW_MIN_MC (listas de tendencias de Jupiter)."""
    seen = {}
    for kind in ("toptrending", "toptraded", "toporganicscore"):
        for win in ("1h", "6h", "24h"):
            for x in get(f"https://datapi.jup.ag/v1/assets/{kind}/{win}", limit=100) or []:
                seen[x["id"]] = x
    out = []
    for m, x in seen.items():
        t0 = chain._epoch((x.get("firstPool") or {}).get("createdAt") or x.get("createdAt") or "")
        supply = float(x.get("totalSupply") or 0)
        if t0 and time.time() - t0 <= NEW_DAYS * 86400 and (x.get("mcap") or 0) >= NEW_MIN_MC \
                and (x.get("holderCount") or 0) >= 1000 and supply > 0:
            out.append((m, x.get("symbol") or m[:5], t0, supply))
    return out


def early_buyers(mint, t0, supply):
    """Quién compró al nacer el token, con MC por debajo de EARLY_MC, y a qué x llegó después desde su precio."""
    path = fine_path(mint, t0)
    if not path:
        return {}
    cross = next((k[0] for k in path if k[4] * supply >= EARLY_MC), None)
    end = min((cross + 60) if cross else t0 + 3600, t0 + 6 * 3600)
    ath = max(k[2] for k in path)
    agg = collections.defaultdict(lambda: [0.0, 0.0, None])
    for x in chunk(mint, t0 - 60, end):
        p = x.get("usdPrice") or 0
        if x.get("isMev") or x["type"] != "buy" or not p or x["usdVolume"] < 20 or p * supply >= EARLY_MC:
            continue
        a = agg[x["traderAddress"]]
        a[0] += x["usdVolume"]
        a[1] += x["usdVolume"] / p
        a[2] = ts(x) if a[2] is None else min(a[2], ts(x))
    return {o: {"usd": round(u), "x": round(ath / (u / q), 1), "mc": round(supply * u / q), "t": int(t1)}
            for o, (u, q, t1) in agg.items() if q > 0}


# ---------- 4-5. perfil e historial de una wallet ----------
def rpc(method, params):
    urls = [chain.PUBLIC_RPC]
    key = db.get("helius_key")
    if key:  # con clave de Helius se usa primero (más rápido y sin límites tan bajos)
        urls.insert(0, f"https://mainnet.helius-rpc.com/?api-key={key}")
    for url in urls:
        for i in range(4):
            try:
                j = C.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).json()
                if "result" in j:
                    return j["result"]
            except Exception:
                pass
            time.sleep(1.5 * (i + 1))
    return None


def history(addr, max_tx=500):
    prof, trades = cached(f"hist_{addr}.json", 12 * 3600, lambda: _history(addr, max_tx))
    return prof, trades


def _history(addr, max_tx):
    sigs, before = [], None
    while len(sigs) < max_tx:
        p = {"limit": 1000}
        if before:
            p["before"] = before
        s = rpc("getSignaturesForAddress", [addr, p]) or []
        sigs += s
        if len(s) < 1000:
            break
        before = s[-1]["signature"]
    ok = [x for x in sigs if not x.get("err") and x.get("blockTime")]
    if not ok:
        return None, []
    span = max(0.05, (ok[0]["blockTime"] - ok[-1]["blockTime"]) / 86400)
    prof = {"tx_day": round(len(ok) / span), "last": ok[0]["blockTime"]}
    if prof["tx_day"] > SELECT_TX_DAY or time.time() - prof["last"] > 30 * 86400:
        return prof, []
    sol_usd = (get("https://lite-api.jup.ag/price/v3", ids=chain.WSOL) or {}).get(chain.WSOL, {}).get("usdPrice") or 120
    since = time.time() - DAYS * 86400
    sel = [x["signature"] for x in ok if x["blockTime"] >= since][:max_tx]

    def fetch(sig):
        tx = rpc("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
        if tx is None:
            raise RuntimeError("sin respuesta")   # no se guarda: se reintenta en la próxima vuelta
        return chain.detect(chain.parse_tx(tx), {addr: {}}, sol_usd, infer_payer=True)

    def one(sig):
        # cada transacción leída se guarda: si la vuelta se corta a medias, no se vuelve a pedir
        try:
            return cached(f"tx_{addr[:8]}_{sig}.json", 30 * 86400, lambda: fetch(sig))
        except RuntimeError:
            return []
    with ThreadPoolExecutor(6 if db.get("helius_key") else 2) as ex:
        trades = [t for r in ex.map(one, sel) for t in r]
    return prof, trades


# ---------- 6. medición: cuánto daría copiarla ----------
COPY_USD = 10             # importe por compra en la copia sobre el papel
ENTRY_SLIP = 1.02         # el bot de copia compra unos segundos después: se paga un 2% más que ella
FEE = 0.98                # ~1% al comprar y ~1% al vender
_gt_last = [0.0]


def gt(path, **params):
    """GeckoTerminal admite unas 30 peticiones por minuto."""
    wait = 2.1 - (time.time() - _gt_last[0])
    if wait > 0:
        time.sleep(wait)
    _gt_last[0] = time.time()
    return get("https://api.geckoterminal.com/api/v2/networks/solana/" + path, **params) or {}


def fine_path(mint, t):
    """Velas desde la compra: de 1 min las primeras ~16 h, de 15 min hasta ~10 días y de 4 h después.
    Con velas más gruesas el máximo sale inflado (el pico de la vela puede ser anterior a la compra)."""
    return cached(f"path_{mint}_{int(t)}.json", 6 * 3600, lambda: _fine_path(mint, t))


def _fine_path(mint, t):
    pools = gt(f"tokens/{mint}/pools", page=1)
    pool = ((pools.get("data") or [{}])[0].get("attributes") or {}).get("address")
    if not pool:
        return []

    def ohlcv(tf, agg, before):
        d = gt(f"pools/{pool}/ohlcv/{tf}", aggregate=agg, limit=1000, token=mint, currency="usd", before_timestamp=int(before))
        return ((d.get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    now = time.time()
    out = [k for k in ohlcv("minute", 1, t + 60000) if k[0] >= t // 60 * 60]
    if t + 60000 < now:
        out += [k for k in ohlcv("minute", 15, t + 900000) if k[0] >= t + 60000]
    if t + 900000 < now:
        out += [k for k in ohlcv("hour", 4, now) if k[0] >= t + 900000]
    return sorted({k[0]: k for k in out}.values())


def ladder(xmax, xnow):
    n = 0
    while xmax >= 2 ** (n + 1):
        n += 1
    return n + 0.5 ** n * xnow


def copy_sim(path, trades, mint, t0, pnow, sl):
    """Copy trade sobre el papel: COPY_USD en cada compra suya, a su precio; en cada venta suya vendes la misma
    parte; stop de cada compra a (1 - sl) de su precio (0 = sin stop). Devuelve (valor final, invertido)."""
    hold, lots, got, inv = 0.0, [], 0.0, 0.0
    ev = [(k[0] + 60, 1, k) for k in path] + [(x["t"], 0, x) for x in trades if x["mint"] == mint and x["t"] >= t0]
    for _, is_candle, k in sorted(ev, key=lambda z: (z[0], z[1])):
        if not is_candle:
            if k["side"] == "buy":
                lots.append([k["price"] * ENTRY_SLIP, COPY_USD / (k["price"] * ENTRY_SLIP)])
                inv += COPY_USD
                hold += k["amount"]
            elif hold > 0:
                fr = min(1.0, k["amount"] / hold)
                hold -= min(hold, k["amount"])
                for lot in lots:
                    q = lot[1] * fr
                    got += q * k["price"] * FEE
                    lot[1] -= q
        elif sl:
            for lot in lots:
                if lot[1] > 0 and k[3] <= lot[0] * (1 - sl):   # k = [t, apertura, máximo, mínimo, cierre, volumen]
                    got += lot[1] * min(lot[0] * (1 - sl), k[1]) * FEE
                    lot[1] = 0
    return got + sum(lot[1] for lot in lots) * pnow * FEE, inv


def x2_sim(path, e, pnow, sl):
    """Compras como ella (pagando ENTRY_SLIP más) y vendes TODO al llegar a x2 desde tu precio; stop opcional
    a (1 - sl). Si no llega a nada, sigue en cartera al precio de hoy. Devuelve el valor por 1 invertido."""
    e *= ENTRY_SLIP
    for k in path:
        if sl and k[3] <= e * (1 - sl):     # en la misma vela que el objetivo, cuenta el stop (lo prudente)
            return min(e * (1 - sl), k[1]) / e * FEE
        if k[2] >= 2 * e:
            return 2 * FEE
    return pnow / e * FEE


# estrategias que se prueban con cada wallet (la mejor es la que se usaría para copiarla)
PLANS = {"copiar": "copiar todo", "copiar_sl30": "copiar todo + stop 30%", "copiar_sl50": "copiar todo + stop 50%",
         "x2": "todo en x2", "x2_sl30": "todo en x2 + stop 30%", "x2_sl50": "todo en x2 + stop 50%"}


def score(trades, exclude):
    """Mide las primeras compras de cada token (fuera de muestra): x hasta el máximo, tu método y, sobre todo,
    cuánto daría copiarla (COPY_USD por compra, vendiendo cuando ella vende, sin stop y con stop del 30 y 50%)."""
    first = {}
    for t in sorted(trades, key=lambda t: t["t"]):
        if t["side"] == "buy" and t["usd"] >= 100 and t["mint"] not in exclude and t["mint"] not in first:
            first[t["mint"]] = t
    buys = sorted(first.values(), key=lambda t: -t["t"])[:40]
    if not buys:
        return None
    now_p = {}
    mints = [b["mint"] for b in buys]
    for i in range(0, len(mints), 50):
        d = get("https://lite-api.jup.ag/price/v3", ids=",".join(mints[i:i + 50])) or {}
        for m in mints[i:i + 50]:
            now_p[m] = (d.get(m) or {}).get("usdPrice") or 0
    rows, per = [], collections.defaultdict(list)   # per[plan] = resultado en cada token (1 = ni gana ni pierde)
    for b in buys:
        path = fine_path(b["mint"], b["t"])
        if not path or not b["price"]:
            continue
        e = b["price"]
        xmax = max(1.0, max(k[2] for k in path) / e)
        if xmax > 500:          # dato roto (pico de un pool recién creado)
            continue
        pnow = now_p.get(b["mint"]) or path[-1][4]
        rows.append((xmax, pnow / e))
        for sl, tag in ((0, ""), (0.3, "_sl30"), (0.5, "_sl50")):
            g, i = copy_sim(path, trades, b["mint"], b["t"], pnow, sl)
            if i:
                per["copiar" + tag].append(g / i)
            per["x2" + tag].append(x2_sim([k for k in path if k[0] + 60 > b["t"]], e, pnow, sl))
    n = len(rows)
    if not n:
        return None
    # cada token cuenta igual, compre ella una vez o diez: así un solo token con muchas compras no lo decide todo
    cp = {k: round(100 * (sum(per[k]) / len(per[k]) - 1)) if per[k] else -100 for k in PLANS}
    st = {"n": n, "pct_x2": round(100 * sum(1 for a, _ in rows if a >= 2) / n),
          "avg_xmax": round(sum(a for a, _ in rows) / n, 2),
          "ladder": round(100 * (sum(ladder(a, b) * FEE for a, b in rows) / n - 1)),
          "all_x2": round(100 * (sum((2 if a >= 2 else b) * FEE for a, b in rows) / n - 1)),
          "copy": cp["copiar"], "copy_sl30": cp["copiar_sl30"], "copy_sl50": cp["copiar_sl50"],
          "x2": cp["x2"], "x2_sl30": cp["x2_sl30"], "x2_sl50": cp["x2_sl50"]}
    rob, won = {}, {}
    for k in PLANS:
        v = sorted(per[k])
        rob[k] = round(100 * (sum(v[:-1]) / (len(v) - 1) - 1)) if len(v) > 1 else -100   # sin su mejor token
        won[k] = round(100 * sum(1 for x in v if x > 1) / len(v)) if v else 0            # % de tokens en que gana
    # la mejor de las que ganan de forma regular; si ninguna lo hace, la de más media (y no pasará el corte)
    steady = [k for k in PLANS if rob[k] >= PASS["robust"] and won[k] >= PASS["won"]]
    st["plan"] = max(steady or PLANS, key=lambda k: cp[k])
    st["best"], st["robust"], st["won"] = cp[st["plan"]], rob[st["plan"]], won[st["plan"]]
    span = max(1.0, (max(t["t"] for t in trades) - min(t["t"] for t in trades)) / 86400)
    st["tokens_day"] = round(len(first) / span, 1)   # tokens nuevos al día: cuanto menos, más selectiva
    return st


# ---------- ejecución ----------
def push(title, body):
    try:
        from .server import _push_sync
        _push_sync(title, body, url="/#scan")
    except Exception as e:
        log("aviso no enviado", e)


def main():
    t0 = time.time()
    db.x("create table if not exists prelist(addr text, mint text, usd real, x real, t integer, primary key(addr, mint))")
    log("buscando listados nuevos…")
    toks = listings()
    for m, sym, ex, t in toks:
        db.x("insert or ignore into scan_tokens(mint, sym, exch, t_list, done, buyers) values(?,?,?,?,0,0)", (m, sym, ex, t))
    todo = db.q("select * from scan_tokens where done=0 order by t_list desc limit ?", (TOKENS_PER_RUN,))
    log(f"{len(toks)} listados en {DAYS} días; en esta vuelta se procesan {len(todo)}")
    for tk in todo:
        b = prelist_buyers(tk["mint"], tk["t_list"])
        db.xm("insert or replace into prelist(addr, mint, usd, x, t) values(?,?,?,?,?)",
              [(o, tk["mint"], v["usd"], v["x"], v["t"]) for o, v in b.items()])
        db.x("update scan_tokens set done=1, buyers=? where mint=?", (len(b), tk["mint"]))
        log(f"{tk['sym']} ({tk['exch']}): {len(b)} compradores antes del listado")

    db.x("create table if not exists newborn(mint text primary key, sym text, t0 integer, supply real, done integer, buyers integer)")
    db.x("create table if not exists early(addr text, mint text, usd real, x real, mc real, t integer, primary key(addr, mint))")
    log("buscando tokens recién nacidos que despegaron…")
    for m, sym, t, sup in newborn_winners():
        db.x("insert or ignore into newborn(mint, sym, t0, supply, done, buyers) values(?,?,?,?,0,0)", (m, sym, t, sup))
    for tk in db.q("select * from newborn where done=0 order by t0 desc limit ?", (NEW_PER_RUN,)):
        b = early_buyers(tk["mint"], tk["t0"], tk["supply"])
        db.xm("insert or replace into early(addr, mint, usd, x, mc, t) values(?,?,?,?,?,?)",
              [(o, tk["mint"], v["usd"], v["x"], v["mc"], v["t"]) for o, v in b.items()])
        db.x("update newborn set done=1, buyers=? where mint=?", (len(b), tk["mint"]))
        log(f"{tk['sym']} (recién nacido): {len(b)} compradores con MC < {EARLY_MC:,}")

    followed = {r["addr"] for r in db.q("select addr from wallets")}
    skip = {r["addr"] for r in db.q("select addr from candidates where status='bot' or found > ?", (int(time.time()) - 14 * 86400,))}
    hits_l = db.q("select addr, count(*) n, group_concat(mint) mints, sum(usd) u from prelist where usd>=? and x>=? "
                  "group by addr having n>=? order by n desc, u desc", (MIN_BUY_USD, MIN_X, MIN_HITS))
    hits_n = db.q("select addr, count(*) n, group_concat(mint) mints, sum(usd) u from early where x>=? "
                  "group by addr having n>=2 order by n desc, u desc", (EARLY_X,))
    pend = [[dict(h, src=src) for h in hits if h["addr"] not in followed and h["addr"] not in skip]
            for src, hits in (("list", hits_l), ("new", hits_n))]
    # primero se vuelven a medir las de mucho acierto que se midieron con una versión anterior del corte
    redo = []
    for c in db.q("select addr, origin, status from candidates where (status='no pasa' and pct_x2 > ? and detail not like '%\"v\": 3%') "
                  "or (status='no selectiva' and json_extract(detail, '$.perfil.tx_day') <= ?) "
                  "order by status, pct_x2 desc limit 6", (PASS["pct_x2"], SELECT_TX_DAY)):
        src = "new" if c["origin"] == ORIGIN["new"] else "list"
        table = "early" if src == "new" else "prelist"
        ms = [r["mint"] for r in db.q(f"select mint from {table} where addr=?", (c["addr"],))]
        redo.append({"addr": c["addr"], "n": len(ms), "mints": ",".join(ms), "src": src, "slow": c["status"] == "no selectiva"})
    fresh, seen = [], {h["addr"] for h in redo}
    for pair in itertools.zip_longest(*pend):   # una de cada categoría, por turnos
        for h in pair:
            if h and h["addr"] not in seen:
                seen.add(h["addr"])
                fresh.append(h)
    # primero las de mucho acierto medidas con un corte anterior; las «no selectiva» (lentas) van intercaladas,
    # una de cada cuatro, para que no frenen la búsqueda de wallets nuevas
    slow = [h for h in redo if h["slow"]]
    pool = [h for h in redo if not h["slow"]]
    for i, h in enumerate(fresh):
        if i % 3 == 0 and slow:
            pool.append(slow.pop(0))
        pool.append(h)
    log(f"antes de listados: {len(hits_l)} wallets con {MIN_HITS}+ aciertos · recién nacidas: {len(hits_n)} con 2+ aciertos x{EARLY_X}; "
        f"pendientes {len(pool)} ({len(redo)} se vuelven a medir); se miden hasta {WALLETS_PER_RUN} que no sean bots")
    passed = measured = checked = 0
    for h in pool:
        if measured >= WALLETS_PER_RUN or checked >= 80:
            break
        checked += 1
        prof, trades = history(h["addr"])
        tx_day = (prof or {}).get("tx_day", 0)
        if tx_day <= SELECT_TX_DAY:
            measured += 1   # los bots y las que compran de todo se descartan rápido y no gastan hueco
        sel_mints = set(h["mints"].split(","))
        st = score(trades, sel_mints) if trades else None
        ok = bool(st and st["n"] >= PASS["n"] and st["pct_x2"] > PASS["pct_x2"] and st["best"] >= PASS["best"]
                  and st["robust"] >= PASS["robust"] and st["won"] >= PASS["won"] and st["tokens_day"] <= MAX_TOKENS_DAY)
        status = "nueva" if ok else "bot" if tx_day > MAX_TX_DAY else "no selectiva" if tx_day > SELECT_TX_DAY else "no pasa"
        st = st or {"n": 0, "pct_x2": 0, "avg_xmax": 0, "ladder": 0, "all_x2": 0, "copy": 0, "copy_sl30": 0, "copy_sl50": 0,
                    "x2": 0, "x2_sl30": 0, "x2_sl50": 0, "plan": "", "best": 0, "robust": 0, "won": 0, "tokens_day": 0}
        db.x("insert or replace into candidates(addr, origin, found, score, n, pct_x2, ladder, all_x2, avg_xmax, hits, detail, status) "
             "values(?,?,?,?,?,?,?,?,?,?,?,?)",
             (h["addr"], ORIGIN[h["src"]], int(time.time()), st["best"], st["n"], st["pct_x2"],
              st["ladder"], st["all_x2"], st["avg_xmax"], h["n"],
              json.dumps({"perfil": prof, "copia": {k: st[k] for k in ("copy", "copy_sl30", "copy_sl50", "x2", "x2_sl30", "x2_sl50", "plan", "best", "robust", "won",
                                                        "tokens_day")}, "v": 3}), status))
        log(f"{h['addr'][:8]} aciertos {h['n']} -> {status} {st}")
        if ok:
            passed += 1
            push("Buscador: nueva wallet muy buena",
                 f"{PLANS[st['plan']]}: {st['best']:+d}% · {st['pct_x2']}% de sus compras llegan a x2 · {st['tokens_day']} tokens al día")
    msg = f"{len(todo)} listados nuevos, {measured} wallets medidas ({checked - measured} bots descartados), {passed} pasan el corte"
    db.put("last_scan", {"t": int(time.time()), "msg": msg, "secs": int(time.time() - t0)})
    log("FIN:", msg)


if __name__ == "__main__":
    if sys.argv[1:2] == ["listados"]:
        for m, sym, ex, t in sorted(listings(), key=lambda x: -x[3]):
            print(sym, ex, datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), m)
    else:
        main()
