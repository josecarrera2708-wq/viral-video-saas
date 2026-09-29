"""Trader en papel del núcleo Millonary. Mismo código de señales que el backtest (core.nucleo).

Orden en cada cierre de vela de 4h (T):
  0) si el sistema está PARADO o hay KILL: se aplana con el último precio válido aunque los datos no
     sean fiables (la emergencia va antes que la validación);
  1) valida datos (si falla: NO se opera, se conserva la posición, se avisa);
  2) contabiliza el funding realmente publicado desde el último evento cobrado (no se pierde si llega tarde);
  3) marca a mercado, actualiza máximos y pérdida del día;
  4) señal y exposición objetivo (código compartido); 5) capa de riesgo; 6) rebalanceo con banda;
  7) registra todo en UNA transacción (BEGIN IMMEDIATE + recomprobación de la vela procesada).
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

    def reset_halt(self, now: pd.Timestamp, price: float | None = None) -> dict:
        """Reanuda tras una parada: reinicia 'parado', máximo histórico y referencia diaria. Queda registrado.
        (El KILL debe haberse retirado antes.)"""
        if self.risk.kill_file.exists():
            raise RuntimeError("Retira primero el archivo KILL")
        eq = self.equity(price) if price else (self.st.get("cash") + 0.0)
        rows = self.st.rows("equity")
        if rows: eq = rows[-1]["equity"]
        self.st.set("halted", False); self.st.set("peak", eq); self.st.set("day_start_equity", eq)
        self.st.log(str(now), "AVISO", f"REINICIO manual tras parada. equity={eq:.2f}; máximo y día reiniciados")
        return {"halted": False, "peak": eq}

    # ------------------------------------------------------------------ paso principal
    def step(self, bars: pd.DataFrame, funding: pd.DataFrame, now: pd.Timestamp) -> dict:
        cfg, st = self.cfg, self.st
        bar = bars.index[-1]
        if st.get("last_bar") is not None and pd.Timestamp(st.get("last_bar")) >= bar:
            return {"status": "ya_procesada", "bar": str(bar)}
        emergency = bool(st.get("halted")) or self.risk.kill_file.exists()
        problems, warns = validate_bars(bars, now, cfg.risk, INTERVAL, cfg.min_history_bars)
        emergency_only = False
        if problems:
            last_px = float(bars["close"].iloc[-1]) if len(bars) else float("nan")
            if emergency and np.isfinite(last_px) and last_px > 0:
                emergency_only = True                 # aplanar con el último precio, sin calcular señal
                warns.append("APLANADO_CON_DATOS_NO_FIABLES: " + "; ".join(problems))
            else:
                st.log(str(now), "ERROR", "datos no fiables, no se opera: " + "; ".join(problems))
                return {"status": "datos_no_fiables", "problems": problems, "bar": str(bar)}
        close = float(bars["close"].iloc[-1]); t_close = bar + INTERVAL
        window = bars.iloc[-cfg.history_bars:]
        new_halt = False
        st.begin()
        try:
            if st.get("last_bar") is not None and pd.Timestamp(st.get("last_bar")) >= bar:   # otro proceso ya la hizo
                st.rollback(); return {"status": "ya_procesada", "bar": str(bar)}
            cash, units = st.get("cash"), st.get("units")
            # 2) funding publicado y aún no cobrado
            last_f = st.get("last_funding_event")
            since = pd.Timestamp(last_f) if last_f else (t_close - 3 * INTERVAL)   # ventana amplia: admite eventos retrasados
            fpay = 0.0
            if len(funding):
                ev = funding[(funding["time"] > since) & (funding["time"] <= t_close)]
                if len(ev):
                    fpay = float((units * close * ev["funding_rate"]).sum())     # los largos pagan si es positivo
                    st.set("last_funding_event", str(ev["time"].max()))
            cash -= fpay
            # 3) marca a mercado y control diario/máximos
            equity = cash + units * close
            day = str(t_close.floor("D"))
            if st.get("day") != day:
                st.set("day", day); st.set("day_start_equity", equity)
            peak = max(st.get("peak"), equity); st.set("peak", peak)
            # 4) señal y objetivo (mismo código que el backtest)
            if emergency_only:
                sig = sig_prev = tgt = 0.0
            else:
                ct = compute_targets(window, cfg.core)
                sig, sig_prev, tgt = float(ct["sig"][-1]), float(ct["sig"][-2]), float(ct["tgt"][-1])
            changed = sig != sig_prev
            # 5) riesgo
            rd = self.risk.apply(tgt, equity, peak, st.get("day_start_equity"), st.get("halted"))
            if rd.halted and not st.get("halted"):
                st.set("halted", True); new_halt = True
                st.log(str(now), "CRITICO", "SISTEMA PARADO: " + ",".join(rd.flags))
            target = rd.target
            # 6) rebalanceo con banda
            expo = units * close / equity if equity > 0 else 0.0
            flags = list(rd.flags) + [w for w in warns if w.startswith(("SALTO", "APLANADO"))]
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
                    reducing = qty < 0 and units > 0
                    small = abs(qty) < cfg.min_qty - 1e-12 or notional < cfg.min_notional
                    if reducing and cfg.reduce_below_min:
                        small = abs(qty) < cfg.min_qty - 1e-12 and not closing_all      # reducir/cerrar: sin nocional mínimo
                    elif closing_all:
                        small = False
                    if small:
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
                "signal": sig, "trade": trade, "flags": flags, "warnings": warns, "new_halt": new_halt}
