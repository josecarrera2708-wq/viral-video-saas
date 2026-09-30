"""Mesa intradía hacia delante (papel): los 14 traders operan sobre velas de 1 h de Deribit BTC-PERPETUAL.

  python -m src.intraday.forward            # actualiza paper_state/intradia/ (idempotente; se recalcula desde el inicio de la prueba)
Deribit es el único proveedor accesible desde este entorno (Binance/Bybit/Hyperliquid devuelven 403/451). Solo se usan velas CERRADAS.
"""
from __future__ import annotations
import json, sys
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import requests
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.engine import Params, run, REASONS
from src.intraday.setups import all_specs

ROOT = Path(__file__).resolve().parents[2]
API = "https://www.deribit.com/api/v2/public"
H1 = pd.Timedelta("1h")
INSTR = "BTC-PERPETUAL"
WARM_H = 420


def _ms(t: pd.Timestamp) -> int:
    return int(pd.Timestamp(t).tz_convert("UTC").timestamp() * 1000)


def fetch_bars(start: pd.Timestamp, now: pd.Timestamp, get=None) -> pd.DataFrame:
    """Velas de 1 h CERRADAS desde start-WARM_H hasta now. `get(url, params)->dict` inyectable para pruebas."""
    get = get or (lambda u, p: requests.get(u, params=p, timeout=30).json())
    a = pd.Timestamp(start).floor("1h") - pd.Timedelta(hours=WARM_H)
    j = get(f"{API}/get_tradingview_chart_data", {"instrument_name": INSTR, "resolution": "60", "start_timestamp": _ms(a), "end_timestamp": _ms(now)})["result"]
    t = pd.to_datetime(pd.Series(j["ticks"]), unit="ms", utc=True)
    df = pd.DataFrame({"open": j["open"], "high": j["high"], "low": j["low"], "close": j["close"], "volume": j["volume"]}, index=pd.DatetimeIndex(t))
    df = df[~df.index.duplicated()].sort_index()
    return df[df.index + H1 <= pd.Timestamp(now)]                   # solo velas cerradas


def fetch_funding(idx: pd.DatetimeIndex, now: pd.Timestamp, get=None) -> np.ndarray:
    """Funding por vela (tasa horaria de Deribit, `interest_1h`); 0 si el proveedor no responde (se anota en el resumen)."""
    get = get or (lambda u, p: requests.get(u, params=p, timeout=30).json())
    try:
        j = get(f"{API}/get_funding_rate_history", {"instrument_name": INSTR, "start_timestamp": _ms(idx[0]), "end_timestamp": _ms(now)})["result"]
        s = pd.Series({pd.Timestamp(x["timestamp"], unit="ms", tz="UTC").floor("1h"): x["interest_1h"] for x in j})
        # el pago marcado a la hora h cubre la vela que cierra en h
        return s.reindex(idx + H1).fillna(0.0).to_numpy()
    except Exception:                                                # noqa: BLE001
        return np.zeros(len(idx))


def run_all(bars: pd.DataFrame, funding: np.ndarray, start: pd.Timestamp, params: Params = Params(), specs: dict | None = None) -> dict:
    specs = specs if specs is not None else all_specs(bars); closes = bars.index + H1; live = np.asarray(closes >= pd.Timestamp(start)); out = {}
    for k, sp in specs.items():
        ent = np.where(live, sp.entry, 0).astype(np.int8); ex = None if sp.exit is None else np.where(live, sp.exit, 0).astype(np.int8)
        p = replace(params, tp_mult=sp.tp_mult, max_bars=sp.max_bars)
        r = run(bars["open"], bars["high"], bars["low"], bars["close"], ent, np.nan_to_num(sp.stop, nan=0.0), p, exit_sig=ex, funding=funding)
        out[k] = r
    return out


def trades_frame(bars: pd.DataFrame, name: str, r: dict, spec=None, ctx: pd.DataFrame | None = None) -> pd.DataFrame:
    """Una fila por operación con hora, entrada, SL, TP, lote, riesgo, salida, R y análisis post-mortem (si se dan spec y contexto)."""
    from .postmortem import detail
    rows = []
    for i in range(int(r["n_trades"])):
        rows.append(detail(bars, ctx, name, spec, r, i, spec.tp_mult, spec.max_bars))
    cols = ["trader", "abre", "cierra", "lado", "px_entrada", "sl", "tp", "lote_btc", "nocional_usdt", "riesgo_usdt", "stop_pct", "px_salida", "salida", "R", "pnl_usdt",
            "comision_usdt", "funding_usdt", "barras", "max_barras", "mfe_R", "mae_R", "post_stop_R", "tendencia_a_favor", "vol_percentil", "hora_utc", "abierta", "lecciones"]
    return pd.DataFrame(rows, columns=cols)


