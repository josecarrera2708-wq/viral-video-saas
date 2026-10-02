"""Carry de funding en papel JUNTO al núcleo (config/carry_papel_prerregistrado.md).

Misma regla que F06 de la mesa de fondos (certificada en histórico), con la contabilidad de una subcuenta real de 1.000 USDT:
  * al cierre diario (00:00 UTC): dentro si la media de las 21 tasas de funding de los últimos 7 días es > 0; fuera si no;
    si está dentro y el nocional se sale de la banda del 20 %, se reajusta a 1×;
  * dentro = largo contado + corto perpetuo con la MISMA cantidad de BTC (lote 0,001), neutral al precio;
  * cada 4 h: liquidación del perpetuo a precio de cierre y equity marcada; funding en cada marca de 8 h (el corto cobra si es > 0),
    con la tasa estimada por el índice de prima mientras Binance no publica el mes y la corrección a la real después.
La cuenta oficial del núcleo NO se toca: es otra subcuenta y otro estado (paper_state/carry/state.db).

  python -m src.live.carry      # idempotente; lo llaman la rutina diaria y la horaria
"""
from __future__ import annotations
import json, math, sys
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.live.store import Store
from src.live.trader import reconcile_funding

ROOT = Path(__file__).resolve().parents[2]
H4 = pd.Timedelta("4h")


@dataclass(frozen=True)
class CarryConfig:
    capital: float = 1000.0
    lot: float = 0.001
    spot_fee: float = 0.0010
    perp_fee: float = 0.0005
    slip: float = 0.0002
    band: float = 0.20
    window_events: int = 21          # 7 días × 3 marcas


class CarryTrader:
    def __init__(self, cfg: CarryConfig, store: Store):
        self.cfg, self.st = cfg, store
        if self.st.get("cash") is None:
            for k, v in (("cash", cfg.capital), ("spot", 0.0), ("perp", 0.0), ("ref", 0.0)):
                self.st.set(k, v)

    def equity(self, S: float, F: float) -> float:
        g = self.st.get
        return g("cash") + g("spot") * S + g("perp") * (F - g("ref"))

    def step(self, spot: pd.DataFrame, perp: pd.DataFrame, funding: pd.DataFrame, now: pd.Timestamp) -> dict:
        cfg, st = self.cfg, self.st
        bar = spot.index[-1]
        if st.get("last_bar") is not None and pd.Timestamp(st.get("last_bar")) >= bar:
            return {"status": "ya_procesada", "bar": str(bar)}
        if bar not in perp.index or not (np.isfinite(spot["close"].iloc[-1]) and np.isfinite(perp.loc[bar, "close"])):
            st.log(str(now), "ERROR", f"datos incompletos en {bar}: contado y perpetuo deben tener la misma vela")
            return {"status": "datos_no_fiables", "bar": str(bar)}
        if bar + H4 > now:
            return {"status": "vela_abierta", "bar": str(bar)}
        S, F = float(spot["close"].iloc[-1]), float(perp.loc[bar, "close"]); t_close = bar + H4
        st.begin()
        try:
            cash, q_s, q_p, ref = st.get("cash"), st.get("spot"), st.get("perp"), st.get("ref") or F
            cash += q_p * (F - ref); ref = F                                         # liquidación del perpetuo a precio de cierre
            fpay = reconcile_funding(st, funding, now)
            last_f = st.get("last_funding_event"); since = pd.Timestamp(last_f) if last_f else t_close - 3 * H4
            if len(funding):
                ev = funding[(funding["time"] > since) & (funding["time"] <= t_close)]
                if len(ev):
                    fpay += float((q_p * F * ev["funding_rate"]).sum())             # corto (q_p < 0) cobra con tasa > 0
                    st.set("last_funding_event", str(ev["time"].max()))
                    if q_p:
                        syn = ev["synthetic"].astype(bool) if "synthetic" in ev else pd.Series(False, index=ev.index)
                        for t_ev, rate, s_ in zip(ev["time"], ev["funding_rate"], syn):
                            st.add_funding(t_ev, rate, q_p, F, q_p * F * float(rate), s_)
            cash -= fpay
            eq = cash + q_s * S
            want = None; trade = []; flags = []
            if t_close.hour == 0:                                                    # decisión diaria al cierre UTC
                w = funding[(funding["time"] > t_close - pd.Timedelta(days=7)) & (funding["time"] <= t_close)] if len(funding) else funding
                want = len(w) >= cfg.window_events and float(w["funding_rate"].mean()) > 0
                if len(w) and "synthetic" in w and bool(w["synthetic"].any()):
                    flags.append(f"decision_con_{int(w['synthetic'].sum())}_tasas_no_definitivas")
                target = math.floor(eq / S / cfg.lot + 1e-9) * cfg.lot if want else 0.0
                expo = q_s * S / eq if eq > 0 else 0.0
                need = (want and q_s == 0) or (not want and q_s > 0) or (want and q_s > 0 and abs(expo - 1) > cfg.band)
                dq = target - q_s if need else 0.0
                if abs(dq) > 1e-12:
                    ps = S * (1 + np.sign(dq) * cfg.slip); pp = F * (1 - np.sign(dq) * cfg.slip)        # contado compra / perpetuo vende
                    fs, fp = abs(dq) * ps * cfg.spot_fee, abs(dq) * pp * cfg.perp_fee
                    cash -= dq * ps + fs                                                 # contado
                    cash += (-dq) * (ref - pp) - fp                                      # perpetuo: −dq al precio pp (deslizamiento contra el cierre)
                    q_s += dq; q_p -= dq
                    why = "entra" if q_s > 0 and q_s == dq else ("sale" if q_s == 0 else "banda 20 %")
                    trade = [dict(bar=str(t_close), side=("COMPRA" if dq > 0 else "VENTA") + " CONTADO", qty=dq, price=ps, fee=fs, reason=why, expo_before=expo, expo_after=0.0),
                             dict(bar=str(t_close), side=("VENTA" if dq > 0 else "COMPRA") + " PERPETUO", qty=-dq, price=pp, fee=fp, reason=why, expo_before=expo, expo_after=0.0)]
                    eq2 = cash + q_s * S
                    for t in trade:
                        t["expo_after"] = q_s * S / eq2 if eq2 > 0 else 0.0; st.add_trade(**t)
            st.set("cash", cash); st.set("spot", q_s); st.set("perp", q_p); st.set("ref", ref)
            eq_end = cash + q_s * S
            st.add_equity(bar=str(t_close), equity=eq_end, units=q_s, price=S, expo=q_s * S / eq_end if eq_end > 0 else 0.0,
                          signal=float(q_s > 0) if want is None else float(want), target=float(q_s > 0), funding=fpay, flags=",".join(flags))
            st.set("last_bar", str(bar))
            st.commit()
        except Exception:
            st.rollback()
            raise
        return {"status": "ok", "bar": str(bar), "equity": eq_end, "spot": q_s, "perp": q_p, "trade": trade, "funding": fpay}


