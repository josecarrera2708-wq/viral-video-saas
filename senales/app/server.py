"""Servidor de señales: recibe los avisos de Helius en tiempo real, vigila las wallets, sigue cada
token comprado (x hasta el máximo y tu método) y sirve la app web privada."""
import asyncio
import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import cex, chain, db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("senales")
STATIC = os.path.join(os.path.dirname(__file__), "static")
HELIUS = "https://mainnet.helius-rpc.com"
TRACK_DAYS = 14          # días que se sigue el precio de cada token comprado
POLL_S = int(os.environ.get("SENALES_POLL_S", "90"))   # sondeo de respaldo por si se pierde un aviso
NOTIFY_MAX_AGE = 900     # solo se avisa de operaciones de los últimos 15 min
CEX_S = 600              # cada cuánto se miran los listados de MEXC, Gate, Bitget y KuCoin
# «Posible listado»: perfil de los tokens que listaron esos exchanges (la mayoría con 0-5 días de vida)
HINT_MAX_AGE = 5 * 86400
HINT_MIN_MC = 300_000
HINT_MIN_HOLDERS = 1000
S = {"client": None, "market": None, "queue": None, "last_hook": 0, "last_poll": 0, "fails": {},
     "bg": set(), "busy": set(), "tried": {}}


# ---------- utilidades ----------
def fmt_usd(v):
    if v is None:
        return "?"
    v = float(v)
    if v >= 1e9:
        return f"${v / 1e9:.2f}B"
    if v >= 1e6:
        return f"${v / 1e6:.2f}M"
    if v >= 1e3:
        return f"${v / 1e3:.1f}k"
    return f"${v:,.0f}"


def fmt_price(p):
    if not p:
        return "?"
    if p >= 1:
        return f"${p:,.4f}"
    dec = f"{p:.15f}".split(".")[1]
    zeros = len(dec) - len(dec.lstrip("0"))
    return f"${p:.{zeros + 4}f}"


def tz():
    try:
        return ZoneInfo(db.get("tz", "Europe/Madrid"))
    except Exception:
        return ZoneInfo("Europe/Madrid")


def hhmm(t):
    return datetime.datetime.fromtimestamp(t, tz()).strftime("%d/%m %H:%M")


def ladder(xmax, xnow):
    """Tu método: en cada x2 (x2, x4, x8...) vendes el 50% de lo que queda; el resto vale lo que valga hoy."""
    n = 0
    while xmax >= 2 ** (n + 1):
        n += 1
    return n + 0.5 ** n * xnow


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.scrypt(pw.encode(), salt=salt.encode(), n=2 ** 14, r=8, p=1).hex()
    return f"{salt}${h}"


def check_pw(pw, stored):
    try:
        salt, _ = stored.split("$", 1)
        return hmac.compare_digest(hash_pw(pw, salt), stored)
    except Exception:
        return False


def wallets_cfg(active_only=True):
    rows = db.q("select * from wallets" + (" where active=1" if active_only else "") + " order by rank, added")
    for r in rows:
        r["payers"] = json.loads(r.get("payers") or "[]")
    return rows


def rpc_urls():
    key = db.get("helius_key")
    urls = [chain.PUBLIC_RPC]
    if key:
        urls.append(f"{HELIUS}/?api-key={key}")
    return urls


# ---------- avisos al móvil (Web Push) ----------
def vapid():
    v = db.get("vapid")
    if v:
        return v
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    k = ec.generate_private_key(ec.SECP256R1())
    priv = k.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                           serialization.NoEncryption()).decode()
    pub = k.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    v = {"private_pem": priv, "public": base64.urlsafe_b64encode(pub).decode().rstrip("=")}
    db.put("vapid", v)
    return v


