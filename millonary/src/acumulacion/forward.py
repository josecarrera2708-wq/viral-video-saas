"""Acumulación de BTC en papel (config/acumulacion_prerregistrada.md): `python -m src.acumulacion.forward` → paper_state/acumulacion/resumen.json.

Decisión del dueño (2026-10-03): «reunir el mayor porcentaje de BTC posible». A1 (APLICADA): 100 % BTC al contado, compra única y nunca se
vende. A2 (SOMBRA, para comparar): 50 % BTC / 25 % núcleo v1 / 25 % carry de funding, rebalanceo a fin de mes. 1.000 USDT cada una, compra
al cierre diario del 2026-10-03 (04-oct 00:00 UTC, después del prerregistro). Se mide también en BTC equivalentes (equity / precio).
No es una prueba de ventaja (sin puertas). Sin dinero real.
"""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from src.fondos.data import load, ROOT
from src.fondos import estrategias as E
from src.cartera import gestor as G
from src.cartera.evaluar import core_daily, NUC, CAR

D = ROOT / "paper_state" / "acumulacion"
START = pd.Timestamp("2026-10-03", tz="UTC"); CAP = 1000.0       # etiqueta del día cuyo cierre (04-oct 00:00 UTC) es la compra
FEE = 0.001                                                       # comisión de contado de la compra de A1
H0 = pd.Timestamp("2020-01-01", tz="UTC")                         # contexto histórico (exploratorio, ya visto)
A1, A2 = "A1 Acumulación BTC (100 % BTC)", "A2 50 % BTC / 25 % núcleo / 25 % carry"
W2 = {"BTC": 0.50, NUC: 0.25, CAR: 0.25}
A3 = "A3 Núcleo + carry con ganancias a BTC"
W3 = {NUC: 0.50, CAR: 0.50}
MIN_SWEEP = 10.0                                                  # USDT mínimos de ganancia para convertir (mínimo de Binance: 5)


def returns(d: pd.DataFrame) -> pd.DataFrame:
    """Retornos diarios (etiqueta = día; cierre a las 00:00 UTC del siguiente) de BTC, núcleo v1 y carry con la regla del histórico."""
    return pd.DataFrame({"BTC": d["close"].pct_change(), NUC: core_daily(d).reindex(d.index), CAR: E.carry(d)["ret"]}).fillna(0.0)


def buy_hold(px: pd.Series, t0: pd.Timestamp, cap: float = CAP) -> tuple[float, float, pd.Series]:
    """Compra única al cierre de t0 con comisión FEE; devuelve (BTC comprados, precio, equity al cierre de cada día desde t0)."""
    days = px.index[px.index >= t0]; p0 = float(px[days[0]]); qty = cap * (1 - FEE) / p0
    return qty, p0, qty * px[days]


def rebalanced(R: pd.DataFrame, w: dict, t0: pd.Timestamp, cap: float = CAP) -> tuple[pd.Series, pd.DataFrame]:
    """Mezcla fija en capital: compra al cierre de t0 (coste G.COST por unidad de rotación); los pesos derivan con los precios y vuelven a
    los objetivo al cierre de cada fin de mes con el mismo coste. Devuelve la equity y los pesos al cierre de cada día desde t0."""
    R = R[list(w)]; days = R.index[R.index >= t0]; tgt = np.array([w[c] for c in R.columns], float)
    v = cap * (1 - G.COST) * tgt; me = G.month_end(days); eq, ws = [v.sum()], [tgt.copy()]
    for i in range(1, len(days)):
        v = v * (1 + R.loc[days[i]].to_numpy(float))
        if me[i]:
            tot = v.sum(); tot *= 1 - np.abs(v / tot - tgt).sum() * G.COST; v = tot * tgt
        eq.append(v.sum()); ws.append(v / v.sum())
    return pd.Series(eq, index=days), pd.DataFrame(ws, index=days, columns=R.columns)


