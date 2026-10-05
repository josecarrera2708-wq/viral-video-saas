"""Lectura de transacciones de Solana y precios.

Una compra se detecta igual que en el vigilante por horas: el token sube en la wallet y la wallet
(o su cuenta de plataforma, si paga con stablecoin) entrega SOL/USDC a cambio. No hace falta saber
qué DEX se usó.
"""
import asyncio
import time

import httpx

WSOL = "So11111111111111111111111111111111111111112"
STABLES = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",  # USDT
    "USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB",   # USD1
    "CASHx9KJUStyftLFWGvEVf59SGeG9sh5FfcnZMVPCASH",  # CASH
    "2b1kV6DkPAnxd5ixfnxCpjxmKwqjjaYmCZfHsFu24GXo",  # PYUSD
    "2u1tszSeqZ3qBWF3uNGPFc8TzMk2tdiwknnRMWGWjGWH",  # USDG
}
QUOTE = STABLES | {WSOL}
MIN_USD = 10            # por debajo es ruido (comisiones, polvo)
PUBLIC_RPC = "https://api.mainnet-beta.solana.com"
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


def _num(b):
    t = b.get("uiTokenAmount") or {}
    s = t.get("uiAmountString")
    if s not in (None, ""):
        return float(s)
    return float(t.get("uiAmount") or 0)


def parse_tx(tx):
    """Transacción en formato getTransaction (JSON) o webhook "raw" de Helius -> saldos que cambian."""
    if not tx or not tx.get("meta") or not tx.get("transaction"):
        return None
    meta, msg = tx["meta"], tx["transaction"]["message"]
    keys = [k["pubkey"] if isinstance(k, dict) else k for k in msg.get("accountKeys", [])]
    la = meta.get("loadedAddresses") or {}
    keys += list(la.get("writable") or []) + list(la.get("readonly") or [])
    pre, post = meta.get("preBalances") or [], meta.get("postBalances") or []
    sol = {}
    for i, k in enumerate(keys):
        if i < len(pre) and i < len(post) and pre[i] != post[i]:
            sol[k] = (post[i] - pre[i]) / 1e9
    tok = {}
    for b in meta.get("preTokenBalances") or []:
        key = (b.get("owner"), b["mint"])
        tok[key] = tok.get(key, 0) - _num(b)
    for b in meta.get("postTokenBalances") or []:
        key = (b.get("owner"), b["mint"])
        tok[key] = tok.get(key, 0) + _num(b)
    tok = {k: v for k, v in tok.items() if abs(v) > 1e-12}
    sigs = tx["transaction"].get("signatures") or []
    return {"sig": sigs[0] if sigs else "", "t": tx.get("blockTime") or int(time.time()),
            "err": meta.get("err"), "keys": set(keys), "sol": sol, "tok": tok}


def detect(p, wallets, sol_usd, infer_payer=False):
    """wallets: {addr: {"payers": [...]}} -> compras y ventas de esas wallets en la transacción.
    infer_payer: si la wallet no paga ni cobra nada (opera desde una plataforma que paga por ella),
    toma como precio el mayor pago/cobro en SOL o stablecoin de otra cuenta de la transacción."""
    out = []
    if not p or p["err"]:
        return out
    owners_in_tx = {o for (o, _m) in p["tok"]}
    for w, cfg in wallets.items():
        if w not in p["keys"] and w not in owners_in_tx:
            continue
        payers = set(cfg.get("payers") or [])
        sol = p["sol"].get(w, 0) + p["tok"].get((w, WSOL), 0)
        stable = sum(v for (o, m), v in p["tok"].items() if m in STABLES and (o == w or o in payers))
        quote = sol * sol_usd + stable
        toks = {m: v for (o, m), v in p["tok"].items() if o == w and m not in QUOTE}
        if len(toks) != 1:  # varias monedas a la vez: no se puede repartir el precio con seguridad
            continue
        (mint, d), = toks.items()
        if infer_payer and abs(quote) < MIN_USD:
            others = [v * (sol_usd if m == WSOL else 1) for (o, m), v in p["tok"].items() if o != w and m in QUOTE]
            others += [v * sol_usd for k, v in p["sol"].items() if k != w and abs(v) > 0.01]
            if d > 0 and others and min(others) < -MIN_USD:
                quote = min(others)
            elif d < 0 and others and max(others) > MIN_USD:
                quote = max(others)
        if d > 0 and quote < -MIN_USD:
            side = "buy"
        elif d < 0 and quote > MIN_USD:
            side = "sell"
        else:
            continue  # regalo o transferencia, no es compraventa
        usd = abs(quote)
        out.append({"sig": p["sig"], "t": p["t"], "wallet": w, "mint": mint, "side": side,
                    "amount": abs(d), "usd": round(usd, 2), "sol": round(abs(sol), 4),
                    "price": usd / abs(d)})
    return out