def _vapid_der(v):
    """pywebpush quiere la clave privada en DER (base64), no en PEM."""
    from cryptography.hazmat.primitives import serialization
    k = serialization.load_pem_private_key(v["private_pem"].encode(), None)
    der = k.private_bytes(serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    return base64.urlsafe_b64encode(der).decode().rstrip("=")


def _push_sync(title, body, url="/", tag=None):
    from pywebpush import WebPushException, webpush
    v = vapid()
    key = _vapid_der(v)
    sent = 0
    for s in db.q("select * from subs"):
        try:
            webpush(subscription_info=json.loads(s["data"]),
                    data=json.dumps({"title": title, "body": body, "url": url, "tag": tag or str(time.time())}),
                    vapid_private_key=key, vapid_claims={"sub": "mailto:avisos@senales.app"}, ttl=3600)
            sent += 1
        except WebPushException as e:
            code = getattr(e.response, "status_code", 0)
            if code in (404, 410):
                db.x("delete from subs where endpoint=?", (s["endpoint"],))
            log.warning("push falló %s", code)
        except Exception as e:
            log.warning("push falló %s", e)
    db.put("last_push", {"t": int(time.time()), "title": title, "body": body, "sent": sent})
    return sent


async def push(title, body, url="/", tag=None):
    return await asyncio.to_thread(_push_sync, title, body, url, tag)


# ---------- operaciones ----------
def bg(coro):
    """Lanza una tarea en segundo plano sin que se pierda (asyncio solo guarda referencias débiles)."""
    t = asyncio.create_task(coro)
    S["bg"].add(t)

    def done(t):
        S["bg"].discard(t)
        if not t.cancelled() and t.exception():
            log.warning("tarea en segundo plano: %r", t.exception())
    t.add_done_callback(done)
    return t


async def rpc_any(method, params):
    for url in rpc_urls():
        r = await chain.rpc(S["client"], url, method, params)
        if r is not None:
            return r
    return None


def listing_hint(mint, info, mc, t):
    """Exchanges donde cotiza (o va a cotizar) el token, o «posible listado» si se parece a los que suelen listarse."""
    rows = db.q("select exch, t_start from cex where mint=?", (mint,))
    if rows:
        names = ", ".join(sorted(cex.NAMES.get(r["exch"], r["exch"]) for r in rows))
        return ("se lista en " if all(r["t_start"] > time.time() for r in rows) else "cotiza en ") + names
    if info.get("created") and t - info["created"] <= HINT_MAX_AGE and (mc or 0) >= HINT_MIN_MC \
            and info.get("holders", 0) >= HINT_MIN_HOLDERS:
        return "posible listado"
    return None


async def record(tr, w, source):
    """Guarda una compra o venta y actualiza la posición de la wallet en ese token."""
    info = await S["market"].token(tr["mint"])
    mc = tr["price"] * info["supply"] if info["supply"] else None
    if db.q("select 1 from trades where sig=? and wallet=? and mint=?", (tr["sig"], tr["wallet"], tr["mint"]), one=True):
        return info, mc, False  # ya guardada (p. ej. la encontraron a la vez el sondeo y la búsqueda en el historial)
    tr["hint"] = listing_hint(tr["mint"], info, mc, tr["t"]) if tr["side"] == "buy" else None
    db.x("insert or ignore into trades(sig, wallet, mint, side, t, amount, usd, sol, price, mc, sym, hint) values(?,?,?,?,?,?,?,?,?,?,?,?)",
         (tr["sig"], tr["wallet"], tr["mint"], tr["side"], tr["t"], tr["amount"], tr["usd"], tr["sol"], tr["price"], mc, info["sym"], tr["hint"]))
    pos = db.q("select * from positions where wallet=? and mint=?", (tr["wallet"], tr["mint"]), one=True)
    if tr["side"] == "buy":
        if not pos:
            db.x("insert into positions(wallet, mint, sym, icon, first_t, entry_price, entry_mc, usd_in, max_price, max_t, last_price, last_t, supply) "
                 "values(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                 (tr["wallet"], tr["mint"], info["sym"], info["icon"], tr["t"], tr["price"], mc, tr["usd"],
                  tr["price"], tr["t"], tr["price"], tr["t"], info["supply"]))
        elif tr["t"] < pos["first_t"]:  # compra más antigua encontrada al buscar en el historial
            db.x("update positions set usd_in=usd_in+?, first_t=?, entry_price=?, entry_mc=?, bf=null where wallet=? and mint=?",
                 (tr["usd"], tr["t"], tr["price"], mc, tr["wallet"], tr["mint"]))
        else:
            db.x("update positions set usd_in=usd_in+? where wallet=? and mint=?", (tr["usd"], tr["wallet"], tr["mint"]))
    elif pos:
        db.x("update positions set usd_out=usd_out+? where wallet=? and mint=?", (tr["usd"], tr["wallet"], tr["mint"]))
    log.info("%s %s %s %s via %s", w["name"], tr["side"], info["sym"], tr["usd"], source)
    return info, mc, True


def cost_basis(wallet, mint, t):
    """Precio medio de las compras vistas hasta `t`, tokens que cubren y tokens vendidos hasta `t`."""
    b = db.q("select sum(usd) u, sum(amount) a from trades where wallet=? and mint=? and side='buy' and t<=?", (wallet, mint, t), one=True)
    s = db.q("select sum(amount) a from trades where wallet=? and mint=? and side='sell' and t<=?", (wallet, mint, t), one=True)
    return (b["u"] / b["a"] if b["a"] else None), (b["a"] or 0), (s["a"] or 0)


