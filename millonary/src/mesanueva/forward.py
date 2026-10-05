"""Mesa nueva (papel), decisión del dueño 2026-10-05: `python -m src.mesanueva.forward`. Prerregistro y regla de selección: config/busqueda_v3_prerregistrada.md.
9 traders en 1 h, 4 h y diario. Velas de Deribit BTC-PERPETUAL construidas desde las de 15 min de las otras mesas (solo velas COMPLETAS; funding = suma).
Se recalcula todo desde el inicio en cada ejecución (idempotente). Entra en la apertura de la vela siguiente a la señal, con el mismo motor y costes."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import norm
from ..backtest.engine import Params, run
from ..intraday.postmortem import detail
from ..desk15 import forward as F
from ..desk15.learner import context15
from ..busqueda import setups as v2
from ..busqueda import v3

D = F.ROOT / "paper_state" / "mesanueva"
START = pd.Timestamp("2026-10-06T00:00:00Z")
IV = {"1h": pd.Timedelta("1h"), "4h": pd.Timedelta("4h"), "1d": pd.Timedelta("1D")}
CTX = {"1h": (800, 500), "4h": (200, 500), "1d": (200, 365)}
# código: (temporalidad, clave de la variante en su búsqueda, módulo). Fijado por la regla prerregistrada (mejor elegible por familia / setup).
TRADERS = {
    "X01 Ruptura 20 velas 4 h (largos)": ("4h", "4h | S1 Ruptura 20 velas | solo_largos | 2ATR | TP2", v2),
    "X02 Retroceso a EMA20 4 h (largos)": ("4h", "4h | S2 Retroceso a EMA20 | solo_largos | estructura | TP3", v2),
    "X03 Barra interior 4 h (largos)": ("4h", "4h | S3 Barra interior | solo_largos | 2ATR | TP2", v2),
    "X04 Envolvente en retroceso 4 h (largos, dejar correr)": ("4h", "4h | S4 Envolvente en retroceso | solo_largos | estructura | dejar_correr", v2),
    "X05 Pin bar en retroceso 4 h": ("4h", "4h | S5 Pin bar en retroceso | ambos | estructura | TP5", v2),
    "X06 Cruce EMA 9/21 4 h (largos)": ("4h", "4h | S6 Cruce EMA 9/21 | solo_largos | 2ATR | TP2", v2),
    "X07 Conjunto de tendencias CTA 4 h": ("4h", "4h | N11 Conjunto de tendencias CTA | ambos", v3),
    "X08 MAX de 20 días (Quantpedia)": ("1d", "1d | N05 MAX de n días (Quantpedia) | n=20", v3),
    "X09 Zona de ruido 1 h (Zarattini, largos)": ("1h", "1h | N01 Zona de ruido (Zarattini) | k=1.5 solo_largos", v3),
}


def resample(bars: pd.DataFrame, f: np.ndarray, tf: str) -> tuple[pd.DataFrame, np.ndarray]:
    rule = {"1h": "1h", "4h": "4h", "1d": "1D"}[tf]; need = {"1h": 4, "4h": 16, "1d": 96}[tf]
    b = bars.copy(); b["f"] = f; g = b.resample(rule, label="left", closed="left")
    o = g.agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "f": "sum"}); o = o[g["close"].count() == need].dropna()
    return o[["open", "high", "low", "close", "volume"]], o["f"].to_numpy()


def main(now: pd.Timestamp | None = None, traders: dict | None = None, D: Path = D, START: pd.Timestamp = START) -> dict:
    """Corre la mesa `traders` ({nombre: (tf, clave de variante, módulo con variants(df, tf))}). Por defecto, la mesa nueva X01-X09."""
    traders = traders or TRADERS; now = now or pd.Timestamp.now(tz="UTC"); D.mkdir(parents=True, exist_ok=True); b15, f15 = F.load_bars(now)
    data = {tf: resample(b15, f15, tf) for tf in IV}; specs = {}; summ, frames = {}, []
    days = max((now - START).total_seconds() / 86400, 1e-9)
    for name, (tf, key, mod) in traders.items():
        bars, f = data[tf]
        if (tf, mod.__name__) not in specs:
            specs[(tf, mod.__name__)] = mod.variants(bars, tf)
        sp = specs[(tf, mod.__name__)][key]; ctx = context15(bars, *CTX[tf]); live = np.asarray(bars.index + IV[tf] >= START); i0 = int(np.argmax(live)) if live.any() else len(bars)
        ent = np.where(live, sp.entry, 0).astype(np.int8); ex = None if sp.exit is None else np.where(live, sp.exit, 0).astype(np.int8)
        r = run(bars["open"], bars["high"], bars["low"], bars["close"], ent, np.nan_to_num(sp.stop, nan=0.0), Params(tp_mult=sp.tp_mult, max_bars=sp.max_bars), exit_sig=ex, funding=f)
        rows = [detail(bars, ctx, name, sp, r, i, sp.tp_mult, sp.max_bars) for i in range(int(r["n_trades"]))]
        t = pd.DataFrame(rows, columns=F.COLS); t["temporalidad"] = tf; t["duracion_min"] = t["barras"] * int(IV[tf].total_seconds() // 60); frames.append(t)
        cl = t[~t["abierta"]] if len(t) else t; R = cl["R"].to_numpy() if len(cl) else np.array([]); m = len(R)
        eq = np.asarray(r["equity"])[i0:]; sd = float(R.std(ddof=1)) if m > 2 else 0.0; mean = float(R.mean()) if m else 0.0
        summ[name] = {"temporalidad": tf, "variante": key, "cerradas": m, "por_dia": m / days, "ganan": int((R > 0).sum()), "pierden": int((R <= 0).sum()), "R_media": mean,
                      "R_total": float(R.sum()) if m else 0.0, "pnl_usdt": float(cl["pnl_usdt"].sum()) if m else 0.0, "equity": float(eq[-1]) if len(eq) else 1000.0,
                      "retorno": float(eq[-1] / 1000 - 1) if len(eq) else 0.0, "caida_max": float((1 - eq / np.maximum.accumulate(eq)).max()) if len(eq) else 0.0,
                      "p_R_positiva": float(norm.cdf(mean / (sd / np.sqrt(m)))) if m > 10 and sd > 0 else None,
                      "salidas": {s: int((cl["salida"] == s).sum()) for s in ("tp", "stop", "time", "signal", "liq")} if m else {},
                      "abierta": (t[t["abierta"]].iloc[-1].drop("lecciones").to_dict() if len(t) and t["abierta"].any() else None),
                      "ultima_vela_cerrada": str(bars.index[-1] + IV[tf])}
    allt = pd.concat(frames, ignore_index=True)
    allt.assign(lecciones=allt["lecciones"].map(lambda x: " | ".join(x))).to_csv(D / "trades.csv", index=False)
    (D / "trades_detalle.json").write_text(json.dumps(allt.sort_values("abre", ascending=False).head(400).to_dict("records"), default=str, ensure_ascii=False, indent=1))
    out = {"generado": str(now), "ultima_vela_cerrada": str(b15.index[-1] + F.M15), "inicio": str(START), "fuente": "Deribit BTC-PERPETUAL (1 h, 4 h y diario desde velas de 15 min cerradas)",
           "precio_actual": float(b15["close"].iloc[-1]), "traders": summ, "trades_totales": int(sum(v["cerradas"] for v in summ.values())),
           "por_dia_total": float(sum(v["por_dia"] for v in summ.values()))}
    (D / "resumen.json").write_text(json.dumps(out, indent=1, default=str)); return out


if __name__ == "__main__":
    o = main(); print({k: v for k, v in o.items() if k != "traders"})
    for k, v in o["traders"].items():
        print(f"{k:58s} {v['temporalidad']} ops {v['cerradas']:3d} R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
