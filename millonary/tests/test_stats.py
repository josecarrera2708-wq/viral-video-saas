import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
from src.robustness.stats import deflated_sharpe, expected_max_sr, pbo_cscv, monte_carlo, sharpe_pp


def test_dsr_penalizes_many_trials():
    rng = np.random.default_rng(0)
    r = rng.normal(0.0008, 0.01, 750)                     # SR diario ≈ 0,08 (≈1,3 anualizado)
    few = deflated_sharpe(r, 5, 0.0004 ** 2 * 10)
    many = deflated_sharpe(r, 20000, 0.0004 ** 2 * 10)
    assert many < few
    assert expected_max_sr(20000, 1e-4) > expected_max_sr(10, 1e-4)


def test_dsr_pure_noise_is_not_significant_after_selection():
    rng = np.random.default_rng(1)
    N, T = 2000, 750
    R = rng.normal(0, 0.01, (T, N))                       # 2000 estrategias SIN habilidad
    srs = np.array([sharpe_pp(R[:, i]) for i in range(N)])
    best = int(np.argmax(srs))
    d = deflated_sharpe(R[:, best], N, srs.var(ddof=1))
    assert srs[best] > 0.08                               # la mejor PARECE buena…
    assert d < 0.95                                       # …pero el DSR la descarta


def test_pbo_high_for_noise_low_for_skill():
    rng = np.random.default_rng(2)
    noise = rng.normal(0, 0.01, (800, 40))
    assert pbo_cscv(noise, s=8) > 0.3
    skill = rng.normal(0, 0.01, (800, 40)); skill[:, 0] += 0.004    # una con habilidad real
    assert pbo_cscv(skill, s=8) < 0.3


def test_monte_carlo_monotonic():
    good = np.r_[np.full(60, 0.02), np.full(40, -0.01)]
    bad = np.r_[np.full(40, 0.01), np.full(60, -0.01)]
    p5g, ddg, _ = monte_carlo(good); p5b, ddb, pl = monte_carlo(bad)
    assert p5g > 0 > p5b and pl > 0.5 and ddb > ddg
