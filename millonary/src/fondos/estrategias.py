"""Mesa de fondos: estrategias célebres con sus parámetros ORIGINALES de la literatura (sin optimizar sobre BTC) + cartera multiestrategia.

Prerregistro: config/fondos_prerregistrada.md. Velas diarias UTC (src/fondos/data.py). Todo es causal: los niveles de las órdenes stop se
conocen al abrir el día (datos hasta t-1); las decisiones de cierre se toman con el cierre de t y se aplican desde t+1.
Dentro de un día no se sabe el orden de máximo y mínimo: siempre se asume el orden PEOR (entrada/añadido antes que el stop).
Costes: perpetuo 5 pb de comisión + 2 pb de deslizamiento por lado; contado 10 pb + 2 pb (solo el carry). Funding: los largos pagan
el funding del día si la posición sigue abierta al cierre (los cortos lo cobran). Todas devuelven retornos diarios de una cuenta de 1,0.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from ..signals.indicators import atr, sma

FEE, SLIP, SPOT_FEE = 0.0005, 0.0002, 0.0010
RISK = 0.005            # riesgo por operación (decisión #9 del proyecto)
MAX_EXPO = 2.0          # tope de exposición efectiva (como el núcleo); el 5× del exchange nunca se usa
TARGET_VOL = 0.25       # volatilidad objetivo anual (como el núcleo)


class Book:
    """Cuenta de una estrategia: BTC con signo (q) y caja; equity marcada al cierre de cada día."""

    def __init__(self, n: int, cm: float):
        self.cash, self.q, self.cm = 1.0, 0.0, cm
        self.eq, self.expo, self.trades = np.ones(n), np.zeros(n), []

    def fill(self, qty: float, level: float) -> float:
        px = level * (1 + np.sign(qty) * SLIP * self.cm)
        self.cash -= qty * px + abs(qty) * px * FEE * self.cm
        self.q += qty
        return px

    def close_day(self, t: int, c: float, f: float):
        self.cash -= self.q * c * f
        e = self.cash + self.q * c
        self.eq[t] = e; self.expo[t] = self.q * c / e if e > 0 else 0.0

    def prev(self, t: int) -> float:
        return self.eq[t - 1] if t > 0 else 1.0


def _out(d: pd.DataFrame, bk: Book, n_ops: int | None = None) -> dict:
    eq = pd.Series(bk.eq, index=d.index)
    tr = pd.DataFrame(bk.trades, columns=["entrada", "salida", "lado", "px_entrada", "px_salida", "unidades", "ret", "R", "motivo"])
    return {"ret": eq.pct_change().fillna(eq.iloc[0] - 1.0), "expo": pd.Series(bk.expo, index=d.index), "nocional": pd.Series(np.abs(bk.expo), index=d.index),
            "trades": tr, "n_ops": int(len(tr) if n_ops is None else n_ops)}


def _arr(d: pd.DataFrame):
    return (d["open"].to_numpy(float), d["high"].to_numpy(float), d["low"].to_numpy(float), d["close"].to_numpy(float), d["f"].to_numpy(float))


# ------------------------------------------------------------------------------------------------------------ tortugas
def turtle(d: pd.DataFrame, entry_n: int = 20, exit_n: int = 10, skip: bool = True, failsafe_n: int = 55, cm: float = 1.0, t0: int = 0) -> dict:
    """Tortugas de Richard Dennis y William Eckhardt (1983; reglas publicadas por Curtis Faith, 2007).
    Entrada stop en la ruptura de `entry_n` días (largos y cortos); N = ATR de Wilder de 20 días; unidad = 0,25 % del capital por N
    (0,5 % de riesgo a 2N: decisión #9); añade 1 unidad cada +½N hasta 4; stop de todas las unidades a 2N de la última;
    salida stop en el canal contrario de `exit_n` días. Sistema 1: se salta la ruptura si la última ruptura (operada o no) fue
    ganadora, salvo que rompa también 55 días (red de seguridad)."""
    O, H, L, C, f = _arr(d); n = len(d); bk = Book(n, cm)
    N = atr(d, 20).to_numpy()
    sh = lambda s, w, fn: getattr(pd.Series(s).shift(1).rolling(w), fn)().to_numpy()
    hiE, loE, hiX, loX = sh(H, entry_n, "max"), sh(L, entry_n, "min"), sh(H, exit_n, "max"), sh(L, exit_n, "min")
    hiF, loF = sh(H, failsafe_n, "max"), sh(L, failsafe_n, "min")
    side = units = 0; last_px = stop = Nent = cash0 = first_px = 0.0; t_in = 0; last_win = False; ghost = None
    for t in range(n):
        ok = t > 0 and np.isfinite(N[t - 1]) and np.isfinite(hiE[t]) and np.isfinite(hiX[t]) and (not skip or np.isfinite(hiF[t]))
        if ok and ghost is not None and t > ghost["t"]:                  # ruptura saltada: se sigue en hipotético para la regla de salto
            g = ghost; lvl = max(g["stop"], loX[t]) if g["side"] > 0 else min(g["stop"], hiX[t])
            if (g["side"] > 0 and L[t] <= lvl) or (g["side"] < 0 and H[t] >= lvl):
                px = min(O[t], lvl) if g["side"] > 0 else max(O[t], lvl)
                last_win = g["side"] * (px - g["px"]) > 0; ghost = None
        if ok and side == 0 and t >= t0:
            lb, sb = H[t] > hiE[t], L[t] < loE[t]
            sig = (1 if hiE[t] - O[t] <= O[t] - loE[t] else -1) if (lb and sb) else (1 if lb else (-1 if sb else 0))
            if sig:
                lvl = hiE[t] if sig > 0 else loE[t]; take = True
                if skip and (ghost is not None or last_win):
                    take = False
                    if ghost is None:
                        gpx = max(O[t], lvl) if sig > 0 else min(O[t], lvl)
                        ghost = {"t": t, "side": sig, "px": gpx, "stop": gpx - sig * 2 * N[t - 1]}
                    if (sig > 0 and H[t] > hiF[t]) or (sig < 0 and L[t] < loF[t]):
                        take = True; lvl = hiF[t] if sig > 0 else loF[t]
                if take:
                    Nent = N[t - 1]; eqp = bk.prev(t); cash0 = bk.cash
                    lv = max(O[t], lvl) if sig > 0 else min(O[t], lvl)
                    qty = min(RISK / 2 * eqp / Nent, MAX_EXPO * eqp / lv)
                    first_px = last_px = bk.fill(sig * qty, lv); side, units, t_in = sig, 1, t
                    stop = last_px - side * 2 * Nent
        if ok and side != 0:
            eqp = bk.prev(t)
            while units < 4:                                                 # añadidos ANTES de comprobar la salida (orden peor)
                lvl = last_px + side * 0.5 * Nent
                if not ((side > 0 and H[t] > lvl) or (side < 0 and L[t] < lvl)):
                    break
                lv = max(O[t], lvl) if side > 0 else min(O[t], lvl)
                qty = min(RISK / 2 * eqp / Nent, max(0.0, MAX_EXPO * eqp / lv - abs(bk.q)))
                if qty <= 0:
                    break
                last_px = bk.fill(side * qty, lv); units += 1; stop = last_px - side * 2 * Nent
            lvl = max(stop, loX[t]) if side > 0 else min(stop, hiX[t])
            if (side > 0 and L[t] <= lvl) or (side < 0 and H[t] >= lvl):
                lv = min(O[t], lvl) if side > 0 else max(O[t], lvl)
                px = bk.fill(-bk.q, lv); pnl = bk.cash - cash0
                motivo = "stop 2N" if (lvl == stop) else f"canal {exit_n} d"
                bk.trades.append((d.index[t_in], d.index[t], "LARGO" if side > 0 else "CORTO", first_px, px, units, pnl / bk.prev(t_in),
                                  pnl / (RISK * bk.prev(t_in)), motivo))
                last_win = side * (px - first_px) > 0; side = units = 0
        bk.close_day(t, C[t], f[t])
    return _out(d, bk)


# ------------------------------------------------------------------------------------------------------------ Larry Williams
def williams(d: pd.DataFrame, k: float = 0.5, cm: float = 1.0, t0: int = 0) -> dict:
    """Ruptura de volatilidad de Larry Williams (Long-Term Secrets to Short-Term Trading, 1999; Robbins Cup 1987): compra stop en
    apertura + 0,5 × rango de ayer; sale en la apertura siguiente (= cierre del día en un mercado 24/7). Solo largos, 1× el capital."""
    O, H, L, C, f = _arr(d); n = len(d); bk = Book(n, cm)
    for t in range(n):
        trig = O[t] + k * (H[t - 1] - L[t - 1]) if t > 0 else np.inf
        if t >= t0 and H[t] > trig > 0:
            eqp = bk.prev(t); cash0 = bk.cash; qty = eqp / trig
            pin = bk.fill(qty, max(O[t], trig)); bk.cash -= qty * C[t] * f[t]; pout = bk.fill(-qty, C[t]); pnl = bk.cash - cash0
            bk.trades.append((d.index[t], d.index[t], "LARGO", pin, pout, 1, pnl / eqp, np.nan, "cierre del día"))
        bk.close_day(t, C[t], f[t])
    return _out(d, bk)


# ------------------------------------------------------------------------------------------------------------ Raschke
def turtle_soup(d: pd.DataFrame, n_lb: int = 20, gap: int = 3, hold: int = 3, cm: float = 1.0, t0: int = 0) -> dict:
    """«Turtle Soup Plus One» de Linda Bradford Raschke y Larry Connors (Street Smarts, 1995): el día t marca un nuevo mínimo de 20 días
    y CIERRA en o bajo el mínimo anterior (hecho hace ≥ 3 días); el día t+1 compra stop en ese mínimo anterior (falsa ruptura).
    Stop un tic bajo el mínimo del día t; salida al cierre del 3.er día. Espejo para cortos. Riesgo 0,5 %."""
    O, H, L, C, f = _arr(d); n = len(d); bk = Book(n, cm)
    side = 0; stop = cash0 = pin = 0.0; t_in = 0; risk = 0.0
    for t in range(n):
        if side != 0:
            if (side > 0 and L[t] <= stop) or (side < 0 and H[t] >= stop):
                px = bk.fill(-bk.q, min(O[t], stop) if side > 0 else max(O[t], stop)); motivo = "stop"
            elif t - t_in + 1 >= hold:
                px = bk.fill(-bk.q, C[t]); motivo = f"tiempo ({hold} d)"
            else:
                px = None
            if px is not None:
                pnl = bk.cash - cash0
                bk.trades.append((d.index[t_in], d.index[t], "LARGO" if side > 0 else "CORTO", pin, px, 1, pnl / risk * RISK, pnl / risk, motivo)); side = 0
        elif t >= max(t0, n_lb + 1):
            s = t - 1; w = slice(s - n_lb, s)                                      # día de preparación s = t-1, ventana previa de 20 días
            jl = s - n_lb + int(np.argmin(L[w])); jh = s - n_lb + int(np.argmax(H[w]))
            lo, hi = L[jl], H[jh]
            sig = 0
            if L[s] < lo and C[s] <= lo and s - jl >= gap and H[t] > lo:
                sig, lvl, stp = 1, lo, L[s] * (1 - 1e-4)
            elif H[s] > hi and C[s] >= hi and s - jh >= gap and L[t] < hi:
                sig, lvl, stp = -1, hi, H[s] * (1 + 1e-4)
            if sig:
                eqp = bk.prev(t); lv = max(O[t], lvl) if sig > 0 else min(O[t], lvl); dist = abs(lv - stp) + lv * 2 * (FEE + SLIP)
                qty = min(RISK * eqp / dist, MAX_EXPO * eqp / lv); cash0 = bk.cash; risk = RISK * eqp
                pin = bk.fill(sig * qty, lv); side, stop, t_in = sig, stp, t
                if (sig > 0 and L[t] <= stop) or (sig < 0 and H[t] >= stop):       # orden peor: entra y luego toca el stop el mismo día
                    px = bk.fill(-bk.q, stop); pnl = bk.cash - cash0
                    bk.trades.append((d.index[t], d.index[t], "LARGO" if sig > 0 else "CORTO", pin, px, 1, pnl / eqp, pnl / risk, "stop (mismo día)")); side = 0
        bk.close_day(t, C[t], f[t])
    return _out(d, bk)


# ------------------------------------------------------------------------------------------------------------ Crabel
def nr7(d: pd.DataFrame, cm: float = 1.0, t0: int = 0) -> dict:
    """NR7 de Toby Crabel (Day Trading with Short Term Price Patterns and Opening Range Breakout, 1990): tras el día de rango más
    estrecho de 7, órdenes stop OCO en su máximo (largo) y su mínimo (corto); stop en el extremo contrario; salida al cierre del día.
    Si el día toca ambos extremos se asume lo peor (entra y sale por el stop). Riesgo 0,5 %."""
    O, H, L, C, f = _arr(d); n = len(d); bk = Book(n, cm); rng = H - L
    for t in range(n):
        s = t - 1
        if t >= max(t0, 8) and rng[s] > 0 and rng[s] < rng[s - 6:s].min():
            up, dn = H[t] > H[s], L[t] < L[s]
            if up or dn:
                sig = (1 if H[s] - O[t] <= O[t] - L[s] else -1) if (up and dn) else (1 if up else -1)
                lvl, stp = (H[s], L[s]) if sig > 0 else (L[s], H[s])
                eqp = bk.prev(t); lv = max(O[t], lvl) if sig > 0 else min(O[t], lvl); dist = abs(lv - stp) + lv * 2 * (FEE + SLIP)
                qty = min(RISK * eqp / dist, MAX_EXPO * eqp / lv); cash0 = bk.cash
                pin = bk.fill(sig * qty, lv)
                if up and dn:
                    px = bk.fill(-bk.q, stp); motivo = "stop (mismo día)"
                else:
                    bk.cash -= bk.q * C[t] * f[t]; px = bk.fill(-bk.q, C[t]); motivo = "cierre del día"
                pnl = bk.cash - cash0
                bk.trades.append((d.index[t], d.index[t], "LARGO" if sig > 0 else "CORTO", pin, px, 1, pnl / eqp, pnl / (RISK * eqp), motivo))
        bk.close_day(t, C[t], 0.0)
    return _out(d, bk)


# ------------------------------------------------------------------------------------------------------------ exposición continua
def _sim_expo(d: pd.DataFrame, target: np.ndarray, rebal: np.ndarray, cm: float, t0: int = 0) -> dict:
    """target[t] y rebal[t] se deciden al cierre de t y se aplican desde el día t+1. Entre reajustes las unidades son constantes."""
    C = d["close"].to_numpy(float); f = d["f"].to_numpy(float); n = len(d)
    r = np.r_[0.0, C[1:] / C[:-1] - 1]; eq = np.ones(n); ex = np.zeros(n); e = 0.0; cur = 1.0; ops = 0
    target = np.where(np.arange(n) >= t0 - 1, np.nan_to_num(target), 0.0)
    for i in range(n):
        if i > 0 and (rebal[i - 1] or (i - 1 == t0 - 1)) and target[i - 1] != e:
            tv = abs(target[i - 1] - e); cur *= 1 - tv * (FEE + SLIP) * cm; e = target[i - 1]; ops += 1
        elif abs(e) > MAX_EXPO:                                            # la deriva nunca deja abrir el día por encima de 2×
            cur *= 1 - (abs(e) - MAX_EXPO) * (FEE + SLIP) * cm; e = np.sign(e) * MAX_EXPO; ops += 1
        g = 1 + e * r[i]; cur *= g - e * f[i]; eq[i] = cur; ex[i] = e
        e = e * (1 + r[i]) / g if g > 0 else 0.0
    eqs = pd.Series(eq, index=d.index)
    return {"ret": eqs.pct_change().fillna(0.0), "expo": pd.Series(ex, index=d.index), "nocional": pd.Series(np.abs(ex), index=d.index),
            "trades": pd.DataFrame(), "n_ops": ops}


def _month_end(d: pd.DataFrame) -> np.ndarray:
    return np.asarray((d.index + pd.Timedelta("1D")).month != d.index.month)


def ewma_vol(d: pd.DataFrame, com: int = 60) -> np.ndarray:
    r = d["close"].pct_change()
    return (r.ewm(com=com, min_periods=60).std() * np.sqrt(365)).to_numpy()


def tsmom(d: pd.DataFrame, cm: float = 1.0, t0: int = 0) -> dict:
    """Momentum de series temporales de Moskowitz, Ooi y Pedersen (JFE 2012; base de los CTA y de AQR): signo del retorno de 12 meses,
    tamaño = volatilidad objetivo / volatilidad ex-ante (EWMA, centro de masa 60 días), reajuste mensual, largo y corto."""
    C = d["close"]; sig = np.sign((C / C.shift(365) - 1).to_numpy()); vol = ewma_vol(d)
    tgt = np.where(np.isfinite(sig) & np.isfinite(vol) & (vol > 0), sig * np.minimum(MAX_EXPO, TARGET_VOL / vol), 0.0)
    return _sim_expo(d, tgt, _month_end(d), cm, t0)


def ptj200(d: pd.DataFrame, cm: float = 1.0, t0: int = 0) -> dict:
    """Regla de la media de 200 días de Paul Tudor Jones («mi métrica para todo es la media de 200 días»; Faber 2007 con 10 meses):
    largo 1× si el cierre está sobre la SMA de 200 días; fuera si está debajo."""
    s = sma(d["close"], 200).to_numpy(); tgt = np.where(np.isfinite(s) & (d["close"].to_numpy() > s), 1.0, 0.0)
    return _sim_expo(d, tgt, np.r_[True, tgt[1:] != tgt[:-1]], cm, t0)


def moreira_muir(d: pd.DataFrame, cm: float = 1.0, t0: int = 0, min_months: int = 12) -> dict:
    """Cartera gestionada por volatilidad de Moreira y Muir (Journal of Finance 2017): peso = c / varianza realizada del mes anterior,
    reajuste mensual, solo largos. c causal = media expansiva de las varianzas mensuales pasadas (el artículo la fija con toda la muestra)."""
    r = d["close"].pct_change().fillna(0.0); me = _month_end(d); m = d.index.year * 12 + d.index.month
    rv = (r ** 2).groupby(m).transform("mean").to_numpy()                     # varianza realizada del mes (al cierre de mes, completa)
    tgt = np.zeros(len(d)); hist = []
    for i in np.where(me)[0]:
        hist.append(rv[i])
        if len(hist) >= min_months and rv[i] > 0:
            tgt[i] = min(MAX_EXPO, np.mean(hist) / rv[i])
    tgt = pd.Series(np.where(me, tgt, np.nan), index=d.index).ffill().fillna(0.0).to_numpy()
    return _sim_expo(d, tgt, me, cm, t0)


# ------------------------------------------------------------------------------------------------------------ carry
def carry(d: pd.DataFrame, cm: float = 1.0, t0: int = 0, win: int = 7, band: float = 0.20) -> dict:
    """Carry del funding / cash-and-carry («Crypto Carry», Schmeling, Schrimpf y Todorov, BIS WP 1087, 2023): largo contado + corto
    perpetuo con la misma cantidad de BTC (neutral al precio), cobrando el funding. Dentro si la media de funding de los últimos 7 días
    es > 0; fuera si no. Nocional 1× (margen de cartera: el contado respalda el corto), reajustado si se sale de una banda del 20 %.
    Coste por cambio: contado 12 pb + perpetuo 7 pb. Exposición direccional 0 (el nocional bruto se informa aparte)."""
    S = d["close"].to_numpy(float); F0 = d["pclose"].to_numpy(float); F = d["pclose"].ffill().to_numpy(float); f = d["f"].to_numpy(float); n = len(d)
    avg = pd.Series(f).rolling(win).mean().to_numpy()
    want = np.where(np.isfinite(avg) & np.isfinite(F0) & (avg > 0) & (np.arange(n) >= t0 - 1), 1, 0)
    eq = np.ones(n); ex = np.zeros(n); q = 0.0; cur = 1.0; ops = 0; trades = []; t_in = 0; e_in = 1.0
    leg = lambda s, p: s * (SPOT_FEE + SLIP) * cm + p * (FEE + SLIP) * cm
    for i in range(1, n):
        if want[i - 1] and q == 0 and np.isfinite(F[i - 1]):
            q = cur / S[i - 1]; cur -= q * leg(S[i - 1], F[i - 1]); ops += 1; t_in = i; e_in = cur
        elif want[i - 1] and q > 0 and abs(q * S[i - 1] / cur - 1) > band:       # nocional fuera de la banda del 20 %: reajuste a 1×
            q2 = cur / S[i - 1]; cur -= abs(q2 - q) * leg(S[i - 1], F[i - 1]); q = q2; ops += 1
        elif not want[i - 1] and q > 0:
            cur -= q * leg(S[i - 1], F[i - 1]); ops += 1
            trades.append((d.index[t_in], d.index[i - 1], "CARRY", S[t_in - 1], S[i - 1], 1, cur / e_in - 1, np.nan, "funding medio 7 d ≤ 0")); q = 0.0
        if q > 0:
            cur += q * (S[i] - S[i - 1]) - q * (F[i] - F[i - 1]) + q * F[i] * f[i]
        eq[i] = cur; ex[i] = q * S[i] / cur if cur > 0 else 0.0
    eqs = pd.Series(eq, index=d.index)
    tr = pd.DataFrame(trades, columns=["entrada", "salida", "lado", "px_entrada", "px_salida", "unidades", "ret", "R", "motivo"])
    return {"ret": eqs.pct_change().fillna(0.0), "expo": pd.Series(0.0, index=d.index), "nocional": pd.Series(2 * ex, index=d.index),
            "trades": tr, "n_ops": ops}


# ------------------------------------------------------------------------------------------------------------ catálogo
ESTRATEGIAS = {
    "F01 Tortugas S1 (Dennis, 20/10)": lambda d, cm=1.0, t0=0: turtle(d, 20, 10, True, cm=cm, t0=t0),
    "F02 Tortugas S2 (Dennis, 55/20)": lambda d, cm=1.0, t0=0: turtle(d, 55, 20, False, cm=cm, t0=t0),
    "F03 Momentum 12 m (AQR/MOP)": tsmom,
    "F04 Media 200 d (Tudor Jones)": ptj200,
    "F05 Ruptura de volatilidad (L. Williams)": williams,
    "F06 Carry de funding (cash-and-carry)": carry,
    "F07 Volatilidad gestionada (Moreira-Muir)": moreira_muir,
    "F08 Turtle Soup +1 (Raschke)": turtle_soup,
    "F09 NR7 (Crabel)": nr7,
}
MULTI = "F10 Cartera multiestrategia (paridad de riesgo)"


def run_all(d: pd.DataFrame, cm: float = 1.0, t0: int = 0) -> dict:
    out = {k: fn(d, cm=cm, t0=t0) for k, fn in ESTRATEGIAS.items()}
    out[MULTI] = multi(out, cm=cm)
    return out


def multi(res: dict, cm: float = 1.0, win: int = 90, min_days: int = 60) -> dict:
    """Paridad de riesgo entre F01–F09 (como un fondo multiestrategia): a cada fin de mes, peso ∝ 1/σ de los últimos 90 días de cada
    estrategia (solo las que ya tienen ≥ 60 días con actividad), suma de pesos = 1; coste del reajuste = Σ|Δpeso|·nocional·7 pb."""
    R = pd.DataFrame({k: v["ret"] for k, v in res.items()}); E = pd.DataFrame({k: v["nocional"] for k, v in res.items()})
    me = _month_end(R); sd = R.rolling(win, min_periods=min_days).std(); act = (R != 0).rolling(win, min_periods=1).sum()
    w = (1 / sd.where((sd > 0) & (act >= min_days))).fillna(0.0)
    w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    W = w.where(pd.Series(me, index=R.index), np.nan).ffill().fillna(0.0).shift(1).fillna(0.0)   # peso decidido al cierre de mes, aplica desde el día siguiente
    dw = W.diff().abs().fillna(W.abs())
    cost = (dw * E.shift(1).fillna(0.0)).sum(axis=1) * (FEE + SLIP) * cm
    ret = (W * R).sum(axis=1) - cost
    return {"ret": ret, "expo": (W * pd.DataFrame({k: v["expo"] for k, v in res.items()})).sum(axis=1), "nocional": (W * E).sum(axis=1), "trades": pd.DataFrame(),
            "n_ops": int((dw.sum(axis=1) > 1e-12).sum()), "pesos": W}
