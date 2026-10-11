import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import pytest
from src.signals import indicators as I, candles as C


def synth(n=1200, seed=0):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.r_[c[0], c[:-1]] * (1 + rng.normal(0, 0.002, n))
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.004, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.004, n)))
    v = rng.uniform(100, 1000, n)
    idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}, index=idx)


FEATURES = {
    "sma": lambda d: I.sma(d.close, 20), "ema": lambda d: I.ema(d.close, 20),
    "atr": lambda d: I.atr(d, 14), "rsi": lambda d: I.rsi(d.close, 14),
    "mfi": lambda d: I.mfi(d, 14), "macd": lambda d: I.macd(d.close),
    "boll": lambda d: I.bollinger(d.close), "donchian": lambda d: I.donchian(d, 20),
    "relvol": lambda d: I.rel_volume(d), "volpct": lambda d: I.vol_percentile(d, window=200),
    "slope": lambda d: I.slope(I.sma(d.close, 20)), "swings": lambda d: I.swings(d, 3),
    "structure": lambda d: I.structure_break(d, 3), "candles": C.all_candles,
}


@pytest.mark.parametrize("name", list(FEATURES))
def test_causal_truncation_invariance(name):
    """Calcular con datos cortados en m debe dar lo mismo, hasta m, que con los datos completos."""
    d = synth()
    full = FEATURES[name](d)
    for m in (300, 517, 900):
        part = FEATURES[name](d.iloc[:m])
        a = full.iloc[:m]; b = part
        pd.testing.assert_frame_equal(pd.DataFrame(a), pd.DataFrame(b), check_dtype=False,
                                      check_exact=False, rtol=1e-9, atol=1e-9)


def mk(rows):
    return pd.DataFrame(rows, columns=["open", "high", "low", "close"]).assign(volume=1.0)


def test_marubozu_green_is_bullish():
    d = mk([(100, 110, 100, 110)])
    assert C.marubozu(d).iloc[0] == 1
    assert C.marubozu(mk([(110, 110, 100, 100)])).iloc[0] == -1     # rojo = bajista


def test_hammer_after_decline():
    down = [(100 - i, 100 - i + 0.5, 100 - i - 1, 100 - i - 0.8) for i in range(8)]
    ham = (92.0, 92.2, 88.0, 92.1)                                  # cuerpo arriba, mecha inferior larga
    d = mk(down + [ham])
    assert C.hammer_family(d)["hammer"].iloc[-1] == 1
    assert C.hammer_family(d)["hanging_man"].iloc[-1] == 0


def test_bullish_engulfing():
    d = mk([(100, 101, 98, 99), (98.5, 103, 98, 102)])
    assert C.engulfing(d).iloc[-1] == 1
    d2 = mk([(99, 102, 98, 101), (101.5, 102, 97, 98)])
    assert C.engulfing(d2).iloc[-1] == -1


def test_doji_and_pin_bar():
    assert C.doji(mk([(100, 105, 95, 100.2)])).iloc[0] == 1
    assert C.pin_bar(mk([(104, 105, 95, 104.8)])).iloc[0] == 1      # mecha inferior larga, cuerpo arriba


def test_swing_confirmed_only_after_k_bars():
    h = [1, 2, 3, 10, 3, 2, 1, 1, 1]
    d = pd.DataFrame({"open": h, "high": h, "low": h, "close": h, "volume": 1.0})
    s = I.swings(d, 2)["last_high"]
    assert np.isnan(s.iloc[3]) and np.isnan(s.iloc[4])              # aún no confirmado
    assert s.iloc[5] == 10                                          # confirmado 2 velas después


def test_rsi_bounds_and_known_value():
    d = synth()
    r = I.rsi(d.close).dropna()
    assert ((r >= 0) & (r <= 100)).all()
    up = pd.Series(np.arange(1.0, 60.0))
    assert I.rsi(up).iloc[-1] == 100.0
