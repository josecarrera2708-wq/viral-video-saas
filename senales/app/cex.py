"""Tokens de Solana que cotizan (o van a cotizar) en exchanges centralizados, por dirección de contrato.

Gate, Bitget, KuCoin y MEXC publican la dirección de contrato de cada moneda, así que no hay que fiarse
del símbolo. Gate y Bitget suelen dar de alta el par antes de abrirlo: eso permite avisar del listado
antes de que empiece a cotizar.
"""
import collections
import re

import httpx

B58 = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
NAMES = {"gate": "Gate", "bitget": "Bitget", "kucoin": "KuCoin", "mexc": "MEXC"}


def _get(c, url, **params):
    try:
        return c.get(url, params=params or None).json()
    except Exception:
        return None


def _put(mints, mint, exch, t):
    """Guarda el inicio de cotización más temprano conocido (0 = se sabe que está, pero no desde cuándo)."""
    old = mints[mint].get(exch)
    mints[mint][exch] = min(old, t) if old and t else (old or t)


def snapshot():
    """{"mints": {mint: {exchange: inicio de la cotización en s (0 si no se sabe)}},
        "sym2mint": {SÍMBOLO: {mints}}, "mexc": {par USDT de MEXC: mint}}.
    Un exchange que no responde no aparece (no se confunde con «sin listados»)."""
    mints = collections.defaultdict(dict)
    sym2mint = collections.defaultdict(set)
    mexc = {}
    with httpx.Client(headers=UA, timeout=30) as c:
        cur, pairs = _get(c, "https://api.gateio.ws/api/v4/spot/currencies"), _get(c, "https://api.gateio.ws/api/v4/spot/currency_pairs")
        if isinstance(cur, list) and isinstance(pairs, list):
            gsol = {}
            for x in cur:
                for ch in x.get("chains") or []:
                    if ch.get("name") == "SOL" and B58.match(ch.get("addr") or ""):
                        gsol[x["currency"]] = ch["addr"]
                        sym2mint[x["currency"].upper()].add(ch["addr"])
            for p in pairs:
                if p.get("base") in gsol and p.get("quote") == "USDT":
                    _put(mints, gsol[p["base"]], "gate", int(p.get("buy_start") or 0))

        coins = (_get(c, "https://api.bitget.com/api/v2/spot/public/coins") or {}).get("data")
        syms = (_get(c, "https://api.bitget.com/api/v2/spot/public/symbols") or {}).get("data")
        if coins and syms:
            bsol = {}
            for x in coins:
                for ch in x.get("chains") or []:
                    if (ch.get("chain") or "").upper() in ("SOL", "SOLANA") and B58.match(ch.get("contractAddress") or ""):
                        bsol[x["coin"]] = ch["contractAddress"]
                        sym2mint[x["coin"].upper()].add(ch["contractAddress"])
            for s in syms:
                if s.get("baseCoin") in bsol and s.get("quoteCoin") == "USDT":
                    _put(mints, bsol[s["baseCoin"]], "bitget", int(s.get("openTime") or 0) // 1000)

        cur = (_get(c, "https://api.kucoin.com/api/v3/currencies") or {}).get("data")
        syms = (_get(c, "https://api.kucoin.com/api/v2/symbols") or {}).get("data")
        if cur and syms:
            ksol = {}
            for x in cur:
                for ch in x.get("chains") or []:
                    if ch.get("chainId") in ("sol", "spl") and B58.match(ch.get("contractAddress") or ""):
                        ksol[x["currency"]] = ch["contractAddress"]
                        sym2mint[x["currency"].upper()].add(ch["contractAddress"])
            for s in syms:
                if s.get("baseCurrency") in ksol and s.get("quoteCurrency") == "USDT":
                    _put(mints, ksol[s["baseCurrency"]], "kucoin", int(s.get("tradingStartTime") or 0) // 1000)

        info = _get(c, "https://api.mexc.com/api/v3/exchangeInfo") or {}
        for s in info.get("symbols") or []:
            ca = s.get("contractAddress") or ""
            if B58.match(ca) and s.get("quoteAsset") == "USDT":
                mexc[s["symbol"]] = ca
                _put(mints, ca, "mexc", 0)
                sym2mint[s["baseAsset"].upper()].add(ca)
    return {"mints": {m: dict(v) for m, v in mints.items()}, "sym2mint": dict(sym2mint), "mexc": mexc}