def summarize_all(bars: pd.DataFrame, res: dict, start: pd.Timestamp, now: pd.Timestamp, specs: dict | None = None) -> tuple[dict, pd.DataFrame]:
    from .postmortem import context
    specs = specs if specs is not None else all_specs(bars); ctx = context(bars)
    days = max((now - pd.Timestamp(start)).total_seconds() / 86400, 1e-9); summ = {}; frames = []
    for k, r in res.items():
        t = trades_frame(bars, k, r, specs[k], ctx); frames.append(t); closed = t[~t["abierta"]] if len(t) else t
        R = closed["R"].to_numpy() if len(closed) else np.array([]); n = len(R); eq = np.asarray(r["equity"]); cap = 1000.0
        live_eq = eq[np.asarray(bars.index + H1 >= pd.Timestamp(start))]
        mean = float(R.mean()) if n else 0.0; sd = float(R.std(ddof=1)) if n > 2 else 0.0
        summ[k] = {"cerradas": n, "por_dia": n / days, "ganan": int((R > 0).sum()), "pierden": int((R <= 0).sum()),
                   "salidas": {s: int((closed["salida"] == s).sum()) for s in ("tp", "stop", "time", "signal", "liq")} if n else {},
                   "R_media": mean, "R_total": float(R.sum()) if n else 0.0, "pnl_usdt": float(closed["pnl_usdt"].sum()) if n else 0.0,
                   "equity": float(live_eq[-1]) if len(live_eq) else cap, "retorno": float(live_eq[-1] / cap - 1) if len(live_eq) else 0.0,
                   "caida_max": float((1 - live_eq / np.maximum.accumulate(live_eq)).max()) if len(live_eq) else 0.0,
                   "p_R_positiva": float(norm.cdf(mean / (sd / np.sqrt(n)))) if n > 10 and sd > 0 else None,
                   "abierta": (t[t["abierta"]].iloc[-1].drop("lecciones").to_dict() if len(t) and t["abierta"].any() else None), "liquidado": bool(r["ruined"])}
    allt = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return summ, allt


def main(now: pd.Timestamp | None = None) -> dict:
    cfg = json.loads((ROOT / "config" / "paper_start.json").read_text()); start = pd.Timestamp(cfg["start"]); now = now or pd.Timestamp.now(tz="UTC")
    d = ROOT / cfg["data_dir"] / "intradia"; d.mkdir(parents=True, exist_ok=True)
    bars = fetch_bars(start, now); f = fetch_funding(bars.index, now)
    if len(bars) < 350:
        return {"error": f"pocas velas ({len(bars)})"}
    specs = all_specs(bars); res = run_all(bars, f, start, specs=specs); summ, allt = summarize_all(bars, res, start, now, specs)
    if len(allt):
        from .postmortem import learning
        allt.assign(lecciones=allt["lecciones"].map(lambda x: " | ".join(x))).to_csv(d / "trades.csv", index=False)
        (d / "trades_detalle.json").write_text(json.dumps(allt.sort_values("abre", ascending=False).to_dict("records"), default=str, ensure_ascii=False, indent=1))
        (d / "aprendizaje.json").write_text(json.dumps(learning(allt.to_dict("records")), ensure_ascii=False, indent=1))
    else:
        (d / "trades.csv").write_text("")
    mej = {}
    lp = ROOT / "reports" / "intradia_mejoras.json"
    if lp.exists():
        from src.intraday.mejora import OPERADORES
        led = json.loads(lp.read_text()); base = all_specs(bars); vs = {k: OPERADORES[led["candidatas"][k]["operador"]](bars, base[led["candidatas"][k]["trader"]]) for k in led["en_sombra"]}
        if vs:
            rv = run_all(bars, f, start, specs=vs); sv, tv = summarize_all(bars, rv, start, now, vs)
            for k, v in sv.items():
                v["R_media_base"] = summ[led["candidatas"][k]["trader"]]["R_media"]; v["cerradas_base"] = summ[led["candidatas"][k]["trader"]]["cerradas"]
                v["etapa"] = "E3 sombra (faltan operaciones)" if v["cerradas"] < 150 else ("E3 candidata" if (v["R_media"] > v["R_media_base"] and (v["p_R_positiva"] or 0) >= 0.90) else "E4 retirada" if v["R_media"] <= 0 else "E3 sombra (sin cumplir)")
            mej = sv
            if len(tv): tv.to_csv(d / "trades_mejoras.csv", index=False)
    out = {"generado": str(now), "ultima_vela_cerrada": str(bars.index[-1] + H1), "inicio": str(start), "fuente": "Deribit BTC-PERPETUAL 1 h (velas cerradas)",
           "funding_disponible": bool(np.any(f != 0)), "precio_actual": float(bars["close"].iloc[-1]), "traders": summ, "trades_totales": int(sum(v["cerradas"] for v in summ.values())),
           "por_dia_total": float(sum(v["por_dia"] for v in summ.values())), "mejoras": mej}
    (d / "resumen.json").write_text(json.dumps(out, indent=1, default=str)); return out


if __name__ == "__main__":
    o = main()
    print({k: v for k, v in o.items() if k not in ("traders", "mejoras")})
    for k, v in o.get("traders", {}).items():
        print(f"{k:38s} ops {v['cerradas']:2d} ({v['por_dia']:.1f}/día) R {v['R_total']:+.2f} ret {v['retorno']:+.2%} abierta {'sí' if v['abierta'] else 'no'}")
