"""Trader en papel del núcleo Millonary. Mismo código de señales que el backtest (core.nucleo).

Orden en cada cierre de vela de 4h (T):
  0) si el sistema está PARADO o hay KILL: se aplana con el último precio válido aunque los datos no
     sean fiables (la emergencia va antes que la validación);
  1) valida datos (si falla: NO se opera, se conserva la posición, se avisa);
  2) contabiliza el funding realmente publicado desde el último evento cobrado (no se pierde si llega tarde) y, si
     antes se cobró una tasa SINTÉTICA (mes aún no publicado en Binance Vision), apunta la diferencia con la real
     en cuanto se publica, con las mismas unidades y precio de entonces (libro funding_ledger);
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


def reconcile_funding(st: Store, funding: pd.DataFrame, now) -> float:
    """Funding ya cobrado con una tasa NO definitiva (0,01 % o estimación por el índice de prima): cuando la fuente trae una tasa
    mejor (la real publicada o una estimación con datos completos) se apunta la diferencia con las unidades y el precio de entonces.
    Devuelve el ajuste a restar de la caja (positivo = coste adicional). Nunca empeora una estimación con el 0,01 % de reserva."""
    pend = st.synthetic_funding()
    if not pend or not len(funding):
        return 0.0
    syn = funding["synthetic"].astype(bool).to_numpy() if "synthetic" in funding else np.zeros(len(funding), bool)
    est = funding["estimado"].astype(bool).to_numpy() if "estimado" in funding else np.zeros(len(funding), bool)
    good = ~syn | est
    rates = {str(t): (float(r), bool(sy)) for t, r, sy, g in zip(funding["time"], funding["funding_rate"], syn, good) if g}
    adj = 0.0
    for t, rate, units, price in pend:
        if t in rates and (abs(rates[t][0] - rate) > 1e-12 or not rates[t][1]):
            adj += units * price * (rates[t][0] - rate)
            st.add_funding(t, rates[t][0], units, price, units * price * rates[t][0], rates[t][1])
    if abs(adj) > 0:
        st.log(str(now), "INFO", f"AJUSTE_FUNDING {adj:+.6f} USDT: tasa provisional sustituida por una mejor (real o estimada)")
    return adj


class PaperTrader:
    def __init__(self, cfg: LiveConfig, store: Store, kill_file=None):
        self.cfg, self.st = cfg, store
        self.risk = RiskLayer(cfg.risk, kill_file or (cfg.data_dir / "KILL"))
        if self.st.get("cash") is None:
            self.st.set("cash", cfg.capital); self.st.set("units", 0.0)
            self.st.set("peak", cfg.capital); self.st.set("halted", False)
        if self.st.rows("equity") and not self.st.rows("funding_ledger"):
            self._backfill_ledger()

    # ------------------------------------------------------------------ utilidades
    def equity(self, price: float) -> float:
        return self.st.get("cash") + self.st.get("units") * price

    def _round_units(self, u: float) -> float:
        lot = self.cfg.lot_step
        return math.floor(u / lot + 1e-9) * lot

    def _backfill_ledger(self):
        """Cuentas anteriores al libro de funding: reconstruye cada cobro de las marcas de 8 h (unidades antes de la orden
        de esa vela = las de la vela anterior) y lo deja pendiente de cotejar con la tasa real publicada."""
        prev_units = 0.0
        for r in self.st.rows("equity"):
            t = pd.Timestamp(r["bar"])
            if r["funding"] and prev_units and t.hour % 8 == 0 and t.minute == 0 and r["price"] > 0:
                self.st.add_funding(t, r["funding"] / (prev_units * r["price"]), prev_units, r["price"], r["funding"], True)
            prev_units = r["units"]

    def _reconcile_funding(self, funding: pd.DataFrame, now) -> float:
        return reconcile_funding(self.st, funding, now)

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
            fpay = self._reconcile_funding(funding, now)
            if len(funding):
                ev = funding[(funding["time"] > since) & (funding["time"] <= t_close)]
                if len(ev):
                    fpay += float((units * close * ev["funding_rate"]).sum())    # los largos pagan si es positivo
                    st.set("last_funding_event", str(ev["time"].max()))
                    if units:
                        syn = ev["synthetic"].astype(bool) if "synthetic" in ev else pd.Series(False, index=ev.index)
                        for t_ev, rate, s_ in zip(ev["time"], ev["funding_rate"], syn):
                            st.add_funding(t_ev, rate, units, close, units * close * float(rate), s_)
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
