import numpy as np
import pandas as pd
import pytest
from src.busqueda import v13


def test_agrupar_ventana_4h():
    rows = [("2024-01-01 10:00", 1, "a", "I"), ("2024-01-01 13:00", 1, "b", "E"), ("2024-01-01 15:00", -1, "c", "S"),
            ("2024-01-01 20:00", 1, "a", "I"), ("2024-01-01 22:00", -1, "b", "E")]
    sig = pd.DataFrame([{"t": pd.Timestamp(t, tz="UTC"), "d": d, "setup": s, "origen": o, "tf": "1h"} for t, d, s, o in rows])
    ev = v13.agrupar(sig)
    assert len(ev) == 2 and list(ev["d"]) == [1, -1]                    # 10:00+13:00 juntos; 15:00 solo; 20:00+22:00 opuestas → fuera
    assert ev["t"].iloc[1] == pd.Timestamp("2024-01-01 15:00", tz="UTC")


@pytest.fixture(scope="module")
def tramo():
    from src.busqueda import intradia5 as I
    b5, f5 = I.load5(); m = (b5.index >= "2022-01-01") & (b5.index < "2022-06-01")
    return b5[m], f5[m]


def test_barrera_swing(tramo):
    b5, _ = tramo
    ev = pd.DataFrame({"t": pd.to_datetime(["2022-04-01 12:00"], utc=True), "d": [1]})
    s = v13.barrera(b5, ev); P = b5["close"].loc[:"2022-04-01 11:55"].iloc[-1]
    assert s[0] / P >= 0.02 - 1e-12


def test_causal(tramo):
    b5, _ = tramo
    ev = v13.agrupar(v13.señales(b5)); ev = ev[ev["t"] >= "2022-03-15"].reset_index(drop=True)
    T = pd.Timestamp("2022-05-01", tz="UTC"); e = ev[ev["t"] <= T].reset_index(drop=True)
    s1 = v13.barrera(b5, e); X1 = v13.variables(b5, e, s1)
    b5t = b5[b5.index < T]; s2 = v13.barrera(b5t, e); X2 = v13.variables(b5t, e, s2)
    assert np.allclose(s1, s2, equal_nan=True); pd.testing.assert_frame_equal(X1, X2)
    assert "o_P" not in X1 and "tf_4h" in X1


def test_cartera_tope_swing():
    t0 = pd.Timestamp("2024-01-01", tz="UTC")
    ops = pd.DataFrame({"t": [t0], "salida": [t0 + pd.Timedelta("1D")], "d": [1], "tf": ["4h"], "R": [1.0], "riesgo": [0.01],
                        "stop_pct": [0.004], "lu": [1.0]})
    p = v13.cartera(ops)
    assert np.isclose(p["apal"].iloc[0], 2.0) and np.isclose(p["riesgo"].iloc[0], 0.008)
