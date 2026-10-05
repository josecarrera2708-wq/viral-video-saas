"""Buscador diario de wallets (se lanza cada noche con systemd: python -m app.buscador).

Repite por lotes el estudio que hicimos a mano:
 1. Nuevos listados de memecoins de Solana en Gate, Bitget, KuCoin, MEXC, OKX y BingX (últimos 60 días).
 2. Quién compró cada token en las 96 h antes del listado (operaciones de Jupiter) y a qué x llegó en el listado.
 3. Wallets que repiten acierto (compraron antes y el token llegó a x2+) en 3 o más listados.
 4. Fuera bots (cientos de operaciones al día) y wallets inactivas.
 5. Se mide cada wallet en sus últimas compras de OTROS tokens (fuera de muestra) con la regla del usuario:
    x desde su precio de compra hasta el máximo posterior, y su método (vender el 50% en cada x2).
 6. Las que pasan el corte aparecen en la app (pestaña Buscador) y llega un aviso.
Todo es reanudable: lo ya hecho se guarda en la base de datos y no se repite.
"""
import collections
import datetime
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from . import cex, chain, db

UA = chain.UA
DAYS = 60                 # listados de los últimos N días (Jupiter guarda unos 3 meses de operaciones)
TOKENS_PER_RUN = int(os.environ.get("SENALES_TOKENS", 12))   # listados nuevos que se procesan por noche
WALLETS_PER_RUN = int(os.environ.get("SENALES_WALLETS", 12))  # wallets que se miden por noche
MIN_BUY_USD = 500         # compra mínima antes del listado para contar como acierto
MIN_X = 2.0               # x mínima al llegar el listado
MIN_HITS = int(os.environ.get("SENALES_MIN_HITS", 3))        # aciertos mínimos para medir la wallet
MAX_TX_DAY = 300          # más que esto = bot
PASS = {"n": 10, "pct_x2": 45, "ladder": 10}   # corte para aparecer como candidata
C = httpx.Client(headers=UA, timeout=30, follow_redirects=True)


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