def process(trader: CarryTrader, spot: pd.DataFrame, perp: pd.DataFrame, funding: pd.DataFrame, now: pd.Timestamp, start: pd.Timestamp) -> list:
    """Todas las velas cerradas pendientes, en orden (como el núcleo). Desde la vela cuyo cierre es posterior a `start`."""
    last = trader.st.get("last_bar"); last = pd.Timestamp(last) if last else None; out = []
    for i, t in enumerate(spot.index):
        if t + H4 > now or (last is not None and t <= last) or t + H4 < start:   # la primera vela es la que cierra en `start` (1.ª decisión)
            continue
        r = trader.step(spot.iloc[: i + 1], perp, funding, t + H4 + pd.Timedelta(seconds=60))
        out.append(r)
        if r["status"] not in ("ok", "ya_procesada"):
            break
    return out


def summary(store: Store, cfg: CarryConfig, start: pd.Timestamp, core_store: Store | None, now: pd.Timestamp, F: float | None = None) -> dict:
    eq = store.rows("equity"); tr = store.rows("trades"); led = store.rows("funding_ledger")
    e = eq[-1]["equity"] if eq else cfg.capital
    s = pd.Series([r["equity"] for r in eq], dtype=float)
    out = {"generado": str(now), "inicio": str(start), "ultima_vela": store.get("last_bar"), "equity": e, "retorno": e / cfg.capital - 1,
           "caida_max": float((1 - s / s.cummax()).max()) if len(s) else 0.0, "contado_btc": store.get("spot"), "perpetuo_btc": store.get("perp"),
           "nocional_usdt": (eq[-1]["units"] * eq[-1]["price"]) if eq else 0.0, "dentro": bool(store.get("spot") or 0),
           "funding_cobrado_usdt": 0.0 - float(sum(r["funding"] for r in eq)) + 0.0, "marcas_funding": len(led),
           "tasas_no_definitivas": int(sum(1 for r in led if r["synthetic"])),
           "ordenes": [{k: r[k] for k in ("bar", "side", "qty", "price", "fee", "reason")} for r in tr][-40:],
           "eventos": store.rows("events")[-10:]}
    if core_store is not None and core_store.rows("equity"):
        ce = core_store.rows("equity")[-1]["equity"]
        out["cartera"] = {"nucleo_usdt": ce, "carry_usdt": e, "total_usdt": ce + e, "capital_inicial_usdt": 1000.0 + cfg.capital,
                          "nota": "Dos subcuentas de 1.000 USDT: el núcleo (prueba oficial, sin tocar) y el carry. El núcleo empezó el 2026-09-29; el carry el 2026-10-03."}
    return out


def main(now: pd.Timestamp | None = None, funding: pd.DataFrame | None = None) -> dict:
    from src.live.vision_feed import VisionFeed, SPOT
    cfgj = json.loads((ROOT / "config" / "carry_start.json").read_text()); start = pd.Timestamp(cfgj["start"])
    d = ROOT / cfgj["data_dir"]; d.mkdir(parents=True, exist_ok=True)
    now = now or pd.Timestamp.now(tz="UTC"); cfg = CarryConfig(capital=cfgj["capital"])
    store = Store(d / "state.db"); tr = CarryTrader(cfg, store)
    n = int((now - start) / H4) + 60
    spot = VisionFeed(base=SPOT).bars(n, now); perp = VisionFeed().bars(n, now)
    if funding is None:
        pend = store.oldest_synthetic_funding()
        since = min([pd.Timestamp(x) for x in (pend, store.get("last_funding_event")) if x] + [start - pd.Timedelta(days=9)])
        funding = VisionFeed().funding(since, now)
    res = process(tr, spot, perp, funding, now, start)
    core = Store(ROOT / "paper_state" / "state.db") if (ROOT / "paper_state" / "state.db").exists() else None
    out = summary(store, cfg, start, core, now)
    out["velas_nuevas"] = sum(r["status"] == "ok" for r in res); out["problemas"] = [r for r in res if r["status"] not in ("ok", "ya_procesada")][:1]
    (d / "resumen.json").write_text(json.dumps(out, indent=1, default=str, ensure_ascii=False))
    return out


if __name__ == "__main__":
    o = main(); print(json.dumps({k: v for k, v in o.items() if k not in ("ordenes", "eventos")}, indent=1, default=str, ensure_ascii=False))