class Market:
    """Precios y datos de tokens con caché (Jupiter, sin clave)."""

    def __init__(self, client: httpx.AsyncClient):
        self.c = client
        self.meta = {}
        self._sol = (0.0, 0)

    async def sol_usd(self):
        v, t = self._sol
        if time.time() - t < 60 and v:
            return v
        p = await self.prices([WSOL])
        if p.get(WSOL):
            self._sol = (p[WSOL], time.time())
        return self._sol[0] or 120.0

    async def prices(self, mints):
        out = {}
        mints = list(dict.fromkeys(mints))
        for i in range(0, len(mints), 50):
            part = mints[i:i + 50]
            try:
                r = await self.c.get("https://lite-api.jup.ag/price/v3", params={"ids": ",".join(part)}, headers=UA, timeout=20)
                d = r.json()
                for m in part:
                    v = (d.get(m) or {}).get("usdPrice")
                    if v:
                        out[m] = float(v)
            except Exception:
                pass
        return out

    async def token(self, mint):
        m = self.meta.get(mint)
        if m and time.time() - m["_t"] < 6 * 3600:
            return m
        info = {"sym": mint[:4], "name": "", "supply": 0, "icon": "", "_t": time.time()}
        for i in range(3):
            try:
                r = await self.c.get("https://datapi.jup.ag/v1/assets/search", params={"query": mint}, headers=UA, timeout=20)
                for x in r.json() or []:
                    if x.get("id") == mint:
                        info.update(sym=x.get("symbol") or info["sym"], name=x.get("name") or "",
                                    supply=float(x.get("totalSupply") or x.get("circSupply") or 0),
                                    icon=x.get("icon") or "")
                        break
                break
            except Exception:
                await asyncio.sleep(1 + i)
        self.meta[mint] = info
        return info


async def gt_max(client, mint, since):
    """Precio más alto desde `since` con velas de 15 min de GeckoTerminal (para compras antiguas)."""
    try:
        r = await client.get(f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{mint}/pools",
                             params={"page": 1}, headers=UA, timeout=20)
        pool = ((r.json().get("data") or [{}])[0].get("attributes") or {}).get("address")
        if not pool:
            return None
        await asyncio.sleep(2.2)
        r = await client.get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/minute",
                             params={"aggregate": 15, "limit": 1000, "token": mint, "currency": "usd"}, headers=UA, timeout=20)
        lst = ((r.json().get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
        highs = [c[2] for c in lst if c[0] + 900 > since]
        return max(highs) if highs else None
    except Exception:
        return None


async def rpc(client, url, method, params):
    for i in range(4):
        try:
            r = await client.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=30)
            j = r.json()
            if "error" in j:
                raise RuntimeError(j["error"])
            return j["result"]
        except Exception:
            await asyncio.sleep(1.5 * (i + 1))
    return None


async def get_tx(client, url, sig):
    return await rpc(client, url, "getTransaction", [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}])
