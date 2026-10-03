"""¿Aporta algo el minero frente a estrategias elegidas al azar?

Compara las candidatas minadas (mejores en TRAIN) con estrategias aleatorias sin minar que cumplen los
mismos mínimos de operaciones. Mide la degradación train -> validación y la correlación de rangos.
Solo usa TRAIN y VALIDATION (nunca el periodo ciego).
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import pandas as pd
from scipy import stats

from src.miner.features import Market
from src.miner.strategy import evaluate, random_genome
from src.robustness import funnel as F

if __name__ == "__main__":
    F.MK = {"1h": Market("1h"), "4h": Market("4h")}
    root = Path(__file__).resolve().parents[2]
    res = pd.read_parquet(root / "reports" / "funnel_results.parquet")
    print("=== 150 candidatas minadas (mejores en train) ===")
    print("Sharpe train medio %.2f | validación medio %.2f | mediana val %.2f | %% val>0: %.0f%%" % (
        res.train_sharpe.mean(), res.val_sharpe.mean(), res.val_sharpe.median(),
        100 * (res.val_sharpe > 0).mean()))
    print("correlación de rangos train<->val (Spearman): %.2f" %
          stats.spearmanr(res.train_sharpe, res.val_sharpe)[0])

    rng = random.Random(123)
    rows = []
    while len(rows) < 1500:
        g = random_genome(rng)
        tf = g["tf"]
        m = F.MK[tf]
        a, b = F.rng_of(tf, "train")
        av, bv = F.rng_of(tf, "validation")
        tr = evaluate(g, m, a, b)
        if tr["trades"] < (150 if tf == "1h" else 100) or tr["ruined"]:
            continue
        va = evaluate(g, m, av, bv)
        rows.append((tr["sharpe"], va["sharpe"], va["trades"]))
    r = pd.DataFrame(rows, columns=["tr", "va", "n"])
    print("\n=== 1500 estrategias ALEATORIAS (sin minar), mismos mínimos de operaciones ===")
    print("Sharpe train medio %.2f | validación medio %.2f | mediana val %.2f | %% val>0: %.0f%% | %% val>1: %.1f%%" % (
        r.tr.mean(), r.va.mean(), r.va.median(), 100 * (r.va > 0).mean(), 100 * (r.va > 1).mean()))
    print("correlación de rangos train<->val: %.2f" % stats.spearmanr(r.tr, r.va)[0])
    print("\nminadas con val Sharpe>1: %.0f%% vs aleatorias: %.1f%%" % (
        100 * (res.val_sharpe > 1).mean(), 100 * (r.va > 1).mean()))
    top = r.sort_values("tr", ascending=False).head(150)
    print("aleatorias: sus 150 mejores en train -> validación media %.2f" % top.va.mean())
