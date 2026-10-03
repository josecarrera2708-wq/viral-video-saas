"""Apertura ÚNICA del periodo ciego (2025-07-01 → fin de datos con funding). Bloqueo anti-repetición."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.backtest.data import load_perp
from src.core.nucleo import CoreParams, run_core, reference_bh
from src.core.evaluate_nucleo import daily_ret, sharpe

ROOT = Path(__file__).resolve().parents[2]
LOCK = ROOT / "reports" / "blind_LOCK.json"
if LOCK.exists():
    sys.exit("EL PERIODO CIEGO YA SE ABRIÓ. No se repite: " + LOCK.read_text())
crit = json.loads((ROOT / "config" / "blind_criteria.json").read_text())
START = pd.Timestamp("2025-07-01", tz="UTC")

df, fund = load_perp("4h")                       # perpetuo 4h, recortado al último funding disponible
p = CoreParams()
core = run_core(df, fund, p)
bh = reference_bh(df, fund, p); bhv = reference_bh(df, fund, p, vol_targeted=True)
def cut(eq):
    e = eq[eq.index >= START]; return e / e.iloc[0]
c, b, v = cut(core["equity"]), cut(bh), cut(bhv)
def st(eq):
    r = daily_ret(eq); yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    return {"sharpe": sharpe(r), "ret": float(eq.iloc[-1] - 1), "maxdd": float((1 - eq / eq.cummax()).max()),
            "worst_day": float(r.min()), "days": int(len(r))}
sel = core["expo"].index >= START
yrs = (c.index[-1] - c.index[0]).days / 365.25
res = {"periodo": [str(c.index[0]), str(c.index[-1])], "nucleo": st(c), "bh": st(b), "bh_vt": st(v),
       "exposicion_media": float(core["expo"][sel].mean()), "rotacion_anual": float(core["turn"][sel].sum() / yrs),
       "funding_pagado": float(core["fund"][sel].sum())}
ok_dd = res["nucleo"]["maxdd"] <= crit["dd_bootstrap_p95"]
lo, hi = crit["banda_exposicion"]; ok_e = lo <= res["exposicion_media"] <= hi
lo, hi = crit["banda_rotacion"]; ok_r = lo <= res["rotacion_anual"] <= hi
res["criterios"] = {"dd<=p95_bootstrap": bool(ok_dd), "exposicion_en_banda": bool(ok_e), "rotacion_en_banda": bool(ok_r)}
res["aceptable"] = bool(ok_dd and ok_e and ok_r)
LOCK.write_text(json.dumps({"abierto": str(pd.Timestamp.now(tz="UTC")), "resultado": res}, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
