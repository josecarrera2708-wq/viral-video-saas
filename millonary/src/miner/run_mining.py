import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.miner.features import Market
from src.miner.ga import Miner

if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1].split(",")] if len(sys.argv) > 1 else [0]
    pop, gens = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (200, 12)
    out = Path(__file__).resolve().parents[2] / "data" / "mining"
    mk = {"1h": Market("1h"), "4h": Market("4h")}
    tot = 0
    for s in seeds:
        m = Miner(mk, out, seed=s).run(pop=pop, gens=gens)
        n = m.save(); tot += n
        print(f"isla {s}: {n} estrategias únicas guardadas", flush=True)
    print("TOTAL pruebas únicas:", tot)
