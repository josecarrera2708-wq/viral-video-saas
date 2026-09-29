"""Simulador de la incubadora: posición {-1,0,+1} (1× fijo), costes por rotación y funding real (largos pagan, cortos cobran)."""
from __future__ import annotations
import numpy as np
import pandas as pd

COST = 0.0007


def simulate(df: pd.DataFrame, state: np.ndarray, funding: np.ndarray, cost: float = COST) -> dict:
    """state[i] = estado deseado al cierre de la vela i -> posición durante la vela i+1."""
    n = len(df); r = df["close"].pct_change().fillna(0.0).to_numpy()
    pos = np.zeros(n); pos[1:] = state[:-1]
    turn = np.abs(np.diff(pos, prepend=0.0))
    ret = pos * r - cost * turn - pos * funding
    return {"ret": pd.Series(ret, index=df.index), "pos": pd.Series(pos, index=df.index), "turn": pd.Series(turn, index=df.index)}


def trades(res: dict) -> pd.DataFrame:
    """Operaciones = tramos de posición constante distinta de 0 (retorno compuesto incluyendo costes de entrada)."""
    pos = res["pos"].to_numpy(); ret = res["ret"].to_numpy(); idx = res["pos"].index
    out = []; i = 0; n = len(pos)
    while i < n:
        if pos[i] != 0:
            j = i
            while j + 1 < n and pos[j + 1] == pos[i]:
                j += 1
            out.append({"open": idx[i], "close": idx[j], "side": int(pos[i]), "bars": j - i + 1,
                        "ret": float(np.prod(1 + ret[i:j + 1]) - 1)})
            i = j + 1
        else:
            i += 1
    return pd.DataFrame(out, columns=["open", "close", "side", "bars", "ret"])


def daily(ret: pd.Series) -> pd.Series:
    return (1 + ret).resample("1D").prod() - 1


def simulate_pos(df: pd.DataFrame, pos: np.ndarray, funding: np.ndarray, cost: float = COST) -> dict:
    """Igual que simulate pero recibiendo la posición ya aplicada durante cada vela (para filtros de operaciones)."""
    r = df["close"].pct_change().fillna(0.0).to_numpy(); turn = np.abs(np.diff(pos, prepend=0.0))
    ret = pos * r - cost * turn - pos * funding
    return {"ret": pd.Series(ret, index=df.index), "pos": pd.Series(pos, index=df.index), "turn": pd.Series(turn, index=df.index)}
