"""Trader S01 (búsqueda v11, config/busqueda_v11_prerregistrada.md): ORB 60 min de la apertura de Nueva York + volumen relativo,
gestión «promediar una vez» (P3). Papel desde 2026-10-08 00:00 UTC.  python -m src.mesanueva.s01

Datos: velas de 5 min del perpetuo BTCUSDT de Binance Vision (archivos diarios, ≤1 día de retraso; caché local). Funding no incluido
(operaciones ≤4 h). Igual que en el backtest: sim5.simulate con 1.000 USDT y riesgo máximo 0,5 %. Una operación cuenta cuando su ventana
de 4 h ya está entera en los datos; antes queda «pendiente»."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from ..live.vision_feed import VisionFeed
from ..desk15.data import ROOT
from ..busqueda.v11 import s_orb, GESTIONES
from ..busqueda.sim5 import simulate

D = ROOT / "paper_state" / "mesas01"
CACHE = ROOT / "data" / "cache" / "vision5m"
START = pd.Timestamp("2026-10-08T00:00:00Z")
GESTION = "P3 protección: promediar 1 vez"
HORAS = 4.0


def bars5(now: pd.Timestamp) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True); feed = VisionFeed("BTCUSDT", "5m"); frames = []
    d = (START - pd.Timedelta(days=40)).floor("D")
    while d < now.floor("D"):
        p = CACHE / f"{d:%Y-%m-%d}.parquet"
        if p.exists():
            frames.append(pd.read_parquet(p))
        else:
            x = feed._day(d)
            if x is None:
                break                                             # aún no publicado: se para aquí (los días siguientes tampoco estarán)
            x.to_parquet(p); frames.append(x)
        d += pd.Timedelta(days=1)
    b = pd.concat(frames).sort_index(); b = b[~b.index.duplicated()]
    b.index = b.index.astype("datetime64[ns, UTC]")
    return b


def main(now: pd.Timestamp | None = None) -> dict:
    now = now or pd.Timestamp.now(tz="UTC")
    b5 = bars5(now); fin = b5.index[-1] + pd.Timedelta("5min")
    sig = s_orb(b5, 60); t = pd.DatetimeIndex(sig["t"])
    live = (t >= START) & (t + pd.Timedelta(hours=HORAS) <= fin)
    pend = int(((t >= START) & ~live).sum())
    tr = simulate(b5, np.zeros(len(b5)), t[live], sig["d"][live], sig["sd"][live], GESTIONES[GESTION](HORAS))
    D.mkdir(parents=True, exist_ok=True); tr.to_csv(D / "trades.csv", index=False)
    res = {"generado": str(now), "trader": "S01 ORB 60 min Nueva York + promediar una vez", "inicio": str(START), "datos_hasta": str(fin),
           "cerradas": len(tr), "pendientes": pend, "acierto": float((tr["R"] > 0).mean()) if len(tr) else 0.0,
           "R_total": float(tr["R"].sum()), "retorno": float(tr["pnl"].sum() / 1000.0), "protecciones_activadas": int(tr["activada"].sum()),
           "fuente": "Binance Vision, velas de 5 min del perpetuo (≤1 día de retraso)", "nota": "Papel. 1.000 USDT. Sin dinero real."}
    (D / "resumen.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    return res


if __name__ == "__main__":
    print(main())