def history(addr, max_tx=800):
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
    if prof["tx_day"] > MAX_TX_DAY or time.time() - prof["last"] > 30 * 86400:
        return prof, []
    sol_usd = (get("https://lite-api.jup.ag/price/v3", ids=chain.WSOL) or {}).get(chain.WSOL, {}).get("usdPrice") or 120
    since = time.time() - DAYS * 86400
    sel = [x["signature"] for x in ok if x["blockTime"] >= since][:max_tx]

    def one(sig):
        tx = rpc("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
        return chain.detect(chain.parse_tx(tx), {addr: {}}, sol_usd, infer_payer=True) if tx else []
    with ThreadPoolExecutor(6 if db.get("helius_key") else 2) as ex:
        trades = [t for r in ex.map(one, sel) for t in r]
    return prof, trades


def gt_candles(mint):
    pools = get(f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}/pools", page=1) or {}
    pool = ((pools.get("data") or [{}])[0].get("attributes") or {}).get("address")
    time.sleep(2.2)
    if not pool:
        return []
    r = get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/hour",
            aggregate=4, limit=1000, token=mint, currency="usd") or {}
    time.sleep(2.2)
    return [[c[0], c[2], c[4]] for c in ((r.get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []]


def ladder(xmax, xnow):
    n = 0
    while xmax >= 2 ** (n + 1):
        n += 1
    return n + 0.5 ** n * xnow


def score(trades, exclude):
    """Mide las primeras compras de cada token (fuera de muestra) con la regla del usuario."""
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
    rows = []
    for b in buys:
        c = gt_candles(b["mint"])
        after = [k for k in c if k[0] + 14400 > b["t"]]
        if not after or not b["price"]:
            continue
        e = b["price"]
        xmax = max(1.0, max(k[1] for k in after) / e)
        if xmax > 500:          # dato roto (pico de un pool recién creado)
            continue
        xnow = (now_p.get(b["mint"]) or sorted(c)[-1][2]) / e
        rows.append((xmax, xnow))
    n = len(rows)
    if not n:
        return None
    return {"n": n, "pct_x2": round(100 * sum(1 for a, _ in rows if a >= 2) / n),
            "avg_xmax": round(sum(a for a, _ in rows) / n, 2),
            "ladder": round(100 * (sum(ladder(a, b) for a, b in rows) / n - 1)),
            "all_x2": round(100 * (sum(2 if a >= 2 else b for a, b in rows) / n - 1))}


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
    log(f"{len(toks)} listados en {DAYS} días; esta noche se procesan {len(todo)}")
    for tk in todo:
        b = prelist_buyers(tk["mint"], tk["t_list"])
        db.xm("insert or replace into prelist(addr, mint, usd, x, t) values(?,?,?,?,?)",
              [(o, tk["mint"], v["usd"], v["x"], v["t"]) for o, v in b.items()])
        db.x("update scan_tokens set done=1, buyers=? where mint=?", (len(b), tk["mint"]))
        log(f"{tk['sym']} ({tk['exch']}): {len(b)} compradores antes del listado")

    followed = {r["addr"] for r in db.q("select addr from wallets")}
    skip = {r["addr"] for r in db.q("select addr from candidates where status='bot' or found > ?", (int(time.time()) - 14 * 86400,))}
    hits = db.q("select addr, count(*) n, group_concat(mint) mints from prelist where usd>=? and x>=? group by addr having n>=? order by n desc",
                (MIN_BUY_USD, MIN_X, MIN_HITS))
    pool = [h for h in hits if h["addr"] not in followed and h["addr"] not in skip]
    log(f"{len(hits)} wallets con {MIN_HITS}+ aciertos; pendientes {len(pool)}; se miden hasta {WALLETS_PER_RUN} que no sean bots")
    passed = measured = checked = 0
    for h in pool:
        if measured >= WALLETS_PER_RUN or checked >= 80:
            break
        checked += 1
        prof, trades = history(h["addr"])
        if not (prof and prof.get("tx_day", 0) > MAX_TX_DAY):
            measured += 1   # los bots se descartan rápido y no gastan hueco
        sel_mints = set(h["mints"].split(","))
        st = score(trades, sel_mints) if trades else None
        ok = bool(st and st["n"] >= PASS["n"] and st["pct_x2"] >= PASS["pct_x2"] and st["ladder"] >= PASS["ladder"])
        status = "nueva" if ok else ("bot" if prof and prof.get("tx_day", 0) > MAX_TX_DAY else "no pasa")
        st = st or {"n": 0, "pct_x2": 0, "avg_xmax": 0, "ladder": 0, "all_x2": 0}
        db.x("insert or replace into candidates(addr, origin, found, score, n, pct_x2, ladder, all_x2, avg_xmax, hits, detail, status) "
             "values(?,?,?,?,?,?,?,?,?,?,?,?)",
             (h["addr"], "compra antes de los listados", int(time.time()), st["ladder"] + st["pct_x2"] / 2, st["n"], st["pct_x2"],
              st["ladder"], st["all_x2"], st["avg_xmax"], h["n"], json.dumps({"perfil": prof}), status))
        log(f"{h['addr'][:8]} aciertos {h['n']} -> {status} {st}")
        if ok:
            passed += 1
            push("Buscador: nueva wallet candidata",
                 f"{st['pct_x2']}% de sus compras llegan a x2 · tu método {st['ladder']:+d}% · {h['n']} aciertos antes de listados")
    msg = f"{len(todo)} listados nuevos, {measured} wallets medidas ({checked - measured} bots descartados), {passed} pasan el corte"
    db.put("last_scan", {"t": int(time.time()), "msg": msg, "secs": int(time.time() - t0)})
    log("FIN:", msg)


if __name__ == "__main__":
    if sys.argv[1:2] == ["listados"]:
        for m, sym, ex, t in sorted(listings(), key=lambda x: -x[3]):
            print(sym, ex, datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"), m)
    else:
        main()
