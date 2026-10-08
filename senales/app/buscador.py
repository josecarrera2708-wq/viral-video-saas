"""Buscador de wallets (se lanza cada 4 horas con systemd: python -m app.buscador).

Repite por lotes el estudio que hicimos a mano:
 1. Nuevos listados de memecoins de Solana en Gate, Bitget, KuCoin, MEXC, OKX y BingX (últimos 60 días).
 2. Quién compró cada token en las 96 h antes del listado (operaciones de Jupiter) y a qué x llegó en el listado.
 3. Wallets que repiten acierto (compraron antes y el token llegó a x2+) en 2 o más listados (primero las que más).
 4. Fuera bots (cientos de operaciones al día) y wallets inactivas.
 5. Se mide cada wallet en sus primeras compras de OTROS tokens de sus últimos 30 días (fuera de muestra: ni los
    tokens por los que se la encontró ni ningún token elegido por su éxito), como lo haría un bot de copia de verdad:
    entra ~1 s después (un 2% más caro que ella), solo cuentan las velas posteriores al minuto de su compra, el x2 tiene que ser de
    verdad (no un pico suelto), cada operación dura como mucho 72 h y se cuentan comisiones y costes fijos. Precios en dólares con el SOL de cada hora. Velas de Jupiter (todos los pools) o de
    GeckoTerminal. Se prueban 6 estrategias (copiar todo o vender todo en x2, sin stop o con stop del 30/50%).
 6. Pasan las selectivas (≤15 tokens nuevos al día) con más del 40% de acierto (x2) que dan +15% o más con su mejor
    estrategia en al menos 15 compras, que siguen ganando sin su mejor token, ganan en ≥40% de los tokens, aguantan el
    remuestreo y la mitad más reciente, y han operado en los últimos 7 días. Aparecen en la app y llega un aviso.
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
PASS = {"n": 15, "pct_x2": 40, "best": 15, "robust": 5, "won": 40, "lcb": 0, "mitad_nueva": 0, "dias": 7,
        "sin_mejor_semana": 0, "ult_21d": 0, "n_21d": 3}
# corte: ≥15 compras medidas, más del 40% llegan a x2, su mejor estrategia da ≥ +15%, sigue dando ≥ +5% sin su mejor
# token (que no dependa de un golpe de suerte), gana en ≥40% de los tokens, el límite inferior de la media por
# remuestreo no pierde (que no sea ruido), la estrategia elegida con su mitad antigua gana en la reciente, ha operado
# en los últimos 7 días y es selectiva (≤ MAX_TOKENS_DAY tokens nuevos al día)
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


SNIPE_S = 15              # compras en los primeros 15 s de vida del token: snipers (no se pueden copiar a su precio)


def launch_path(mint, t0):
    """Velas de Jupiter desde que nace el token hasta hoy: 1 min (~16 h), 15 min (~10 días) y 4 h después."""
    def q(interval, to, n):
        d = get(f"https://datapi.jup.ag/v2/charts/{mint}", interval=interval, to=int(to) * 1000, candles=n, type="price", quote="usd") or {}
        return [[k["time"], k["open"], k["high"], k["low"], k["close"], k.get("volume") or 0] for k in d.get("candles") or []]

    def build():
        now = time.time()
        out = [k for k in q("1_MINUTE", min(now, t0 + 60000), 1000) if k[0] >= t0 // 60 * 60]
        if t0 + 60000 < now:
            out += [k for k in q("15_MINUTE", min(now, t0 + 900000), 1000) if k[0] >= t0 + 60000]
        if t0 + 900000 < now:
            out += [k for k in q("4_HOUR", now, 1000) if k[0] >= t0 + 900000]
        return sorted({k[0]: k for k in out}.values())
    return cached(f"lpath_{mint}.json", 6 * 3600, build)


def early_buyers(mint, t0, supply):
    """Quién compró al nacer el token, con MC por debajo de EARLY_MC, y a qué x llegó después desde su precio.
    Fuera los snipers (primeros SNIPE_S segundos) y las wallets que Jupiter marca como sniper, bundler o dev."""
    path = launch_path(mint, t0) or fine_path(mint, t0)
    if not path:
        return {}
    cross = next((k[0] for k in path if k[4] * supply >= EARLY_MC), None)
    end = min((cross + 60) if cross else t0 + 3600, t0 + 6 * 3600)
    ath = max(k[2] for k in path)
    agg = collections.defaultdict(lambda: [0.0, 0.0, None])
    txs = chunk(mint, t0 - 60, end)
    first = min((ts(x) for x in txs), default=t0)
    for x in txs:
        p = x.get("usdPrice") or 0
        if x.get("isMev") or x["type"] != "buy" or not p or x["usdVolume"] < 20 or p * supply >= EARLY_MC \
                or ts(x) < first + SNIPE_S or {"sniper", "bundler", "dev"} & set(x.get("holderTags") or []):
            continue
        a = agg[x["traderAddress"]]
        a[0] += x["usdVolume"]
        a[1] += x["usdVolume"] / p
        a[2] = ts(x) if a[2] is None else min(a[2], ts(x))
    return {o: {"usd": round(u), "x": round(ath / (u / q), 1), "mc": round(supply * u / q), "t": int(t1)}
            for o, (u, q, t1) in agg.items() if q > 0}


# ---------- 4-5. perfil e historial de una wallet ----------
TX_RPC = "https://solana-rpc.publicnode.com"   # el más rápido, pero solo guarda unas 30 h de transacciones
ARCHIVE_RPC = "https://solana.api.pocket.network"   # público con archivo completo (inestable: pocos reintentos)
_rr = itertools.count()


def rpc(method, params):
    urls = [chain.PUBLIC_RPC]
    if method == "getTransaction":
        # primero publicnode (lo reciente); si no la tiene (null: es de hace más de ~30 h) se pide a los dos públicos con
        # archivo completo, por turnos. Antes un null de publicnode se daba por bueno y el historial salía incompleto
        urls = [TX_RPC] + [chain.PUBLIC_RPC, ARCHIVE_RPC][::1 if next(_rr) % 2 else -1]
    key = db.get("helius_key")
    if key:  # con clave de Helius se usa primero (más rápido y sin límites tan bajos)
        urls.insert(0, f"https://mainnet.helius-rpc.com/?api-key={key}")
    for url in urls:
        for i in range(2 if url in (TX_RPC, ARCHIVE_RPC) else 4):
            try:
                j = C.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).json()
                if "result" in j:
                    if j["result"] is None and method == "getTransaction" and url != urls[-1]:
                        break    # este RPC no la tiene: al siguiente
                    return j["result"]
            except Exception:
                pass
            time.sleep(1.5 * (i + 1))
    return None


MEASURE_DAYS = 60         # historial que se mide: sus últimos 60 días (por tiempo, no por número de firmas;
                          # las muy selectivas compran menos de un token al día)
MAX_SIGS = 1500           # tope de transacciones leídas por wallet (el RPC público es lento)
MAX_MISSING = 0.02        # si no se puede leer más del 2% de sus transacciones, no se mide (se reintenta en otra vuelta)
_sol_h = {}


def sol_usd_at(t):
    """Precio de SOL en la hora de `t` (velas de 1 h de MEXC; si fallan, Coinbase). Las operaciones de hace semanas
    se pasan a dólares con el SOL de entonces: con el de hoy, su precio de compra salía hasta un 20% mal."""
    h = int(t) // 3600 * 3600
    if h not in _sol_h:
        k = get("https://api.mexc.com/api/v3/klines", symbol="SOLUSDT", interval="60m",
                startTime=h * 1000, endTime=(h + 499 * 3600) * 1000, limit=500)
        for x in k if isinstance(k, list) else []:
            _sol_h[int(x[0]) // 1000] = float(x[4])
    if h not in _sol_h:
        iso = lambda v: datetime.datetime.utcfromtimestamp(v).strftime("%Y-%m-%dT%H:%M:%SZ")
        k = get("https://api.exchange.coinbase.com/products/SOL-USD/candles", granularity=3600, start=iso(h), end=iso(h + 299 * 3600))
        for x in k if isinstance(k, list) else []:   # [hora, mínimo, máximo, apertura, cierre, volumen]
            _sol_h[int(x[0])] = float(x[4])
    return _sol_h.get(h)


def reprice(trades):
    """Las transacciones que se guardaron antes de este arreglo se pasaron a dólares con el SOL del día en que se
    leyeron. Las pagadas (o cobradas) en SOL se recalculan con el SOL de su hora; las de stablecoin no cambian."""
    rs = sorted(x["usd"] / x["sol"] for x in trades if "su" not in x and x.get("side") in ("buy", "sell") and x.get("sol", 0) > 0.001)
    ref = rs[len(rs) // 2] if rs else 0          # el precio de SOL que se usó al leerlas (el de casi todas)
    out = []
    for x in trades:
        if "su" not in x and x.get("side") in ("buy", "sell") and x.get("sol", 0) > 0.001 and ref \
                and 0.85 * ref < x["usd"] / x["sol"] < 1.15 * ref:
            su = sol_usd_at(x["t"])
            if su:
                x = dict(x, usd=round(x["sol"] * su, 2), su=su)
                x["price"] = x["usd"] / x["amount"]
        out.append(x)
    return out


def history(addr, max_tx=MAX_SIGS):
    prof, trades = cached(f"hist2_{addr}.json", 12 * 3600, lambda: _history(addr, max_tx))
    if prof and prof.get("faltan"):
        # historial incompleto (transacciones que no se pudieron leer): no se guarda, se reintenta en la próxima vuelta
        os.remove(os.path.join(CACHE, f"hist2_{addr}.json"))
    return prof, reprice(trades)


def _history(addr, max_tx):
    since = time.time() - MEASURE_DAYS * 86400
    sigs, before = [], None
    while len(sigs) < max_tx:
        p = {"limit": 1000}
        if before:
            p["before"] = before
        s = rpc("getSignaturesForAddress", [addr, p]) or []
        sigs += s
        if len(s) < 1000 or (s[-1].get("blockTime") or 0) < since:
            break
        before = s[-1]["signature"]
    ok = [x for x in sigs if not x.get("err") and x.get("blockTime")]
    if not ok:
        return None, []
    span = max(0.05, (ok[0]["blockTime"] - ok[-1]["blockTime"]) / 86400)
    prof = {"tx_day": round(len(ok) / span), "last": ok[0]["blockTime"]}
    if prof["tx_day"] > SELECT_TX_DAY:
        # a las wallets famosas les llegan cientos de envíos basura al día: cuenta solo las que firma ella (muestra de 20)
        own = 0
        for x in ok[:20]:
            tx = rpc("getTransaction", [x["signature"], {"encoding": "json", "maxSupportedTransactionVersion": 1}])
            keys = ((tx or {}).get("transaction") or {}).get("message", {}).get("accountKeys") or []
            own += bool(keys) and (keys[0]["pubkey"] if isinstance(keys[0], dict) else keys[0]) == addr
        prof["propias"] = round(own / min(20, len(ok)), 2)
        prof["tx_day"] = round(prof["tx_day"] * prof["propias"])
    if prof["tx_day"] > SELECT_TX_DAY or time.time() - prof["last"] > 30 * 86400:
        return prof, []
    sel = [x["signature"] for x in ok if x["blockTime"] >= since][:max_tx]
    prof["desde"] = min((x["blockTime"] for x in ok if x["blockTime"] >= since), default=0)

    def fetch(sig):
        tx = rpc("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
        if tx is None:
            raise RuntimeError("sin respuesta")   # no se guarda: se reintenta
        p = chain.parse_tx(tx)
        su = sol_usd_at(p["t"]) if p else None
        if p and not su:
            raise RuntimeError("sin precio de SOL")
        out = chain.detect(p, {addr: {}}, su, infer_payer=True, swaps=True)
        return [dict(x, su=su) for x in out]

    def one(sig):
        # cada transacción leída se guarda: si la vuelta se corta a medias, no se vuelve a pedir
        name = f"tx_{addr[:8]}_{sig}.json"
        try:
            r = cached(name, 30 * 86400, lambda: fetch(sig))
            # guardadas antes de marcar los precios deducidos: las que no pagó en SOL se vuelven a leer (una compra
            # «suya» puede ser la que pagó otra cuenta en la misma transacción, p. ej. el dev del token)
            if any("su" not in x and x.get("side") in ("buy", "sell") and x.get("sol", 0) < 0.01 for x in r):
                r = fetch(sig)
                with open(os.path.join(CACHE, name), "w") as f:
                    json.dump(r, f)
            return r
        except RuntimeError:
            return None
    with ThreadPoolExecutor(8 if db.get("helius_key") else 6) as ex:   # 2 hilos por RPC público (3 RPC)
        res = list(ex.map(one, sel))
    for i, r in enumerate(res):   # segundo intento, de una en una, de las que fallaron
        if r is None:
            res[i] = one(sel[i])
    miss = sum(1 for r in res if r is None)
    prof["leidas"], prof["huecos"] = len(sel) - miss, miss
    if miss > MAX_MISSING * len(sel):
        prof["faltan"] = miss
    return prof, [t for r in res if r for t in r]


# ---------- 6. medición: cuánto daría copiarla (como lo haría un bot de copia de verdad) ----------
COPY_USD = 10             # importe por compra en la copia sobre el papel
ENTRY_SLIP = 1.02         # el bot (en un VPS) entra ~1 s después que ella: paga un 2% más que ella
                          # (verifica.py lo comprueba después con los precios reales de la cinta a 1 s)
EXIT_SLIP = 0.98          # y al copiar sus ventas vende ~1 s después que ella: un 2% más barato
FEE = 0.98                # ~1% al comprar y ~1% al vender
FIXED_USD = 0.25          # prioridad + propina de cada transacción (con 10 USDT pesa un ~2,5% por lado)
HORIZON = 72 * 3600       # igual que la simulación de la app: lo que no llegó a x2 en 72 h se vende a las 72 h
_gt_last = [0.0]


def gt(path, **params):
    """GeckoTerminal admite unas 30 peticiones por minuto."""
    wait = 2.1 - (time.time() - _gt_last[0])
    if wait > 0:
        time.sleep(wait)
    _gt_last[0] = time.time()
    return get("https://api.geckoterminal.com/api/v2/networks/solana/" + path, **params) or {}


def fine_path(mint, t):
    """Velas de GeckoTerminal (solo su pool principal) desde la compra: de 1 min las primeras ~16 h, de 15 min hasta
    ~10 días y de 4 h después."""
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


def jup_path(mint, t):
    """Velas de Jupiter (todos los pools, también la curva de pump.fun antes de migrar): de 1 min las primeras ~16 h
    y de 15 min hasta el final del horizonte. Solo hay velas en los minutos con operaciones."""
    done = time.time() > t + HORIZON + 3600   # pasado el horizonte las velas ya no cambian
    return cached(f"jpath_{mint}_{int(t)}.json", 30 * 86400 if done else 1800, lambda: _jup_path(mint, t))


def _jup_path(mint, t):
    def q(interval, to, n):
        d = get(f"https://datapi.jup.ag/v2/charts/{mint}", interval=interval, to=int(to) * 1000, candles=n, type="price", quote="usd") or {}
        return [[k["time"], k["open"], k["high"], k["low"], k["close"], k.get("volume") or 0] for k in d.get("candles") or []]
    m0 = int(t) // 60 * 60
    out = [k for k in q("1_MINUTE", m0 + 60000, 1000) if k[0] >= m0]
    if time.time() > m0 + 60000:
        out += [k for k in q("15_MINUTE", m0 + HORIZON + 900, 300) if k[0] >= m0 + 60000]
    return sorted({k[0]: k for k in out}.values())


def price_path(mint, t):
    """Velas para medir una compra: las de Jupiter si tienen la vela del minuto de su compra; si no, GeckoTerminal."""
    m0 = int(t) // 60 * 60
    p = jup_path(mint, t)
    if any(k[0] == m0 for k in p):
        return p
    g = fine_path(mint, t)
    return g if any(k[0] == m0 for k in g) else p


def after(path, t):
    """Velas que EMPIEZAN después del minuto de `t` (la de ese minuto pudo tener su máximo o su mínimo antes de la
    compra) y dentro del horizonte."""
    m1 = int(t) // 60 * 60 + 60
    return [k for k in path if m1 <= k[0] < t + HORIZON]


def entry_at(path, t, price):
    """Precio al que entra el copiador (el suyo + ENTRY_SLIP) y las velas posteriores al minuto de su compra.
    (None, []) si las velas no tienen el minuto de su compra: no cubren el mercado en el que compró (p. ej. otro pool)."""
    m0 = int(t) // 60 * 60
    if not any(k[0] == m0 for k in path):
        return None, []
    return price * ENTRY_SLIP, after(path, t)


X2_MIN_VOL = 500          # $ negociados en un minuto para fiarse de un pico de un solo minuto


def market_price(b):
    """Precio de MERCADO de su compra: el de su propia transacción en la cinta de Jupiter (media ponderada por volumen
    de los tramos de su txHash). Su `price` es su COSTE TOTAL (delta de SOL: comisión de red, prioridad, propina,
    renta de la cuenta del token, comisión de su terminal), de mediana un 2,6% más caro que el mercado (hasta +18%);
    el copiador ya paga aparte sus propios costes (ENTRY_SLIP, FEE, FIXED_USD): usar su coste los cuenta dos veces."""
    rows = [x for x in chunk(b["mint"], b["t"] - 2, b["t"] + 3)
            if x.get("txHash") == b.get("sig") and (x.get("usdPrice") or 0) > 0]
    if not rows:
        return b["price"]
    vol = sum(x.get("usdVolume") or 0 for x in rows)
    p = sum(x["usdPrice"] * (x.get("usdVolume") or 0) for x in rows) / vol if vol else rows[0]["usdPrice"]
    return min(b["price"], p) if p > 0.5 * b["price"] else b["price"]   # nunca más caro que su coste; dato raro -> su coste


def x2_hit(ks, e, t):
    """Primera vela en la que el x2 es de verdad: toca 2e y cierra por encima, o la siguiente vela también lo toca, o es
    una vela de 1 minuto con volumen real (un pico suelto de una operación pequeña o una mecha de 15 min no cuentan)."""
    for i, k in enumerate(ks):
        if k[2] >= 2 * e and (k[4] >= 2 * e or (i + 1 < len(ks) and ks[i + 1][2] >= 2 * e)
                              or (k[0] < t + 60000 and (k[5] or 0) >= X2_MIN_VOL)):
            return i
    return None


def exit_price(path, t, pnow):
    """Lo que vale lo no vendido: el cierre al acabar el horizonte si ya pasó; si no, el precio de hoy."""
    ks = [k for k in path if k[0] < t + HORIZON]
    if time.time() >= t + HORIZON and ks:
        return ks[-1][4]
    return pnow or (ks[-1][4] if ks else 0)


def stop_fill(k, e, sl):
    """Precio al que salta un stop en la vela k: en memecoins resbala, si la vela cerró por debajo se vende al cierre."""
    return min(e * (1 - sl), k[1], max(k[4], k[3]))


def ladder(xmax, xnow):
    n = 0
    while xmax >= 2 ** (n + 1):
        n += 1
    return n + 0.5 ** n * xnow


def copy_sim(path, trades, mint, t0, pnow, sl, entry_mult=1.0):
    """Copy trade sobre el papel: COPY_USD en cada compra suya (un ENTRY_SLIP más caro que ella) y, en cada venta suya,
    vendes la misma parte (un EXIT_SLIP más barato); stop de cada compra a (1 - sl) de tu precio; horizonte de 72 h y
    costes fijos. entry_mult: cuánto más caro que ella entra de verdad el bot (verifica.py lo saca de la cinta).
    Devuelve (valor final, invertido)."""
    hold, lots, got, inv = 0.0, [], 0.0, 0.0
    ks = [k for k in path if k[0] < t0 + HORIZON]
    # cada vela cuenta al TERMINAR (1 o 15 min según su tamaño): así sus ventas de esos minutos van antes
    dur = lambda i: (ks[i + 1][0] - ks[i][0]) if i + 1 < len(ks) and ks[i + 1][0] - ks[i][0] <= 900 else 60
    ev = [(k[0] + dur(i), 1, k) for i, k in enumerate(ks)] + \
         [(x["t"], 0, x) for x in trades if x.get("mint") == mint and t0 <= x["t"] < t0 + HORIZON]
    for _, is_candle, k in sorted(ev, key=lambda z: (z[0], z[1])):
        if not is_candle:
            if k["side"] == "buy":
                e = k["price"] * ENTRY_SLIP * entry_mult
                lots.append([e, COPY_USD / e, k["t"]])
                inv += COPY_USD
                got -= FIXED_USD
                hold += k["amount"]
            elif k["side"] == "sell" and hold > 0:
                fr = min(1.0, k["amount"] / hold)
                hold -= min(hold, k["amount"])
                for lot in lots:
                    q = lot[1] * fr
                    got += q * k["price"] * EXIT_SLIP * FEE
                    lot[1] -= q
                got -= FIXED_USD
        elif sl:
            for lot in lots:
                if lot[1] > 0 and k[0] >= lot[2] // 60 * 60 + 60 and k[3] <= lot[0] * (1 - sl):
                    got += lot[1] * stop_fill(k, lot[0], sl) * FEE - FIXED_USD
                    lot[1] = 0
    left = sum(lot[1] for lot in lots)
    return got + left * exit_price(path, t0, pnow) * FEE - (FIXED_USD if left else 0), inv


def x2_sim(ks, e, pexit, sl, t):
    """Entras a `e` (ya con deslizamiento) en `t` y vendes TODO en el primer x2 de verdad desde tu precio; stop opcional
    a (1 - sl). `ks` = velas posteriores a tu entrada dentro del horizonte. Devuelve el valor por 1 invertido."""
    c = 2 * FIXED_USD / COPY_USD
    hit = x2_hit(ks, e, t)
    for i, k in enumerate(ks):
        if sl and k[3] <= e * (1 - sl):     # en la misma vela que el objetivo, cuenta el stop (lo prudente)
            return stop_fill(k, e, sl) / e * FEE - c
        if i == hit:
            return 2 * FEE - c
    return pexit / e * FEE - c


def boot_lcb(v, q=0.10, n=2000):
    """Límite inferior (percentil q) de la media por remuestreo: con 15-40 tokens la media tiene ±15-20 puntos de ruido."""
    import random
    rnd = random.Random(len(v))   # reproducible
    m = sorted(sum(rnd.choice(v) for _ in v) / len(v) for _ in range(n))
    return m[int(q * n)]


# estrategias que se prueban con cada wallet (la mejor es la que se usaría para copiarla)
PLANS = {"copiar": "copiar todo", "copiar_sl30": "copiar todo + stop 30%", "copiar_sl50": "copiar todo + stop 50%",
         "x2": "todo en x2", "x2_sl30": "todo en x2 + stop 30%", "x2_sl50": "todo en x2 + stop 50%"}


def winners():
    """Tokens elegidos POR su éxito (listados en exchanges, recién nacidos que ya valen ≥ NEW_MIN_MC): no sirven para
    medir a ninguna wallet (serían aciertos dentro de la muestra)."""
    try:
        return {r["mint"] for r in db.q("select mint from scan_tokens union select mint from newborn")}
    except Exception:
        return set()


SWAP_BUYS = os.environ.get("SENALES_SWAP_BUYS", "0") == "1"   # medir también las compras pagadas con otro token


def swap_buys(trades, exclude):
    """Compras pagadas con otro token (el parser las deja como side="swap", sin precio) convertidas en compras con el precio
    de mercado de su propia transacción en la cinta de Jupiter. La app ya las copia así (server.value_swaps)."""
    out, seen = [], set()
    for x in sorted(trades, key=lambda t: t["t"]):
        m = x.get("mint_in") if x["side"] == "swap" else x.get("mint")
        if x["side"] != "swap" or m in exclude or m in seen:
            seen.add(m)
            continue
        seen.add(m)
        rows = [r for r in chunk(m, x["t"] - 2, x["t"] + 3) if r.get("txHash") == x["sig"] and (r.get("usdPrice") or 0) > 0]
        if not rows:
            continue
        p = rows[0]["usdPrice"]
        out.append({"sig": x["sig"], "t": x["t"], "wallet": x["wallet"], "mint": m, "side": "buy", "amount": x["amt_in"],
                    "usd": round(p * x["amt_in"], 2), "sol": 0, "price": p, "inferred": False, "pre": 0, "paid_with": x["mint_out"]})
    return out


def last_own(trades):
    """Su última operación PROPIA (compra, venta o swap que no pagó otra cuenta). La última firma de la dirección no vale:
    a las wallets les llegan repartos de comisiones, airdrops y spam firmados por otros."""
    return max((t["t"] for t in trades if t["side"] in ("buy", "sell", "swap") and not t.get("inferred")), default=0)


def score(trades, exclude):
    """Mide las primeras compras de cada token fuera de muestra como las copiaría un bot de verdad (en un VPS, ~1 s después
    que ella): entrada un 2% más cara, sin mirar velas anteriores, x2 confirmado, horizonte de 72 h y costes."""
    exclude = set(exclude) | winners()
    swapped = {x.get(k) for x in trades if x["side"] == "swap" for k in ("mint_in", "mint_out")}
    first = {}
    for t in sorted(trades + (swap_buys(trades, exclude) if SWAP_BUYS else []), key=lambda t: t["t"]):
        if t["side"] == "buy" and t["usd"] >= 100 and t["mint"] not in exclude and t["mint"] not in first:
            first[t["mint"]] = t
    # compras que pagó otra cuenta (precio deducido) o de algo que ya tenía: la app no las copiaría así -> no se miden
    skipped = sum(1 for t in first.values() if t.get("inferred") or t.get("pre", 0) > 0.01 * t["amount"])
    buys = sorted((t for t in first.values() if not t.get("inferred") and t.get("pre", 0) <= 0.01 * t["amount"]),
                  key=lambda t: -t["t"])[:40]
    if not buys:
        return None
    now_p = {}
    mints = [b["mint"] for b in buys]
    for i in range(0, len(mints), 50):
        d = get("https://lite-api.jup.ag/price/v3", ids=",".join(mints[i:i + 50])) or {}
        for m in mints[i:i + 50]:
            now_p[m] = (d.get(m) or {}).get("usdPrice") or 0
    rows, per, per_t, gi, nomed, odd, mins, used = [], collections.defaultdict(list), collections.defaultdict(list), \
        collections.defaultdict(list), 0, 0, [], []
    for b in buys:
        path = price_path(b["mint"], b["t"])
        price = market_price(b) if path and b["price"] else b["price"]
        e, ks = entry_at(path, b["t"], price) if path and b["price"] else (None, [])
        if not e or not ks:
            nomed += 1          # sin mercado medible al copiarla: no cuenta ni como acierto ni como fallo
            continue
        xmax = max(1.0, max(k[2] for k in ks) / e)
        if xmax > 500:          # dato roto (pico de un pool recién creado)
            nomed += 1
            continue
        pexit = exit_price(path, b["t"], now_p.get(b["mint"]) or path[-1][4])
        hit = x2_hit(ks, e, b["t"])
        rows.append((xmax, pexit / e, hit is not None))
        if hit is not None:
            mins.append((ks[hit][0] - b["t"]) / 60)
        used.append([b["mint"], b["t"], price])   # precio de mercado: verifica/medir.py ponen ahí el suelo de la entrada a 1 s
        m, tm = b["mint"], [t for t in trades if t["t"] >= b["t"]]
        # lo que le entra y le sale del token, también pagando o cobrando con OTRO token (side="swap": STONK, META, un
        # memecoin...): esas compras SÍ las vemos (y la app las copia, server.value_swaps), no son compras mal leídas
        got = sum(t["amount"] for t in tm if t["side"] == "buy" and t["mint"] == m) + \
            sum(t["amt_in"] for t in tm if t["side"] == "swap" and t["mint_in"] == m)
        gave = sum(t["amount"] for t in tm if t["side"] == "sell" and t["mint"] == m) + \
            sum(t["amt_out"] for t in tm if t["side"] == "swap" and t["mint_out"] == m)
        # rara: vende más de lo que le vimos entrar (compra no leída, transferencia de otra cuenta, reparto a holders)
        bad = gave > 1.05 * got
        odd += bad
        # «copiar» solo sigue sus compras/ventas en SOL o stablecoin: si cambia el token por otro, no se puede copiar
        nocopy = bad or m in swapped
        for sl, tag in ((0, ""), (0.3, "_sl30"), (0.5, "_sl50")):
            if not nocopy:
                g, i = copy_sim(path, trades, b["mint"], b["t"], pexit, sl, entry_mult=price / b["price"])
                if i:
                    per["copiar" + tag].append(g / i)
                    per_t["copiar" + tag].append((b["t"], g / i))
                    gi["copiar" + tag].append((g, i))
            v = x2_sim(ks, e, pexit, sl, b["t"])
            per["x2" + tag].append(v)
            per_t["x2" + tag].append((b["t"], v))
    n = len(rows)
    if not n:
        return None
    # «todo en x2»: cada token cuenta igual (una entrada por token). «Copiar»: por USDT invertido, como la simulación y
    # el bot (10 USDT en CADA compra suya): por token, un token en el que promedia 6 veces a la baja contaba como uno
    cp = {k: round(100 * (sum(per[k]) / len(per[k]) - 1)) if per[k] else -100 for k in PLANS}
    for k in ("copiar", "copiar_sl30", "copiar_sl50"):
        if gi[k]:
            cp[k] = round(100 * (sum(g for g, _ in gi[k]) / sum(i for _, i in gi[k]) - 1))
    st = {"n": n, "pct_x2": round(100 * sum(1 for r in rows if r[2]) / n),
          "avg_xmax": round(sum(r[0] for r in rows) / n, 2),
          "ladder": round(100 * (sum(ladder(a, b) * FEE for a, b, _ in rows) / n - 1)),
          "all_x2": round(100 * (sum((2 if h else b) * FEE for _, b, h in rows) / n - 1)),
          "copy": cp["copiar"], "copy_sl30": cp["copiar_sl30"], "copy_sl50": cp["copiar_sl50"],
          "x2": cp["x2"], "x2_sl30": cp["x2_sl30"], "x2_sl50": cp["x2_sl50"],
          "no_medibles": nomed, "raras": odd, "no_copiables": skipped,
          "min_x2": round(sorted(mins)[len(mins) // 2]) if mins else None}
    rob, rob3, won = {}, {}, {}
    for k in PLANS:
        v = sorted(per[k])
        rob[k] = round(100 * (sum(v[:-1]) / (len(v) - 1) - 1)) if len(v) > 1 else -100   # sin su mejor token
        rob3[k] = round(100 * (sum(v[:-3]) / (len(v) - 3) - 1)) if len(v) > 3 else -100  # sin sus 3 mejores
        if len(gi.get(k) or []) > 3:
            g2 = sorted(gi[k], key=lambda x: x[0] - x[1])
            rob[k] = round(100 * (sum(g for g, _ in g2[:-1]) / sum(i for _, i in g2[:-1]) - 1))
            rob3[k] = round(100 * (sum(g for g, _ in g2[:-3]) / sum(i for _, i in g2[:-3]) - 1))
        won[k] = round(100 * sum(1 for x in v if x > 1) / len(v)) if v else 0            # % de tokens en que gana
    # la mejor de las que ganan de forma regular; si ninguna lo hace, la de más media (y no pasará el corte)
    steady = [k for k in PLANS if rob[k] >= PASS["robust"] and won[k] >= PASS["won"]]
    st["plan"] = max(steady or PLANS, key=lambda k: cp[k])
    st["best"], st["robust"], st["robust3"], st["won"] = cp[st["plan"]], rob[st["plan"]], rob3[st["plan"]], won[st["plan"]]
    # la estrategia se eligió mirando estos mismos tokens: además, la media tiene que aguantar el remuestreo...
    v = per[st["plan"]]
    st["lcb"] = round(100 * (boot_lcb(v) - 1)) if len(v) >= 5 else -100
    # ...y la estrategia elegida con su mitad más antigua de tokens tiene que ganar también en la mitad más reciente
    ts = sorted(t for t, _ in per_t["x2"])
    cut = ts[len(ts) // 2] if ts else 0
    old = {k: [x for t, x in v2 if t < cut] for k, v2 in per_t.items()}
    new = {k: [x for t, x in v2 if t >= cut] for k, v2 in per_t.items()}
    k_old = max(PLANS, key=lambda k: sum(old.get(k) or [0]) / max(1, len(old.get(k) or [])))
    st["mitad_nueva"] = round(100 * (sum(new[k_old]) / len(new[k_old]) - 1)) if new.get(k_old) else -100
    # ...y que no dependa de UNA racha (la moda de un lanzador durante una semana): sin su mejor semana tiene que seguir
    # ganando, y también en las últimas 3 semanas (con al menos PASS["n_21d"] tokens: si no, ya no opera o no se puede saber)
    pt = per_t[st["plan"]]
    weeks = collections.defaultdict(list)
    for t, x in pt:
        weeks[int(t // (7 * 86400))].append(x)
    best_w = max(weeks, key=lambda w: sum(x - 1 for x in weeks[w])) if len(weeks) > 1 else None
    rest = [x for w, xs in weeks.items() if w != best_w for x in xs] if best_w is not None else []
    st["sin_mejor_semana"] = round(100 * (sum(rest) / len(rest) - 1)) if rest else -100
    rec = [x for t, x in pt if t >= time.time() - 21 * 86400]
    st["n_21d"], st["ult_21d"] = len(rec), round(100 * (sum(rec) / len(rec) - 1)) if rec else -100
    span = max(1.0, (max(t["t"] for t in trades) - min(t["t"] for t in trades)) / 86400)
    st["tokens_day"] = round(len(first) / span, 1)   # tokens nuevos al día: cuanto menos, más selectiva
    st["muestra"] = used                             # para que verifica.py mida exactamente lo mismo
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
    from . import fuentes   # fuentes nuevas: traders famosos, financiadas por exchange, lanzamientos de 60 días
    fuentes.setup()
    ORIGIN.update(fuentes.ORIGIN)
    if time.time() - (db.get("fuentes_t") or 0) > 6 * 3600:   # las listas grandes, cada 6 h
        log(f"traders famosos en la lista: {fuentes.kols()} · lanzamientos de {fuentes.LAUNCH_DAYS} días: "
            f"{fuentes.lanzamientos()} tokens nuevos")
        db.put("fuentes_t", int(time.time()))
    if time.time() - (db.get("fuentes_jup_t") or 0) > 6 * 3600:   # smart money y top traders x5 de Jupiter, cada 6 h
        try:
            log(f"Jupiter (smart money y top traders x5, cribadas sin RPC): {fuentes.jupiter_leads()} nuevas")
        except Exception as e:   # un fallo de Jupiter no para la vuelta
            log("jupiter_leads", type(e).__name__, e)
        db.put("fuentes_jup_t", int(time.time()))
    log(f"financiadas por un exchange antes de un listado: {fuentes.financiadas()} nuevas")
    log("buscando tokens recién nacidos que despegaron…")
    for m, sym, t, sup in newborn_winners():
        db.x("insert or ignore into newborn(mint, sym, t0, supply, done, buyers) values(?,?,?,?,0,0)", (m, sym, t, sup))
    # la mitad, los más nuevos; la otra mitad, los más antiguos pendientes (lanzamientos de hace semanas)
    for tk in db.q("select * from newborn where done=0 order by t0 desc limit ?", (NEW_PER_RUN // 2,)) + \
            db.q("select * from newborn where done=0 order by t0 limit ?", (NEW_PER_RUN - NEW_PER_RUN // 2,)):
        if db.q("select done from newborn where mint=?", (tk["mint"],), one=True)["done"]:
            continue
        b = early_buyers(tk["mint"], tk["t0"], tk["supply"])
        db.xm("insert or replace into early(addr, mint, usd, x, mc, t) values(?,?,?,?,?,?)",
              [(o, tk["mint"], v["usd"], v["x"], v["mc"], v["t"]) for o, v in b.items()])
        db.x("update newborn set done=1, buyers=? where mint=?", (len(b), tk["mint"]))
        log(f"{tk['sym']} (recién nacido): {len(b)} compradores con MC < {EARLY_MC:,}")

    followed = {r["addr"] for r in db.q("select addr from wallets")}
    skip = {r["addr"] for r in db.q("select addr from candidates where status='bot' or (found > ? and "
                                    "json_extract(detail, '$.perfil.faltan') is null)", (int(time.time()) - 14 * 86400,))}
    hits_l = db.q("select addr, count(*) n, group_concat(mint) mints, sum(usd) u from prelist where usd>=? and x>=? "
                  "group by addr having n>=? order by n desc, u desc", (MIN_BUY_USD, MIN_X, MIN_HITS))
    hits_n = db.q("select addr, count(*) n, group_concat(mint) mints, sum(usd) u from early where x>=? "
                  "group by addr having n>=2 order by n desc, u desc", (EARLY_X,))
    leads = db.q("select addr, src, evidence from leads where addr not in (select addr from candidates where "
                 "json_extract(detail, '$.perfil.faltan') is null) order by prio desc")   # las de historial incompleto se reintentan
    hits_k = [{"addr": r["addr"], "n": 0, "mints": "", "u": 0} for r in leads if r["src"] == "kol"]
    hits_f = [{"addr": r["addr"], "n": 1, "mints": "", "u": 0} for r in leads if r["src"] == "fund"]
    hits_s = [{"addr": r["addr"], "n": 0, "mints": "", "u": 0} for r in leads if r["src"] == "smart"]
    ev_x = [(r["addr"], json.loads(r["evidence"] or "{}")) for r in leads if r["src"] == "x5"]
    hits_x = [{"addr": a, "n": e.get("tokens_x5") or 0, "mints": ",".join(e.get("mints") or []), "u": 0} for a, e in ev_x]
    # por grupos, de más a menos wallets cercanas al corte por cada una mirada (pizarra/datos: smartMoney 8,1%, top traders
    # x5 6,2%, antes de listados 5,5%; recién nacidas ~1%; traders famosos pasan a 0 s pero caen a 1 s): dentro de cada
    # grupo, una de cada categoría por turnos; un grupo no empieza hasta que se acaba el anterior
    tiers = [(("smart", hits_s), ("x5", hits_x), ("list", hits_l), ("fund", hits_f)), (("new", hits_n),), (("kol", hits_k),)]
    tiers = [[[dict(h, src=src) for h in hits if h["addr"] not in followed and h["addr"] not in skip] for src, hits in tier]
             for tier in tiers]
    # primero se vuelven a medir las de mucho acierto que se midieron con una versión anterior del corte
    redo = []
    for c in db.q("select addr, origin, status from candidates where (status='no pasa' and pct_x2 > ? and detail not like '%\"v\": 5%') "
                  "or (status='no selectiva' and json_extract(detail, '$.perfil.tx_day') <= ?) "
                  "order by status, pct_x2 desc limit 6", (PASS["pct_x2"], SELECT_TX_DAY)):
        src = {v: k for k, v in ORIGIN.items()}.get(c["origin"], "list")
        table = "early" if src == "new" else "prelist"
        ms = [r["mint"] for r in db.q(f"select mint from {table} where addr=?", (c["addr"],))]
        redo.append({"addr": c["addr"], "n": len(ms), "mints": ",".join(ms), "src": src, "slow": c["status"] == "no selectiva"})
    fresh, seen = [], {h["addr"] for h in redo}
    for pend in tiers:
        for pair in itertools.zip_longest(*pend):   # una de cada categoría del grupo, por turnos
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
    log(f"antes de listados: {len(hits_l)} wallets con {MIN_HITS}+ aciertos · recién nacidas: {len(hits_n)} con 2+ aciertos x{EARLY_X} · "
        f"traders famosos: {len(hits_k)} · financiadas por exchange: {len(hits_f)} · smart money de Jupiter: {len(hits_s)} · "
        f"top traders x5: {len(hits_x)}; "
        f"pendientes {len(pool)} ({len(redo)} se vuelven a medir); se miden hasta {WALLETS_PER_RUN} que no sean bots")
    passed = measured = checked = 0
    for h in pool:
        if measured >= WALLETS_PER_RUN or checked >= 80:
            break
        checked += 1
        # a los traders famosos les llegan muchas firmas basura: se leen más para cubrir suficientes compras suyas
        prof, trades = history(h["addr"], 4000 if h["src"] == "kol" else MAX_SIGS)
        tx_day = (prof or {}).get("tx_day", 0)
        if tx_day <= SELECT_TX_DAY:
            measured += 1   # los bots y las que compran de todo se descartan rápido y no gastan hueco
        # fuera de muestra: TODOS sus tokens de las dos tablas (no solo los aciertos de una); score quita además los ganadores
        sel_mints = set(h["mints"].split(",")) | {r["mint"] for r in db.q(
            "select mint from prelist where addr=? union select mint from early where addr=?", (h["addr"], h["addr"]))}
        if (prof or {}).get("faltan"):
            # historial incompleto (el RPC no devolvió parte de sus transacciones): NO se guarda como «no pasa» con n=0;
            # si se guardara, `skip` (found de menos de 14 días) y `leads` (addr not in candidates) la dejarían fuera dos
            # semanas y `redo` tampoco la recoge (pct_x2 = 0). Las tx ya leídas quedan en caché: el reintento solo pide las que faltan.
            log(f"{h['addr'][:8]} historial incompleto ({prof['faltan']} tx sin leer de {prof.get('leidas', 0) + prof['faltan']}): se reintenta en la próxima vuelta")
            continue
        st = score(trades, sel_mints) if trades else None
        ok = bool(st and st["n"] >= PASS["n"] and st["pct_x2"] > PASS["pct_x2"] and st["best"] >= PASS["best"]
                  and st["robust"] >= PASS["robust"] and st["won"] >= PASS["won"] and st["tokens_day"] <= MAX_TOKENS_DAY
                  and st["lcb"] >= PASS["lcb"] and st["mitad_nueva"] >= PASS["mitad_nueva"]
                  and st["no_medibles"] <= 0.2 * (st["n"] + st["no_medibles"]) and st["raras"] <= 0.2 * st["n"]
                  and st["sin_mejor_semana"] >= PASS["sin_mejor_semana"] and st["ult_21d"] >= PASS["ult_21d"]
                  and st["n_21d"] >= PASS["n_21d"] and time.time() - last_own(trades) <= PASS["dias"] * 86400)
        status = "nueva" if ok else "bot" if tx_day > MAX_TX_DAY else "no selectiva" if tx_day > SELECT_TX_DAY else "no pasa"
        st = st or {"n": 0, "pct_x2": 0, "avg_xmax": 0, "ladder": 0, "all_x2": 0, "copy": 0, "copy_sl30": 0, "copy_sl50": 0,
                    "x2": 0, "x2_sl30": 0, "x2_sl50": 0, "plan": "", "best": 0, "robust": 0, "won": 0, "tokens_day": 0}
        db.x("insert or replace into candidates(addr, origin, found, score, n, pct_x2, ladder, all_x2, avg_xmax, hits, detail, status) "
             "values(?,?,?,?,?,?,?,?,?,?,?,?)",
             (h["addr"], ORIGIN[h["src"]], int(time.time()), st["best"], st["n"], st["pct_x2"],
              st["ladder"], st["all_x2"], st["avg_xmax"], h["n"],
              json.dumps({"perfil": prof, "copia": {k: st.get(k) for k in ("copy", "copy_sl30", "copy_sl50", "x2", "x2_sl30", "x2_sl50", "plan", "best",
                                                            "robust", "robust3", "won", "tokens_day", "lcb", "mitad_nueva", "no_medibles",
                                                            "raras", "no_copiables", "min_x2", "sin_mejor_semana",
                                                            "ult_21d", "n_21d")},
                          "muestra": st.get("muestra"), "v": 5}), status))
        log(f"{h['addr'][:8]} aciertos {h['n']} -> {status} {({k: v for k, v in st.items() if k != 'muestra'})}")
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
