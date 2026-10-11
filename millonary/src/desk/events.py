"""Calendario de eventos macro. FOMC: parseado del calendario OFICIAL de la Fed (sin fechas inventadas).
CPI/empleo: el BLS bloquea el acceso automático (403); se cargan desde config/events_extra.csv si el dueño lo aporta.
Los horarios se convierten a UTC con la hora de Nueva York (la declaración del FOMC sale a las 14:00 ET)."""
from __future__ import annotations
import re
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

FOMC_URL = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"
MONTHS = {m: i + 1 for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                          "September", "October", "November", "December"])}
ABBR = {k[:3]: v for k, v in MONTHS.items()}
NY = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parents[2]


def parse_fomc(html: str) -> pd.DataFrame:
    """Devuelve una fila por reunión: día de la decisión (2.º día) a las 14:00 ET, en UTC."""
    rows = []
    for y in sorted(set(re.findall(r"(20\d\d) FOMC Meetings", html))):
        i = html.find(f"{y} FOMC Meetings")
        j = html.find("FOMC Meetings", i + 20)
        seg = re.sub(r"<[^>]+>", " ", html[i: j if j > 0 else i + 20000])
        seg = re.sub(r"\s+", " ", seg)
        for m in re.finditer(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s*-\s*(?:(January|February|March|April|May|June|July|August|September|October|November|December)\s+)?(\d{1,2})(\*)?", seg):
            # solo RANGOS de reunión (día 1 - día 2, a veces cruzando de mes); las fechas sueltas ("Released February 18") son minutas
            mon, day = MONTHS[m.group(3) or m.group(1)], int(m.group(4))
            local = pd.Timestamp(int(y), mon, day, 14, 0, tz=NY)
            rows.append({"time": local.tz_convert("UTC"), "type": "FOMC", "impact": "alto",
                         "nota": "con proyecciones" if m.group(5) else "reunión"})
        for m in re.finditer(r"([A-Z][a-z]{2})/([A-Z][a-z]{2})\s+(\d{1,2})\s*-\s*(\d{1,2})(\*)?", seg):      # cruce de mes: "Oct/Nov 31-1"
            if m.group(2) in ABBR:
                local = pd.Timestamp(int(y), ABBR[m.group(2)], int(m.group(4)), 14, 0, tz=NY)
                rows.append({"time": local.tz_convert("UTC"), "type": "FOMC", "impact": "alto",
                             "nota": "con proyecciones" if m.group(5) else "reunión"})
    return pd.DataFrame(rows).drop_duplicates("time").sort_values("time").reset_index(drop=True)


def load_events(fomc_html: str | None = None) -> pd.DataFrame:
    parts = []
    if fomc_html:
        parts.append(parse_fomc(fomc_html))
    extra = ROOT / "config" / "events_extra.csv"
    if extra.exists():
        e = pd.read_csv(extra, parse_dates=["time"]); e["time"] = pd.to_datetime(e["time"], utc=True)
        parts.append(e)
    return pd.concat(parts).sort_values("time").reset_index(drop=True) if parts else pd.DataFrame(columns=["time", "type", "impact"])


def next_event(events: pd.DataFrame, now: pd.Timestamp):
    f = events[events["time"] > now]
    return None if f.empty else f.iloc[0]


def event_study(bars: pd.DataFrame, events: pd.DataFrame, window_bars: int = 3) -> dict:
    """¿Se mueve BTC más de lo normal en torno a los eventos? Cociente del movimiento absoluto de la vela de 4h
    que contiene el evento (y las siguientes) frente a la mediana de todas las velas. INFORMATIVO: no es una regla."""
    r = bars["close"].pct_change().abs()
    med = float(r.median()); out = {"n_eventos": 0, "cociente_vela_evento": None, "cociente_siguientes": None, "mediana_abs_4h": med}
    v0, v1 = [], []
    for t in events["time"]:
        if t < bars.index[0] or t > bars.index[-1]:
            continue
        i = bars.index.searchsorted(t, side="right") - 1
        if i < 0 or i + window_bars >= len(bars):
            continue
        v0.append(r.iloc[i]); v1.append(r.iloc[i + 1: i + 1 + window_bars].mean())
    if v0:
        out.update(n_eventos=len(v0), cociente_vela_evento=float(np.mean(v0) / med), cociente_siguientes=float(np.mean(v1) / med),
                   p_valor_vela_evento=float(_perm_p(r.dropna().to_numpy(), np.array(v0))))
    return out


def _perm_p(all_vals: np.ndarray, sample: np.ndarray, n=4000, seed=0) -> float:
    """P(media del azar >= media observada) con muestras aleatorias del mismo tamaño."""
    rng = np.random.default_rng(seed); obs = sample.mean()
    m = np.array([rng.choice(all_vals, len(sample), replace=False).mean() for _ in range(n)])
    return float((m >= obs).mean())
