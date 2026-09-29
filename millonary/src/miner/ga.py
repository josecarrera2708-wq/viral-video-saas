"""Minero genético. Solo ve el tramo TRAIN (barrera anti-fuga). Registra TODAS las pruebas."""
from __future__ import annotations
import json, math, random, time
from pathlib import Path
import numpy as np
import pandas as pd
from .features import Market
from .strategy import CHOICES, ENTRY_TYPES, REGIMES, random_genome, genome_key, evaluate, active, n_params

ROOT = Path(__file__).resolve().parents[2]
SPLITS = json.loads((ROOT / "config" / "splits.json").read_text())
TRAIN = tuple(SPLITS["train"])


def fitness(m: dict, g: dict, min_trades: int) -> float:
    if m["ruined"] or m["trades"] < min_trades:
        return -10.0 + min(1.0, m["trades"] / max(1, min_trades)) - (5.0 if m["ruined"] else 0.0)
    if m["exp_r"] <= 0:
        return -1.0 + min(m["sharpe"], 0.0)
    shrink = min(1.0, math.sqrt(m["trades"] / (2 * min_trades)))
    return m["sharpe"] * shrink - 2.0 * max(0.0, m["maxdd"] - 0.25) - 0.02 * n_params(g)


class Miner:
    def __init__(self, markets: dict[str, Market], out_dir: Path, seed: int = 0,
                 train: tuple = None):
        """train=(inicio, fin). Los mercados se TRUNCAN físicamente en `fin`: el minero no puede
        ver ningún dato posterior (barrera real, no una comparación de sí mismo)."""
        self.train = tuple(train) if train else TRAIN
        self.rng, self.seed = random.Random(seed), seed
        self.mk = {tf: mk.truncate(self.train[1]) for tf, mk in markets.items()}
        self.rng_range = {tf: mk.index_range(self.train[0], None) for tf, mk in self.mk.items()}
        self.trials: dict[str, dict] = {}            # clave -> registro (cuenta de pruebas únicas)
        self.out = Path(out_dir); self.out.mkdir(parents=True, exist_ok=True)

    def _min_trades(self, tf): return 150 if tf == "1h" else 100

    def eval(self, g: dict) -> float:
        k = genome_key(g)
        if k in self.trials:
            return self.trials[k]["fitness"]
        a, b = self.rng_range[g["tf"]]
        r = evaluate(g, self.mk[g["tf"]], a, b); r.pop("_res")
        f = fitness(r, g, self._min_trades(g["tf"]))
        self.trials[k] = {"key": k, "genome": json.dumps(active(g), default=str), "fitness": f,
                          "seed": self.seed, **{f"tr_{x}": v for x, v in r.items()}}
        self.trials[k]["_g"] = g
        return f

    def _mutate(self, g: dict, rate=0.18) -> dict:
        n = dict(g)
        for key, opts in CHOICES.items():
            if self.rng.random() < rate: n[key] = self.rng.choice(opts)
        if self.rng.random() < rate: n["entry"] = self.rng.choice(ENTRY_TYPES)
        if self.rng.random() < rate: n["regime"] = self.rng.choice(REGIMES)
        n["fast"] = min(CHOICES["fast"], key=lambda x: abs(x - n["fast"]))       # siempre en la rejilla
        n["slow"] = min(CHOICES["slow"], key=lambda x: abs(x - n["slow"]))
        if n["fast"] >= n["slow"]:
            smaller = [x for x in CHOICES["fast"] if x < n["slow"]]
            n["fast"] = max(smaller) if smaller else min(CHOICES["fast"])
        return n

    def _cross(self, a: dict, b: dict) -> dict:
        return {k: (a[k] if self.rng.random() < 0.5 else b[k]) for k in a}

    def run(self, pop=200, gens=12, elite=0.05, log=True):
        popl = [random_genome(self.rng) for _ in range(pop)]
        t0 = time.time()
        for gen in range(gens):
            fits = [self.eval(g) for g in popl]
            order = np.argsort(fits)[::-1]
            best = fits[order[0]]
            if log:
                ok = sum(1 for f in fits if f > 0)
                print(f"  isla {self.seed} gen {gen+1}/{gens}: mejor {best:.2f} | con fitness>0: {ok}/{pop} "
                      f"| únicas probadas {len(self.trials)} | {time.time()-t0:.0f}s", flush=True)
            nel = max(1, int(pop * elite)); nxt = [popl[i] for i in order[:nel]]
            def pick():
                cand = self.rng.sample(range(pop), 3); return popl[max(cand, key=lambda i: fits[i])]
            while len(nxt) < pop:
                child = self._mutate(self._cross(pick(), pick()))
                nxt.append(child)
            popl = nxt
        return self

    def save(self):
        rows = [{k: v for k, v in t.items() if k != "_g"} for t in self.trials.values()]
        pd.DataFrame(rows).to_parquet(self.out / f"trials_seed{self.seed}.parquet", index=False)
        return len(rows)
