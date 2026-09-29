"""Mesa de opciones BTC (Deribit, datos públicos): volatilidad implícita vs realizada, sesgo 25Δ y coste de un put 10 % OTM.

Solo INFORMA (modo sombra): no se opera con opciones. Si no hay conexión el departamento lo dice y no inventa nada.
"""
from __future__ import annotations
import re
import numpy as np
import pandas as pd
import requests
from scipy.stats import norm
from .base import Context, Report, OK, AVISO

API = "https://www.deribit.com/api/v2/public"
_MON = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def _expiry(name: str) -> pd.Timestamp:
    d, m, y = re.match(r"BTC-(\d+)([A-Z]{3})(\d+)-", name).groups()
    return pd.Timestamp(year=2000 + int(y), month=_MON[m], day=int(d), hour=8, tz="UTC")


def _bs_delta(S, K, T, iv, put: bool) -> float:
    d1 = (np.log(S / K) + 0.5 * iv ** 2 * T) / (iv * np.sqrt(T))
    return float(norm.cdf(d1) - 1 if put else norm.cdf(d1))


def analyze_chain(book: list, now: pd.Timestamp, target_days: float = 30.0) -> dict | None:
    """book: lista de resúmenes de Deribit (instrument_name, mark_iv en %, mark_price en BTC, underlying_price)."""
    rows = []
    for b in book:
        try:
            n = b["instrument_name"]; e = _expiry(n); K = float(n.split("-")[2]); put = n.endswith("-P")
            rows.append((e, K, put, b["mark_iv"] / 100.0, b["mark_price"], b["underlying_price"]))
        except Exception:                                            # noqa: BLE001
            continue
    if not rows: return None
    df = pd.DataFrame(rows, columns=["exp", "K", "put", "iv", "px", "S"])
    df["days"] = (df["exp"] - now).dt.total_seconds() / 86400; df = df[df["days"] > 3]
    if df.empty: return None
    exp = df.loc[(df["days"] - target_days).abs().idxmin(), "exp"]; d = df[df["exp"] == exp]; S = float(d["S"].iloc[0]); T = float(d["days"].iloc[0]) / 365
    d = d.assign(delta=[_bs_delta(S, r.K, T, r.iv, r.put) for r in d.itertuples()])
    p25 = d[d["put"]].iloc[(d[d["put"]]["delta"] + 0.25).abs().argsort()[:1]]; c25 = d[~d["put"]].iloc[(d[~d["put"]]["delta"] - 0.25).abs().argsort()[:1]]
    atm = d.iloc[(d["K"] - S).abs().argsort()[:1]]; otm = d[d["put"]].iloc[(d[d["put"]]["K"] - 0.9 * S).abs().argsort()[:1]]
    return {"dias_vencimiento": float(d["days"].iloc[0]), "iv_atm": float(atm["iv"].iloc[0]), "sesgo_25d": float(p25["iv"].iloc[0] - c25["iv"].iloc[0]),
            "put10_coste_pct": float(otm["px"].iloc[0] * otm["S"].iloc[0] / S), "put10_strike": float(otm["K"].iloc[0])}


def fetch_book() -> list:
    return requests.get(f"{API}/get_book_summary_by_currency", params={"currency": "BTC", "kind": "option"}, timeout=30).json()["result"]


def opciones(ctx: Context, book: list | None = None) -> Report:
    try:
        book = book if book is not None else fetch_book()
        ch = analyze_chain(book, ctx.now)
    except Exception as e:                                           # noqa: BLE001
        return Report("Mesa de opciones", "Sin conexión con Deribit: sin datos (no se inventa nada)", OK, notes=[f"{type(e).__name__}"])
    if ch is None:
        return Report("Mesa de opciones", "Cadena de opciones no disponible", OK)
    r = ctx.bars["close"].pct_change().dropna(); rv = float(r.iloc[-180:].std() * np.sqrt(6 * 365.25))   # 30 días de velas 4h
    prima = ch["iv_atm"] - rv
    notes = [f"Vencimiento a {ch['dias_vencimiento']:.1f} días: volatilidad implícita ATM {ch['iv_atm']:.1%} · realizada 30 d {rv:.1%} · prima {100*prima:+.1f} pts.",
             f"Sesgo 25Δ (puts − calls): {100*ch['sesgo_25d']:+.1f} pts. Put 10 % por debajo (K≈{ch['put10_strike']:,.0f}): cuesta {ch['put10_coste_pct']:.2%} del nocional.",
             ("Las opciones están caras frente a la volatilidad realizada: cubrirse sale caro." if prima > 0.05 else
              "Las opciones están baratas frente a la volatilidad realizada: proteger sale a buen precio." if prima < -0.02 else "Prima de volatilidad normal."),
             "ESTADO: solo informa. La protección de cola no se activa: no se puede validar con histórico (sin datos históricos de opciones)."]
    return Report("Mesa de opciones", f"IV {ch['iv_atm']:.0%} vs RV {rv:.0%} · put 10 % OTM {ch['put10_coste_pct']:.2%}", OK,
                  {**ch, "rv30": rv, "prima": prima}, notes)