def swept(R: pd.DataFrame, px: pd.Series, w: dict, t0: pd.Timestamp, cap: float = CAP) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Núcleo + carry 50/50 que sigue operando con `cap`; al cierre de cada fin de mes, si la cuenta supera `cap` en ≥ MIN_SWEEP, ese
    exceso se convierte en BTC (comisión FEE, una sola compra al mes) y la cuenta vuelve a `cap`. Con pérdidas no se convierte nada.
    El BTC nunca se vende. Devuelve (USDT operando, BTC acumulados, valor total) al cierre de cada día desde t0."""
    R = R[list(w)]; days = R.index[R.index >= t0]; tgt = np.array([w[c] for c in R.columns], float)
    v = cap * (1 - G.COST) * tgt; me = G.month_end(days); btc = 0.0; us, bs = [v.sum()], [0.0]
    for i in range(1, len(days)):
        t = days[i]; v = v * (1 + R.loc[t].to_numpy(float))
        if me[i]:
            tot = v.sum()
            if tot - cap >= MIN_SWEEP:
                btc += (tot - cap) * (1 - FEE) / float(px[t]); tot = cap; v = v / v.sum() * tot
            tot *= 1 - np.abs(v / v.sum() - tgt).sum() * G.COST; v = tot * tgt
        us.append(v.sum()); bs.append(btc)
    u, b = pd.Series(us, index=days), pd.Series(bs, index=days)
    return u, b, u + b * px.reindex(days)


def _card(eq: pd.Series, px: pd.Series, ref_btc: float) -> dict:
    b = eq / px.reindex(eq.index)
    return {"equity": float(eq.iloc[-1]), "retorno_usdt": float(eq.iloc[-1] / CAP - 1), "btc": float(b.iloc[-1]),
            "retorno_btc": float(b.iloc[-1] / ref_btc - 1), "caida_max": float(1 - (eq / eq.cummax()).min()), "dias": int(len(eq) - 1)}


def context(d: pd.DataFrame, R: pd.DataFrame) -> dict:
    """Contexto 2020 → hoy con las mismas reglas (exploratorio: ya visto antes del prerregistro, no certifica nada)."""
    px = d["close"]; _, p0, e1 = buy_hold(px, H0); e2, _ = rebalanced(R, W2, H0); out = {}
    e3 = swept(R, px, W3, H0)[2]
    for k, e in ((A1, e1), (A2, e2), (A3, e3)):
        b = e / px.reindex(e.index) / (CAP / p0); yb = b.groupby(b.index.year).last(); prev = yb.shift(1).fillna(b.iloc[0])
        out[k] = {"x_usdt": float(e.iloc[-1] / CAP), "btc_por_btc_inicial": float(b.iloc[-1]), "caida_max": float(1 - (e / e.cummax()).min()),
                  "btc_por_anio": {str(y): float(yb[y] / prev[y]) for y in yb.index}}
    return out


def run(now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC"); d = load(now); px = d["close"]; R = returns(d)
    o = {"generado": str(now), "inicio": "cierre diario del 2026-10-03 (04-oct 00:00 UTC)", "ultimo_dia_cerrado": str(d.index[-1].date()),
         "precio_btc": float(px.iloc[-1]), "contexto_2020_hoy": context(d, R),
         "nota": "Papel. 1.000 USDT cada una. A1 (hucha de BTC) y A3 (núcleo + carry que pasan sus ganancias a BTC cada mes) son las aplicadas; A2 es sombra para comparar. Sin dinero real."}
    if d.index[-1] < START:
        return o | {"estado": "pendiente: compra en papel al cierre diario del 2026-10-03 (04-oct 00:00 UTC)", "carteras": {}}
    qty, p0, e1 = buy_hold(px, START); e2, w = rebalanced(R, W2, START); ref = CAP / p0
    u3, b3, e3 = swept(R, px, W3, START)
    hist = pd.DataFrame({"A1": e1, "A2": e2, "A3": e3, "precio": px.reindex(e1.index)})
    return o | {"estado": "activa", "precio_entrada": p0, "btc_de_referencia": ref,
                "carteras": {A1: _card(e1, px, ref) | {"papel": "APLICADA", "btc_comprados": qty},
                             A2: _card(e2, px, ref) | {"papel": "SOMBRA", "pesos_ahora": {k: round(float(v), 4) for k, v in w.iloc[-1].items()}},
                             A3: _card(e3, px, ref) | {"papel": "APLICADA", "usdt_operando": float(u3.iloc[-1]), "btc_acumulados": float(b3.iloc[-1]),
                                                       "conversiones": int((b3.diff() > 0).sum())}},
                "hist": [[str(t.date()), round(float(r.A1), 2), round(float(r.A2), 2), round(float(r.A3), 2), round(float(r.precio), 2)] for t, r in hist.iterrows()]}


def main(now: pd.Timestamp | None = None) -> dict:
    D.mkdir(parents=True, exist_ok=True); o = run(now)
    (D / "resumen.json").write_text(json.dumps(o, indent=1, default=str, ensure_ascii=False)); return o


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in main().items() if k != "hist"}, indent=1, ensure_ascii=False))
