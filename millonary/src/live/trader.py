"""Trader en papel del núcleo Millonary. Mismo código de señales que el backtest (core.nucleo).

Orden en cada cierre de vela de 4h (T):
  1) valida datos (si falla: NO se opera, se conserva la posición, se avisa);
  2) contabiliza el funding liquidado en (T_anterior, T] sobre la posición mantenida;
  3) marca a mercado, actualiza máximos y pérdida del día;
  4) calcula señal y exposición objetivo (código compartido);
  5) capa de riesgo determinista; 6) rebalanceo con banda; 7) registra todo en una transacción.
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from ..core.nucleo import compute_targets
from .config import LiveConfig
from .risk import RiskLayer, validate_bars
from .store import Store

INTERVAL = pd.Timedelta("4h")


class PaperTrader:
    def __init__(self, cfg: LiveConfig, store: Store, kill_file=None):
        self.cfg, self.st = cfg, store
        self.risk = RiskLayer(cfg.risk, kill_file or (cfg.data_dir / "KILL"))
        if self.st.get("cash") is None:
            self.st.set("cash", cfg.capital); self.st.set("units", 0.0)
            self.st.set("peak", cfg.capital); self.st.set("halted", False)

    # ------------------------------------------------------------------ utilidades
    def equity(self, price: float) -> float:
        return self.st.get("cash") + self.st.get("units") * price

    def _round_units(self, u: float) -> float:
        lot = self.cfg.lot_step
        return math.floor(u / lot + 1e-9) * lot

    # ------------------------------------------------------------------ paso principal
    def step(self, bars: pd.DataFrame, funding: pd.DataFrame, now: pd.Timestamp) -> dict:
        cfg, st = self.cfg, self.st
        bar = bars.index[-1]
        if st.get("last_bar") is not None and pd.Timestamp(st.get("last_bar")) >= bar:
            return {"status": "ya_procesada", "bar": str(bar)}
        problems = validate_bars(bars, now, cfg.risk, INTERVAL)
        if problems:
            st.log(str(now), "ERROR", "datos no fiables, no se opera: " + "; ".join(problems))
            return {"status": "datos_no_fiables", "problems": problems, "bar": str(bar)}
        close = float(bars["close"].iloc[-1]); t_close = bar + INTERVAL
        window = bars.iloc[-cfg.history_bars:]
        st.begin()
        try:
            cash, units = st.get("cash"), st.get("units")
            # 2) funding sobre la posición mantenida durante la vela
            last_f = st.get("last_funding")
            since = pd.Timestamp(last_f) if last_f else (t_close - INTERVAL)
            fpay = 0.0
            if len(funding):
                ev = funding[(funding["time"] > since) & (funding["time"] <= t_close)]
                fpay = float((units * close * ev["funding_rate"]).sum())     # los largos pagan si es positivo
            cash -= fpay
            st.set("last_funding", str(t_close))
            # 3) marca a mercado y control diario/máximos
            equity = cash + units * close
            day = str(t_close.floor("D"))
            if st.get("day") != day:
                st.set("day", day); st.set("day_start_equity", equity)
            peak = max(st.get("peak"), equity); st.set("peak", peak)
            # 4) señal y objetivo (mismo código que el backtest)
            ct = compute_targets(window, cfg.core)
            sig, sig_prev, tgt = float(ct["sig"][-1]), float(ct["sig"][-2]), float(ct["tgt"][-1])
            changed = sig != sig_prev
            # 5) riesgo
            rd = self.risk.apply(tgt, equity, peak, st.get("day_start_equity"), st.get("halted"))
            if rd.halted and not st.get("halted"):
                st.set("halted", True); st.log(str(now), "CRITICO", "SISTEMA PARADO: " + ",".join(rd.flags))
            target = rd.target
            # 6) rebalanceo con banda
            expo = units * close / equity if equity > 0 else 0.0
            flags = list(rd.flags)
            need = changed or (target > 0 and abs(expo - target) > cfg.core.band * target) \
                or (target == 0 and units > 0)
            trade = None
            if need and equity > 0:
                want = self._round_units(target * equity / close) if target > 0 else 0.0
                qty = want - units
                closing_all = want == 0.0
                if closing_all and units <= 0:
                    qty = 0.0
                if abs(qty) > 1e-12:
                    notional = abs(qty) * close
                    if not closing_all and (abs(qty) < cfg.min_qty - 1e-12 or notional < cfg.min_notional):
                        flags.append("OMITIDA_MIN_ORDEN"); qty = 0.0
                if abs(qty) > 1e-12:
                    px = close * (1 + cfg.slippage) if qty > 0 else close * (1 - cfg.slippage)
                    fee = abs(qty) * px * cfg.taker_fee
                    cash -= qty * px + fee; units += qty
                    trade = dict(bar=str(t_close), side="BUY" if qty > 0 else "SELL", qty=qty, price=px, fee=fee,
                                 reason=("RIESGO" if rd.flatten else ("SEÑAL" if changed else "BANDA")),
                                 expo_before=expo, expo_after=units * close / max(cash + units * close, 1e-12))
                    st.add_trade(**trade)
            st.set("cash", cash); st.set("units", units)
            eq_end = cash + units * close
            st.add_equity(bar=str(t_close), equity=eq_end, units=units, price=close,
                          expo=units * close / eq_end if eq_end > 0 else 0.0, signal=sig, target=target,
                          funding=fpay, flags=",".join(flags))
            st.set("last_bar", str(bar))
            st.commit()
        except Exception:
            st.rollback()
            raise
        return {"status": "ok", "bar": str(bar), "equity": eq_end, "units": units, "target": target,
                "signal": sig, "trade": trade, "flags": flags}