async def backfill_buys(tr, acct=None):
    """Busca en el historial de la cuenta de ese token las compras que no vimos (anteriores a vigilarla)."""
    w = {x["addr"]: x for x in wallets_cfg(False)}.get(tr["wallet"])
    if not w:
        return
    if not acct:
        tx = await rpc_any("getTransaction", [tr["sig"], {"encoding": "json", "maxSupportedTransactionVersion": 1}])
        if not tx:
            raise RuntimeError("no se pudo leer la venta")
        acct = (chain.parse_tx(tx) or {}).get("acct", {}).get((tr["wallet"], tr["mint"]))
        if not acct:
            return
    sigs = await rpc_any("getSignaturesForAddress", [acct, {"limit": 100, "before": tr["sig"]}])
    if sigs is None:
        raise RuntimeError("no se pudo leer el historial")
    for s in reversed(sigs[:60]):
        sig = s["signature"]
        if s.get("err") or db.q("select 1 from trades where sig=? and wallet=?", (sig, tr["wallet"]), one=True):
            continue
        tx = await rpc_any("getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
        p = chain.parse_tx(tx)
        if not p:
            continue
        sol_usd = await S["market"].sol_usd_at(p["t"])
        mine = {w["addr"]: w}
        found = [x for x in chain.detect(p, mine, sol_usd) if x["mint"] == tr["mint"]] or \
                [x for x in chain.detect(p, mine, sol_usd, infer_payer=True) if x["mint"] == tr["mint"]]
        for x in found:
            db.x("insert or ignore into seen(sig, t) values(?, ?)", (sig, int(time.time())))
            await record(x, w, "historial")


async def sell_entry(tr, acct=None):
    """Precio medio al que la wallet compró lo que ahora vende (0 si no se encuentra la compra)."""
    key, tok = (tr["sig"], tr["wallet"], tr["mint"]), (tr["wallet"], tr["mint"])
    while tok in S["busy"]:  # una sola búsqueda a la vez por wallet y token
        await asyncio.sleep(1)
    row = db.q("select entry from trades where sig=? and wallet=? and mint=?", key, one=True)
    if row and row["entry"] is not None:
        return row["entry"]
    S["busy"].add(tok)
    try:
        e, have, sold = cost_basis(tr["wallet"], tr["mint"], tr["t"])
        if not e or have < 0.9 * sold:
            await backfill_buys(tr, acct)
            e, have, sold = cost_basis(tr["wallet"], tr["mint"], tr["t"])
        e = e or 0
        db.x("update trades set entry=? where sig=? and wallet=? and mint=?", (e,) + key)
        return e
    finally:
        S["busy"].discard(tok)


def gain(tr, entry):
    """Ganancia de una venta en dólares y en x sobre su precio medio de compra."""
    if not entry:
        return None, None
    return tr["usd"] - tr["amount"] * entry, tr["price"] / entry


async def notify(tr, w, info, mc, entry=None):
    verb = "COMPRA" if tr["side"] == "buy" else "VENDE"
    body = f"{fmt_usd(tr['usd'])}"
    if tr["sol"] >= 0.05:
        body += f" ({tr['sol']:.2f} SOL)"
    body += f" · {hhmm(tr['t'])} · precio {fmt_price(tr['price'])} · MC {fmt_usd(mc)}"
    if tr["side"] == "buy" and mc:
        body += f" · x2 = MC {fmt_usd(2 * mc)}"
    if tr.get("hint"):
        body += f" · {tr['hint']}"
    if tr.get("paid_with"):
        body += f" · pagó con {(await S['market'].token(tr['paid_with']))['sym']}"
    pnl, xs = gain(tr, entry)
    if pnl is not None:
        body += f" · {'ganó' if pnl >= 0 else 'perdió'} {fmt_usd(abs(pnl))} (x{xs:.2f})"
    await push(f"{w['name'].upper()} {verb} {info['sym']}", body, url=f"/#t/{tr['mint']}", tag=tr["sig"])


async def finish_sell(tr, w, info, mc, acct, fresh):
    """Calcula la ganancia de la venta y avisa. El aviso espera como mucho 20 s a la búsqueda de la compra."""
    task = bg(sell_entry(tr, acct))
    entry = None
    try:
        entry = await asyncio.wait_for(asyncio.shield(task), 20)
    except Exception:
        pass
    if fresh:
        await notify(tr, w, info, mc, entry)


async def value_swaps(found):
    """Un cambio directo de un memecoin por otro se guarda como venta del que entrega y compra del que recibe,
    valorados con el precio de ahora (solo si la operación es reciente)."""
    out = []
    for x in found:
        if x["side"] != "swap":
            out.append(x)
            continue
        if time.time() - x["t"] > 3600:
            continue
        pr = await S["market"].prices([x["mint_in"], x["mint_out"]])
        usd = x["amt_out"] * pr[x["mint_out"]] if pr.get(x["mint_out"]) else x["amt_in"] * pr[x["mint_in"]] if pr.get(x["mint_in"]) else 0
        if usd < chain.MIN_USD:
            continue
        base = {"sig": x["sig"], "t": x["t"], "wallet": x["wallet"], "usd": round(usd, 2), "sol": 0}
        out.append({**base, "mint": x["mint_out"], "side": "sell", "amount": x["amt_out"], "price": usd / x["amt_out"]})
        out.append({**base, "mint": x["mint_in"], "side": "buy", "amount": x["amt_in"], "price": usd / x["amt_in"], "paid_with": x["mint_out"]})
    return out


async def process_tx(tx, source="hook"):
    p = chain.parse_tx(tx)
    if not p or not p["sig"]:
        return
    if db.q("select 1 from seen where sig=?", (p["sig"],), one=True):
        return
    db.x("insert or ignore into seen(sig, t) values(?, ?)", (p["sig"], int(time.time())))
    ws = {w["addr"]: w for w in wallets_cfg()}
    if not ws:
        return
    for tr in await value_swaps(chain.detect(p, ws, await S["market"].sol_usd_at(p["t"]), swaps=True)):
        w = ws[tr["wallet"]]
        info, mc, new = await record(tr, w, source)
        if new:
            pre = p["pre"].get((tr["wallet"], tr["mint"])) or 0
            await sim_on_trade(tr, info, min(1.0, tr["amount"] / pre) if pre else 1.0)
        fresh = time.time() - tr["t"] <= NOTIFY_MAX_AGE
        if tr["side"] == "sell":
            bg(finish_sell(tr, w, info, mc, p["acct"].get((tr["wallet"], tr["mint"])), fresh))
        elif fresh:
            await notify(tr, w, info, mc)


# ---------- simulación de copia ----------
SIM_FEE = 0.01   # comisión de cada compra y de cada venta
STRATS = {"copiar": "copiar todo", "x2": "todo en x2"}


def sim_cfg():
    """{"start", "days", "usd", "plan": {wallet: [{"strat": "copiar"|"x2", "sl": 0.3|0.5|null, "medido": %}, ...]}}
    Una wallet puede probar varias estrategias a la vez; cada una lleva sus propias operaciones."""
    return db.get("sim") or {}


def sim_plans(c, wallet):
    v = (c.get("plan") or {}).get(wallet) or []
    return v if isinstance(v, list) else [v]


def sim_window(c, plan):
    """Cada estrategia dura «days» desde su propio inicio (la de una wallet añadida después empieza al añadirla)."""
    start = plan.get("start") or c["start"]
    return start, start + c["days"] * 86400


SIM_LOCK = asyncio.Lock()   # el sondeo y el seguimiento no pueden cerrar a la vez la misma operación


async def sim_on_trade(tr, info, frac):
    """Una operación nueva de una wallet: la simulación abre o vende como lo haría el copy trade."""
    async with SIM_LOCK:
        await _sim_on_trade(tr, info, frac)


async def _sim_on_trade(tr, info, frac):
    c = sim_cfg()
    if not c:
        return
    for plan in sim_plans(c, tr["wallet"]):
        start, end = sim_window(c, plan)
        if not start <= tr["t"] < end:
            continue
        same = (tr["wallet"], tr["mint"], plan["strat"], plan.get("sl"))
        if tr["side"] == "buy":
            if plan["strat"] == "x2" and db.q("select 1 from sim where wallet=? and mint=? and strat=? and sl is ?", same, one=True):
                continue  # con «todo en x2» solo cuenta la primera compra de cada token
            db.x("insert into sim(wallet, mint, sym, strat, sl, opened, entry, qty, usd_in, last, chk) values(?,?,?,?,?,?,?,?,?,?,?)",
                 (tr["wallet"], tr["mint"], info["sym"], plan["strat"], plan.get("sl"), tr["t"], tr["price"],
                  c["usd"] * (1 - SIM_FEE) / tr["price"], c["usd"], tr["price"], tr["t"]))
        elif plan["strat"] == "copiar":
            for lot in db.q("select * from sim where wallet=? and mint=? and strat=? and sl is ? and closed is null", same):
                # una venta que llega tarde: antes, el stop que pudo saltar mientras el servidor estaba parado
                if await sim_catchup(lot, tr["t"]):
                    continue
                lot = db.q("select * from sim where id=?", (lot["id"],), one=True)
                sim_sell(lot, lot["qty"] * frac, tr["price"], tr["t"], "vendió la wallet")


def sim_sell(lot, qty, price, t, reason):
    out, left = qty * price * (1 - SIM_FEE), lot["qty"] - qty
    if left <= lot["qty"] * 1e-6:
        db.x("update sim set qty=0, usd_out=usd_out+?, last=?, closed=?, reason=? where id=?", (out, price, t, reason, lot["id"]))
    else:
        db.x("update sim set qty=?, usd_out=usd_out+?, last=? where id=?", (left, out, price, lot["id"]))


SIM_GAP = 180   # s sin revisar una operación a partir de los cuales se repasan las velas de 1 min


def sim_end(lot, c=None):
    c = c or sim_cfg()
    plan = next((p for p in sim_plans(c, lot["wallet"]) if p["strat"] == lot["strat"] and p.get("sl") == lot["sl"]), {})
    return sim_window(c, plan)[1]


async def sim_catchup(lot, until):
    """Si el servidor estuvo parado, el x2, el stop y el fin de la prueba se aplican cuando ocurrieron (con las velas
    de 1 min), no al volver. Devuelve True si la operación quedó cerrada."""
    chk = lot["chk"] or lot["opened"]
    if until - chk < SIM_GAP:
        return False
    end = sim_end(lot)
    upto = min(until, end)
    cs = await chain.gt_candles(S["client"], lot["mint"], chk, upto)
    e, sl = lot["entry"], lot["sl"]
    for t, o, h, lo, cl, *_ in cs:
        if t < chk // 60 * 60 + 60 or t >= upto:
            continue  # la vela en curso al revisar ya se miró (o es anterior a la compra)
        if sl and lo <= e * (1 - sl):   # stop y x2 en la misma vela: se supone que saltó antes el stop
            sim_sell(lot, lot["qty"], min(o, e * (1 - sl)), t + 60, f"stop {sl:.0%}")
            return True
        if lot["strat"] == "x2" and h >= 2 * e:
            sim_sell(lot, lot["qty"], 2 * e, t + 60, "x2")
            return True
    last = cs[-1][4] if cs else lot["last"]
    if until >= end:
        sim_sell(lot, lot["qty"], last, end, "fin de la prueba")
        return True
    db.x("update sim set last=?, chk=? where id=?", (last, upto if cs else until, lot["id"]))
    return False


async def sim_check(prices, now):
    """Cada minuto: objetivo x2, stop-loss y, al acabar la prueba, cierre de lo que quede abierto."""
    async with SIM_LOCK:
        await _sim_check(prices, now)


async def _sim_check(prices, now):
    c = sim_cfg()
    if not c:
        return
    for lot in db.q("select * from sim where closed is null"):
        if await sim_catchup(lot, now):
            continue
        lot = db.q("select * from sim where id=?", (lot["id"],), one=True)
        v = prices.get(lot["mint"])
        if not v or lot["closed"]:
            continue
        if now >= sim_end(lot, c):
            sim_sell(lot, lot["qty"], v, now, "fin de la prueba")
        elif lot["strat"] == "x2" and v >= 2 * lot["entry"]:
            sim_sell(lot, lot["qty"], 2 * lot["entry"], now, "x2")
        elif lot["sl"] and v <= lot["entry"] * (1 - lot["sl"]):
            sim_sell(lot, lot["qty"], v, now, f"stop {lot['sl']:.0%}")
        else:
            db.x("update sim set last=?, chk=? where id=?", (v, now, lot["id"]))


def sim_summary():
    c = sim_cfg()
    if not c:
        return {"cfg": None, "rows": []}
    rows = []
    for w, plan in ((w, plan) for w in wallets_cfg(False) for plan in sim_plans(c, w["addr"])):
        lots = db.q("select * from sim where wallet=? and strat=? and sl is ?", (w["addr"], plan["strat"], plan.get("sl")))
        inv = sum(x["usd_in"] for x in lots)
        val = sum(x["usd_out"] + x["qty"] * (x["last"] or x["entry"]) * (1 - SIM_FEE) for x in lots)
        done = [x for x in lots if x["closed"]]
        label = STRATS.get(plan["strat"], plan["strat"]) + (f" · stop {plan['sl']:.0%}" if plan.get("sl") else " · sin stop")
        start, end = sim_window(c, plan)
        rows.append({"name": w["name"], "plan": label, "medido": plan.get("medido"), "n": len(lots), "start": start, "end": end,
                     "won": sum(1 for x in done if x["usd_out"] > x["usd_in"]), "lost": sum(1 for x in done if x["usd_out"] <= x["usd_in"]),
                     "open": len(lots) - len(done), "invested": round(inv, 2), "pnl": round(val - inv, 2),
                     "pct": round(100 * (val - inv) / inv, 1) if inv else None})
    return {"cfg": {k: c[k] for k in ("start", "days", "usd")}, "rows": rows}


async def listing_alert(mint, exch, t_start):
    """Un exchange acaba de dar de alta un token: si una Ganadora lo compró en los últimos 30 días, aviso."""
    pos = db.q("select p.*, w.name from positions p join wallets w on w.addr=p.wallet "
               "where p.mint=? and w.active=1 and p.first_t>? order by p.first_t", (mint, int(time.time()) - 30 * 86400))
    if not pos:
        return
    p0, name = pos[0], cex.NAMES.get(exch, exch)
    x = (p0["last_price"] or p0["entry_price"]) / p0["entry_price"] if p0["entry_price"] else None
    who = ", ".join(sorted({p["name"] for p in pos}))
    body = f"Lo compró {who} el {hhmm(p0['first_t'])} (MC {fmt_usd(p0['entry_mc'])})" + (f" · ahora x{x:.2f}" if x else "")
    body += f" · empieza a cotizar {hhmm(t_start)}" if t_start > time.time() else " · ya cotiza"
    log.info("listado en %s de %s (%s)", name, p0["sym"], who)
    await push(f"LISTADO EN {name.upper()}: {p0['sym']}", body, url=f"/#t/{mint}", tag=f"cex-{exch}-{mint}")


async def cex_watch():
    """Tokens de Solana nuevos en MEXC, Gate, Bitget o KuCoin (por contrato). La primera vez que responde
    cada exchange solo se toma la foto de lo que ya cotizaba, sin avisar."""
    while True:
        try:
            snap = await asyncio.to_thread(cex.snapshot)
            now = int(time.time())
            have = {}
            for r in db.q("select mint, exch from cex"):
                have.setdefault(r["exch"], set()).add(r["mint"])
            for exch in cex.NAMES:
                fresh = [(m, v[exch]) for m, v in snap["mints"].items() if exch in v and m not in have.get(exch, ())]
                if not fresh:
                    continue
                db.xm("insert or ignore into cex(mint, exch, t_start, t_seen) values(?,?,?,?)", [(m, exch, t, now) for m, t in fresh])
                if exch in have:
                    for m, t in fresh:
                        await listing_alert(m, exch, t)
        except Exception:
            log.exception("error vigilando los listados")
        await asyncio.sleep(CEX_S)


async def entries():
    """Respaldo: ventas a las que aún les falta el precio de compra (p. ej. si falló la red)."""
    while True:
        try:
            now = int(time.time())
            for t in db.q("select * from trades where side='sell' and entry is null and t > ? order by t desc limit 5", (now - 30 * 86400,)):
                key = (t["sig"], t["wallet"], t["mint"])
                if S["tried"].get(key, 0) > now - 3600 or key[1:] in S["busy"]:
                    continue
                S["tried"][key] = now
                try:
                    await asyncio.wait_for(sell_entry(t), 180)
                except Exception:
                    log.exception("no se pudo calcular la ganancia de una venta")
        except Exception:
            log.exception("error en el respaldo de ganancias")
        await asyncio.sleep(60)


async def worker():
    while True:
        tx = await S["queue"].get()
        try:
            await process_tx(tx, "hook")
        except Exception:
            log.exception("error procesando aviso")


async def recent_sigs(addr, since, page=100, pages=5):
    """Firmas recientes de una wallet, de más nueva a más antigua. Tras un parón sigue hacia atrás hasta llegar a
    una ya vista o a `since`, para no perder operaciones (una wallet activa hace más de 20 en una hora)."""
    out, before = [], None
    for _ in range(pages):
        p = {"limit": page}
        if before:
            p["before"] = before
        sigs = None
        for url in rpc_urls():
            sigs = await chain.rpc(S["client"], url, "getSignaturesForAddress", [addr, p])
            if sigs is not None:
                break
        out += sigs or []
        if not sigs or len(sigs) < page or (sigs[-1].get("blockTime") or 0) < since \
                or db.q("select 1 from seen where sig=?", (sigs[-1]["signature"],), one=True):
            break
        before = sigs[-1]["signature"]
    return out


async def poller():
    """Respaldo: revisa las últimas firmas de cada wallet por si un aviso de Helius se perdió."""
    while True:
        try:
            since = (db.get("last_poll") or time.time()) - 120   # si el servidor estuvo parado, hasta donde se quedó
            for w in wallets_cfg():
                # las 20 últimas siempre (como antes, también para una wallet recién añadida); más atrás, solo el parón
                sigs = [s for i, s in enumerate(await recent_sigs(w["addr"], since)) if i < 20 or (s.get("blockTime") or 0) >= since]
                for s in reversed(sigs):
                    if s.get("err") or db.q("select 1 from seen where sig=?", (s["signature"],), one=True):
                        continue
                    tx = None
                    for url in rpc_urls():
                        tx = await chain.get_tx(S["client"], url, s["signature"])
                        if tx:
                            break
                    if tx:
                        await process_tx(tx, "sondeo")
            S["last_poll"] = int(time.time())
            db.put("last_poll", S["last_poll"])
        except Exception:
            log.exception("error en el sondeo")
        await asyncio.sleep(POLL_S)


async def tracker():
    """Cada minuto: precio actual de los tokens comprados; guarda el máximo desde la compra."""
    while True:
        try:
            now = int(time.time())
            pos = db.q("select wallet, mint, max_price from positions where first_t > ?", (now - TRACK_DAYS * 86400,))
            sim_open = [r["mint"] for r in db.q("select distinct mint from sim where closed is null")]
            if pos or sim_open:
                pr = await S["market"].prices([p["mint"] for p in pos] + sim_open)
                await sim_check(pr, now)
                for p in pos:
                    v = pr.get(p["mint"])
                    if not v:
                        continue
                    if v > (p["max_price"] or 0):
                        db.x("update positions set last_price=?, last_t=?, max_price=?, max_t=? where wallet=? and mint=?",
                             (v, now, v, now, p["wallet"], p["mint"]))
                    else:
                        db.x("update positions set last_price=?, last_t=? where wallet=? and mint=?", (v, now, p["wallet"], p["mint"]))
            for p in db.q("select wallet, mint, first_t, max_price from positions where bf is null and first_t < ? and first_t > ? limit 5",
                          (now - 600, now - TRACK_DAYS * 86400)):
                hi = await chain.gt_max(S["client"], p["mint"], p["first_t"])
                if hi and hi > (p["max_price"] or 0):
                    db.x("update positions set max_price=?, max_t=? where wallet=? and mint=?", (hi, now, p["wallet"], p["mint"]))
                db.x("update positions set bf=1 where wallet=? and mint=?", (p["wallet"], p["mint"]))
                await asyncio.sleep(2.2)
            db.x("delete from seen where t < ?", (now - 30 * 86400,))
        except Exception:
            log.exception("error en el seguimiento")
        await asyncio.sleep(60)


def wallet_stats(addr, days=30):
    pos = db.q("select * from positions where wallet=? and first_t > ?", (addr, int(time.time()) - days * 86400))
    rows = []
    for p in pos:
        e = p["entry_price"] or 0
        if not e:
            continue
        xmax, xnow = (p["max_price"] or e) / e, (p["last_price"] or e) / e
        rows.append((xmax, xnow))
    n = len(rows)
    if not n:
        return {"n": 0}
    return {"n": n, "pct_x2": round(100 * sum(1 for a, _ in rows if a >= 2) / n),
            "avg_xmax": round(sum(a for a, _ in rows) / n, 2),
            "ladder": round(100 * (sum(ladder(a, b) for a, b in rows) / n - 1)),
            "all_x2": round(100 * (sum(2 if a >= 2 else b for a, b in rows) / n - 1))}


async def daily_summary():
    while True:
        try:
            now = datetime.datetime.now(tz())
            hour = int(db.get("daily_hour", 21))
            key = now.strftime("%Y-%m-%d")
            if now.hour == hour and db.get("last_daily") != key:
                db.put("last_daily", key)
                parts = []
                t0 = int(time.time()) - 86400
                for w in wallets_cfg():
                    nb = db.q("select count(*) c from trades where wallet=? and side='buy' and t>?", (w["addr"], t0), one=True)["c"]
                    st = wallet_stats(w["addr"])
                    parts.append(f"{w['name']}: {nb} compras hoy" + (f", {st['pct_x2']}% llegan a x2 (30 d)" if st.get("n") else ""))
                if parts:
                    await push("Resumen del día", " · ".join(parts), url="/#wallets")
        except Exception:
            log.exception("error en el resumen diario")
        await asyncio.sleep(60)


async def sync_webhook():
    """Crea o actualiza el aviso en tiempo real de Helius con las wallets activas."""
    key, url = db.get("helius_key"), db.get("public_url")
    if not key or not url:
        return {"ok": False, "msg": "Falta la clave de Helius o la dirección pública"}
    secret = db.get("hook_secret") or secrets.token_urlsafe(24)
    db.put("hook_secret", secret)
    addrs = [w["addr"] for w in wallets_cfg()]
    body = {"webhookURL": url.rstrip("/") + "/hook", "webhookType": "raw", "transactionTypes": ["ANY"],
            "accountAddresses": addrs or ["11111111111111111111111111111111"], "authHeader": secret, "txnStatus": "success"}
    wid = db.get("webhook_id")
    c = S["client"]
    try:
        r = None
        if wid:
            r = await c.put(f"{HELIUS}/v0/webhooks/{wid}", params={"api-key": key}, json=body, timeout=30)
        if not wid or r.status_code in (400, 404):
            r = await c.post(f"{HELIUS}/v0/webhooks", params={"api-key": key}, json=body, timeout=30)
        if r.status_code >= 300:
            return {"ok": False, "msg": f"Helius respondió {r.status_code}: {r.text[:200]}"}
        j = r.json()
        db.put("webhook_id", j.get("webhookID") or wid)
        db.put("webhook_ok", int(time.time()))
        return {"ok": True, "msg": f"Aviso en tiempo real activo para {len(addrs)} wallets"}
    except Exception as e:
        return {"ok": False, "msg": f"No se pudo conectar con Helius: {e}"}


# ---------- app ----------
@asynccontextmanager
async def lifespan(app):
    S["client"] = httpx.AsyncClient(headers=chain.UA)
    S["market"] = chain.Market(S["client"])
    S["queue"] = asyncio.Queue()
    vapid()
    if not db.get("password") and not db.get("setup_token"):
        db.put("setup_token", (os.environ.get("SENALES_SETUP_CODE") or secrets.token_hex(4)).strip().upper())
    if db.get("setup_token"):
        with open(os.path.join(db.DATA, "codigo_inicial.txt"), "w") as f:
            f.write(db.get("setup_token") + "\n")
    if time.time() - (db.get("last_poll") or time.time()) > 300:
        # el servidor estuvo parado: el máximo de cada token se vuelve a mirar en las velas (pudo subir mientras tanto)
        db.x("update positions set bf=null where first_t > ?", (int(time.time()) - TRACK_DAYS * 86400,))
    tasks = [asyncio.create_task(t()) for t in (worker, poller, tracker, daily_summary, entries, cex_watch)]
    if db.get("helius_key"):
        asyncio.create_task(sync_webhook())
    yield
    for t in tasks:
        t.cancel()
    await S["client"].aclose()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
LOGIN_TRIES = {}


def authed(req: Request):
    tok = req.cookies.get("s")
    if not tok:
        return False
    r = db.q("select exp from sessions where token=?", (tok,), one=True)
    return bool(r and r["exp"] > time.time())


def need(req: Request):
    if not authed(req):
        raise HTTPException(401, "inicia sesión")


def login_response(data):
    tok = secrets.token_urlsafe(32)
    exp = int(time.time()) + 90 * 86400
    db.x("insert into sessions(token, exp) values(?, ?)", (tok, exp))
    r = JSONResponse(data)
    r.set_cookie("s", tok, max_age=90 * 86400, httponly=True, secure=True, samesite="lax")
    return r


@app.get("/api/me")
async def me(req: Request):
    return {"setup": not db.get("password"), "logged": authed(req)}


@app.post("/api/setup")
async def setup(req: Request):
    d = await req.json()
    if db.get("password"):
        raise HTTPException(400, "ya configurado")
    if (d.get("code") or "").strip().upper() != db.get("setup_token"):
        raise HTTPException(403, "código incorrecto")
    if len(d.get("password") or "") < 8:
        raise HTTPException(400, "la contraseña debe tener al menos 8 caracteres")
    db.put("password", hash_pw(d["password"]))
    db.put("setup_token", None)
    try:
        os.remove(os.path.join(db.DATA, "codigo_inicial.txt"))
    except OSError:
        pass
    host = req.headers.get("x-forwarded-host") or req.headers.get("host")
    if host and not db.get("public_url"):
        db.put("public_url", f"https://{host}")
    return login_response({"ok": True})


@app.post("/api/login")
async def login(req: Request):
    ip = req.headers.get("x-forwarded-for", req.client.host if req.client else "?").split(",")[0]
    n, t0 = LOGIN_TRIES.get(ip, (0, time.time()))
    if time.time() - t0 > 900:
        n, t0 = 0, time.time()
    if n >= 10:
        raise HTTPException(429, "demasiados intentos, espera 15 minutos")
    d = await req.json()
    if not check_pw(d.get("password") or "", db.get("password") or ""):
        LOGIN_TRIES[ip] = (n + 1, t0)
        raise HTTPException(403, "contraseña incorrecta")
    LOGIN_TRIES.pop(ip, None)
    return login_response({"ok": True})


@app.post("/api/logout")
async def logout(req: Request):
    db.x("delete from sessions where token=?", (req.cookies.get("s") or "",))
    r = JSONResponse({"ok": True})
    r.delete_cookie("s")
    return r


@app.get("/api/feed")
async def feed(req: Request, limit: int = 150, mint: str = ""):
    need(req)
    names = {w["addr"]: w for w in wallets_cfg(False)}
    sql = ("select t.*, p.entry_price, p.max_price, p.last_price, p.icon from trades t join wallets w on w.addr=t.wallet "
           "left join positions p on p.wallet=t.wallet and p.mint=t.mint")
    args = ()
    if mint:
        sql += " where t.mint=?"
        args = (mint,)
    rows = db.q(sql + " order by t.t desc limit ?", args + (min(limit, 500),))
    for r in rows:
        w = names.get(r["wallet"], {})
        r["name"], r["origin"], r["rank"] = w.get("name", r["wallet"][:6]), w.get("origin", ""), w.get("rank", 99)
        if r["side"] == "buy" and r["price"]:
            r["x_now"] = (r["last_price"] or r["price"]) / r["price"]
            r["x_max"] = max(1.0, (r["max_price"] or r["price"]) / r["price"])
        elif r["side"] == "sell":
            r["pnl"], r["x_sell"] = gain(r, r["entry"])
    return rows


@app.get("/api/sim")
async def sim_get(req: Request):
    need(req)
    return sim_summary()


@app.post("/api/sim")
async def sim_start(req: Request):
    """Empieza (o reinicia) la simulación: {"usd": 10, "days": 3, "plan": {wallet: [{"strat", "sl", "medido", "start"}, ...]}}."""
    need(req)
    d = await req.json()
    plan = {a: [{"strat": x.get("strat") if x.get("strat") in STRATS else "copiar", "sl": x.get("sl"), "medido": x.get("medido"),
                 "start": x.get("start")}
                for x in (v if isinstance(v, list) else [v])]
            for a, v in (d.get("plan") or {}).items()}
    db.x("delete from sim")
    db.put("sim", {"start": int(time.time()), "days": float(d.get("days") or 3), "usd": float(d.get("usd") or 10), "plan": plan})
    return sim_summary()


@app.get("/api/wallets")
async def wallets(req: Request):
    need(req)
    out = []
    for w in wallets_cfg(False):
        last = db.q("select t, side, sym, usd from trades where wallet=? order by t desc limit 1", (w["addr"],), one=True)
        out.append({**w, "stats": wallet_stats(w["addr"]), "last": last})
    return out


@app.post("/api/wallets")
async def save_wallets(req: Request):
    """Guarda la lista completa: [{addr, name, origin, note, payers, active}] (el orden es el ranking)."""
    need(req)
    d = await req.json()
    items = d.get("wallets") if isinstance(d, dict) else d
    if not isinstance(items, list):
        raise HTTPException(400, "formato no válido")
    now = int(time.time())
    keep = []
    for i, w in enumerate(items):
        a = (w.get("addr") or "").strip()
        if not (32 <= len(a) <= 44):
            raise HTTPException(400, f"dirección no válida: {a[:12]}")
        keep.append(a)
        old = db.q("select added from wallets where addr=?", (a,), one=True)
        db.x("insert or replace into wallets(addr, name, rank, origin, note, payers, active, added) values(?,?,?,?,?,?,?,?)",
             (a, (w.get("name") or f"Wallet {i + 1}")[:40], i + 1, (w.get("origin") or "")[:40], (w.get("note") or "")[:300],
              json.dumps([p.strip() for p in (w.get("payers") or []) if 32 <= len(p.strip()) <= 44]),
              1 if w.get("active", True) else 0, old["added"] if old else now))
    if keep:
        db.x(f"delete from wallets where addr not in ({','.join('?' * len(keep))})", tuple(keep))
    else:
        db.x("delete from wallets")
    res = await sync_webhook() if db.get("helius_key") else {"ok": True, "msg": "Guardado (falta la clave de Helius para el tiempo real)"}
    return {"ok": True, "webhook": res}


@app.get("/api/settings")
async def get_settings(req: Request):
    need(req)
    return {"helius": bool(db.get("helius_key")), "webhook_id": db.get("webhook_id"), "webhook_ok": db.get("webhook_ok"),
            "public_url": db.get("public_url"), "vapid": vapid()["public"], "daily_hour": db.get("daily_hour", 21),
            "tz": db.get("tz", "Europe/Madrid"), "last_poll": db.get("last_poll"), "last_hook": db.get("last_hook"),
            "last_push": db.get("last_push"), "subs": db.q("select count(*) c from subs", one=True)["c"],
            "last_scan": db.get("last_scan")}


@app.post("/api/settings")
async def set_settings(req: Request):
    need(req)
    d = await req.json()
    if d.get("helius_key"):
        db.put("helius_key", d["helius_key"].strip())
    if d.get("public_url"):
        db.put("public_url", d["public_url"].strip().rstrip("/"))
    if "daily_hour" in d:
        db.put("daily_hour", max(0, min(23, int(d["daily_hour"]))))
    if d.get("tz"):
        ZoneInfo(d["tz"])
        db.put("tz", d["tz"])
    if d.get("new_password"):
        if len(d["new_password"]) < 8:
            raise HTTPException(400, "la contraseña debe tener al menos 8 caracteres")
        db.put("password", hash_pw(d["new_password"]))
    res = await sync_webhook() if (d.get("helius_key") or d.get("public_url")) else None
    return {"ok": True, "webhook": res}


@app.post("/api/push/subscribe")
async def subscribe(req: Request):
    need(req)
    sub = await req.json()
    if not sub.get("endpoint"):
        raise HTTPException(400, "suscripción no válida")
    db.x("insert or replace into subs(endpoint, data, added) values(?,?,?)", (sub["endpoint"], json.dumps(sub), int(time.time())))
    return {"ok": True}


@app.post("/api/push/test")
async def push_test(req: Request):
    need(req)
    n = await push("Prueba de avisos", "Si ves esto, los avisos de las Ganadoras te llegarán al móvil.", url="/")
    return {"ok": n > 0, "sent": n}


@app.get("/api/candidates")
async def candidates(req: Request):
    need(req)
    rows = db.q("select * from candidates where status in ('nueva', 'seguida') order by score desc limit 50")
    for r in rows:
        r["detail"] = json.loads(r.get("detail") or "{}")
    cnt = {r["status"]: r["c"] for r in db.q("select status, count(*) c from candidates group by status")}
    marked = db.q("select mint, min(t) t from trades where side='buy' and hint='posible listado' group by mint")
    listed = sum(1 for m in marked if db.q("select 1 from cex where mint=? and t_seen>=?", (m["mint"], m["t"]), one=True))
    return {"rows": rows, "last_scan": db.get("last_scan"), "counts": cnt, "hint": {"marked": len(marked), "listed": listed},
            "tokens": db.q("select count(*) c from scan_tokens where done=1", one=True)["c"]}


@app.post("/api/candidates/{addr}/{action}")
async def candidate_action(addr: str, action: str, req: Request):
    need(req)
    c = db.q("select * from candidates where addr=?", (addr,), one=True)
    if not c:
        raise HTTPException(404, "no existe")
    if action == "seguir":
        n = db.q("select count(*) c from wallets", one=True)["c"]
        if not db.q("select 1 from wallets where addr=?", (addr,), one=True):
            db.x("insert into wallets(addr, name, rank, origin, note, payers, active, added) values(?,?,?,?,?,?,?,?)",
                 (addr, f"Ganadora {n + 1}", n + 1, c["origin"], f"Buscador: {c['pct_x2']}% llegan a x2, tu método {c['ladder']:+.0f}%", "[]", 1, int(time.time())))
        db.x("update candidates set status='seguida' where addr=?", (addr,))
        if db.get("helius_key"):
            await sync_webhook()
    elif action == "descartar":
        db.x("update candidates set status='descartada' where addr=?", (addr,))
    return {"ok": True}


@app.post("/hook")
async def hook(req: Request):
    if req.headers.get("authorization") != db.get("hook_secret"):
        raise HTTPException(403, "no autorizado")
    try:
        data = await req.json()
    except Exception:
        return Response(status_code=200)
    for tx in data if isinstance(data, list) else [data]:
        S["queue"].put_nowait(tx)
    S["last_hook"] = int(time.time())
    db.put("last_hook", S["last_hook"])
    return Response(status_code=200)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "poll": db.get("last_poll"), "hook": db.get("last_hook")}


@app.get("/sw.js")
async def sw():
    return FileResponse(os.path.join(STATIC, "sw.js"), media_type="application/javascript", headers={"Cache-Control": "no-cache"})


@app.get("/manifest.webmanifest")
async def manifest():
    return FileResponse(os.path.join(STATIC, "manifest.webmanifest"), media_type="application/manifest+json")


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC, "index.html"), headers={"Cache-Control": "no-cache"})


app.mount("/static", StaticFiles(directory=STATIC), name="static")
