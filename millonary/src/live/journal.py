"""Diario de operaciones: órdenes, LOTES (cada compra, contabilidad FIFO) y POSICIONES completas.

Cada lote y cada posición cerrada queda como GANA o PIERDE, con precio, comisión, funding, duración,
MAE/MFE y contexto. El P&L de todos los lotes (realizado + no realizado) CUADRA con la equity al céntimo:
    equity_final - capital_inicial = suma de P&L de lotes
(comprobación automática = puerta G5 del protocolo).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .store import Store


def _stats(pnl_pct: pd.Series, pnl: pd.Series) -> dict:
    n = len(pnl)
    if n == 0:
        return {"n": 0}
    w = pnl > 0
    gp, gl = pnl[w].sum(), -pnl[~w].sum()
    return {"n": n, "ganan": int(w.sum()), "pierden": int((~w).sum()), "tasa_acierto": float(w.mean()),
            "ganancia_media_pct": float(pnl_pct[w].mean()) if w.any() else 0.0,
            "perdida_media_pct": float(pnl_pct[~w].mean()) if (~w).any() else 0.0,
            "relacion_ganancia_perdida": float(pnl_pct[w].mean() / abs(pnl_pct[~w].mean())) if w.any() and (~w).any() and pnl_pct[~w].mean() != 0 else None,
            "factor_beneficio": float(gp / gl) if gl > 0 else None,
            "esperanza_pct": float(pnl_pct.mean()), "pnl_total": float(pnl.sum())}


def build_journal(store: Store, capital: float) -> dict:
    trades = pd.DataFrame(store.rows("trades")); eq = pd.DataFrame(store.rows("equity"))
    empty = pd.DataFrame()
    if eq.empty:
        return {"orders": empty, "lots": empty, "episodes": empty, "resumen": {"lotes_cerrados": {"n": 0}, "posiciones_cerradas": {"n": 0}},
                "cuadre": {"ok": True, "diferencia": 0.0}}
    lots: list[dict] = []; frags: list[dict] = []
    open_lots: list[dict] = []; lot_id = 0
    by_bar = {b: g for b, g in trades.groupby("bar")} if not trades.empty else {}
    for _, row in eq.iterrows():
        bar = row["bar"]
        # funding pagado durante la vela sobre los lotes abiertos (antes de las órdenes de la vela)
        if row["funding"] != 0 and open_lots:
            tot = sum(l["qty_open"] for l in open_lots)
            for l in open_lots:
                l["funding"] += row["funding"] * l["qty_open"] / tot
        for _, t in by_bar.get(bar, empty).iterrows() if bar in by_bar else []:
            if t["qty"] > 0:                                              # compra: nace un lote
                lot_id += 1
                l = {"lot_id": lot_id, "abre": bar, "qty": t["qty"], "qty_open": t["qty"], "px_entrada": t["price"],
                     "fee_entrada": t["fee"], "funding": 0.0, "realizado": 0.0, "cierra": None, "px_max": t["price"], "px_min": t["price"],
                     "senal_entrada": row["signal"], "motivo": t["reason"]}
                open_lots.append(l); lots.append(l)
            else:                                                          # venta: consume lotes FIFO
                q = -t["qty"]; fee_left, q_left = t["fee"], q
                while q_left > 1e-12 and open_lots:
                    l = open_lots[0]; take = min(l["qty_open"], q_left)
                    fee_buy = l["fee_entrada"] * take / l["qty"]; fee_sell = t["fee"] * take / q
                    pnl = take * (t["price"] - l["px_entrada"]) - fee_buy - fee_sell
                    l["realizado"] += pnl; l["qty_open"] -= take; q_left -= take
                    frags.append({"lot_id": l["lot_id"], "cierra": bar, "qty": take, "px_salida": t["price"], "pnl": pnl})
                    if l["qty_open"] <= 1e-12:
                        l["cierra"] = bar; open_lots.pop(0)
        for l in open_lots:                                               # excursiones (marcas de cierre)
            l["px_max"] = max(l["px_max"], row["price"]); l["px_min"] = min(l["px_min"], row["price"])
    last_px = float(eq["price"].iloc[-1])
    rows = []
    for l in lots:
        unreal = l["qty_open"] * (last_px - l["px_entrada"]) - l["fee_entrada"] * l["qty_open"] / l["qty"]
        pnl = l["realizado"] + unreal + (-l["funding"])                    # funding pagado (positivo) resta
        cost = l["qty"] * l["px_entrada"]
        rows.append({"lote": l["lot_id"], "abre": l["abre"], "cierra": l["cierra"], "estado": "CERRADO" if l["cierra"] else "ABIERTO",
                     "qty": l["qty"], "px_entrada": l["px_entrada"], "pnl_usdt": pnl, "pnl_pct": pnl / cost if cost else 0.0,
                     "resultado": ("GANA" if pnl > 0 else "PIERDE") if l["cierra"] else ("GANA (no realizado)" if pnl > 0 else "PIERDE (no realizado)"),
                     "funding_pagado": l["funding"], "mfe_pct": l["px_max"] / l["px_entrada"] - 1, "mae_pct": l["px_min"] / l["px_entrada"] - 1,
                     "senal_al_entrar": l["senal_entrada"], "motivo": l["motivo"]})
    lots_df = pd.DataFrame(rows)
    # posiciones completas (0 -> >0 -> 0), a partir de las unidades de la equity
    eps = []; cur = None; prev_units = 0.0; prev_eq = capital
    for _, r in eq.iterrows():
        if prev_units <= 1e-12 and r["units"] > 1e-12:
            cur = {"abre": r["bar"], "eq_antes": prev_eq, "senal": r["signal"], "prices": [r["price"]], "lotes": []}
        if cur is not None:
            cur["prices"].append(r["price"])
        if cur is not None and r["units"] <= 1e-12:
            cur.update(cierra=r["bar"], eq_despues=r["equity"], estado="CERRADA"); eps.append(cur); cur = None
        prev_units, prev_eq = r["units"], r["equity"]
    if cur is not None:
        cur.update(cierra=None, eq_despues=float(eq["equity"].iloc[-1]), estado="ABIERTA"); eps.append(cur)
    ep_rows = []
    for k, e in enumerate(eps, 1):
        ls = lots_df[(lots_df["abre"] >= e["abre"]) & ((e["cierra"] is None) | (lots_df["abre"] <= (e["cierra"] or "z")))] if not lots_df.empty else lots_df
        pnl = e["eq_despues"] - e["eq_antes"]; p = np.array(e["prices"])
        entry = float(np.average(ls["px_entrada"], weights=ls["qty"])) if len(ls) else p[0]
        ep_rows.append({"posicion": k, "abre": e["abre"], "cierra": e["cierra"], "estado": e["estado"], "pnl_usdt": pnl,
                        "pnl_pct": pnl / e["eq_antes"], "resultado": ("GANA" if pnl > 0 else "PIERDE") if e["estado"] == "CERRADA" else ("GANA (no realizado)" if pnl > 0 else "PIERDE (no realizado)"),
                        "n_lotes": len(ls), "px_entrada_medio": entry, "mfe_pct": float(p.max() / entry - 1), "mae_pct": float(p.min() / entry - 1),
                        "senal_al_abrir": e["senal"],
                        "duracion_dias": (pd.Timestamp(e["cierra"] or eq["bar"].iloc[-1]) - pd.Timestamp(e["abre"])).total_seconds() / 86400})
    eps_df = pd.DataFrame(ep_rows)
    diff = float(eq["equity"].iloc[-1] - capital - (lots_df["pnl_usdt"].sum() if not lots_df.empty else 0.0))
    cl = lots_df[lots_df["estado"] == "CERRADO"] if not lots_df.empty else lots_df
    ce = eps_df[eps_df["estado"] == "CERRADA"] if not eps_df.empty else eps_df
    resumen = {"lotes_cerrados": _stats(cl["pnl_pct"], cl["pnl_usdt"]) if len(cl) else {"n": 0},
               "posiciones_cerradas": _stats(ce["pnl_pct"], ce["pnl_usdt"]) if len(ce) else {"n": 0},
               "lotes_abiertos": int((lots_df["estado"] == "ABIERTO").sum()) if not lots_df.empty else 0,
               "pnl_no_realizado": float(lots_df.loc[lots_df["estado"] == "ABIERTO", "pnl_usdt"].sum()) if not lots_df.empty else 0.0}
    return {"orders": trades, "lots": lots_df, "episodes": eps_df, "resumen": resumen,
            "cuadre": {"ok": abs(diff) <= 0.01, "diferencia": diff}}


def export_journal(j: dict, out) -> None:
    from pathlib import Path
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    for k, name in (("orders", "diario_ordenes"), ("lots", "diario_lotes"), ("episodes", "diario_posiciones")):
        (j[k] if not j[k].empty else pd.DataFrame()).to_csv(out / f"{name}.csv", index=False)
