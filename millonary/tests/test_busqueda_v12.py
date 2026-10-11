import numpy as np
import pandas as pd
import pytest
from src.busqueda import v12
from src.busqueda.evaluate_v12 import trimestres, t_dia
from src.busqueda.sim5 import simulate


def _sig(rows):
    return pd.DataFrame([{"t": pd.Timestamp(t, tz="UTC"), "d": d, "setup": s, "origen": o, "tf": "1h"} for t, d, s, o in rows])


def test_agrupar_misma_direccion_y_opuestas():
    sig = _sig([("2024-01-01 10:00", 1, "a", "I"), ("2024-01-01 10:00", 1, "b", "P"), ("2024-01-01 10:30", 1, "c", "E"),
                ("2024-01-01 12:00", 1, "a", "I"), ("2024-01-01 12:15", -1, "b", "P"), ("2024-01-01 14:00", -1, "d", "S")])
    ev = v12.agrupar(sig)
    assert len(ev) == 2                                                   # el racimo de las 12:00 tiene direcciones opuestas → fuera
    assert ev["n_setups"].iloc[0] == 2 and ev["o_E"].iloc[0] == 0         # el de las 10:30 aún no se conocía a las 10:00
    assert ev["d"].iloc[1] == -1 and ev["t"].iloc[1] == pd.Timestamp("2024-01-01 14:00", tz="UTC")


def test_pesos_unicidad():
    t = pd.Series(pd.to_datetime(["2024-01-01 00:00", "2024-01-01 01:00", "2024-01-01 10:00"], utc=True))
    x = pd.Series(pd.to_datetime(["2024-01-01 02:00", "2024-01-01 03:00", "2024-01-01 11:00"], utc=True))
    assert np.allclose(v12.pesos_unicidad(t, x), [0.5, 0.5, 1.0])


def test_trimestres():
    q = trimestres(); assert len(q) == 16 and str(q[0][0].date()) == "2022-10-01"


def test_t_dia_agrupa():
    t = pd.to_datetime(["2024-01-01 01:00"] * 10 + ["2024-01-02 01:00"] * 10, utc=True)
    R = np.r_[np.ones(10), -np.ones(10) * 0.5]
    assert abs(t_dia(t, R)) < 1.0                                       # 2 días, no 20 observaciones independientes


@pytest.fixture(scope="module")
def tramo():
    from src.busqueda import intradia5 as I
    b5, f5 = I.load5(); m = (b5.index >= "2022-01-01") & (b5.index < "2022-05-01")
    return b5[m], f5[m]


def test_etiquetas_igual_que_simulador(tramo):
    b5, f5 = tramo
    ev = pd.DataFrame({"t": pd.to_datetime(["2022-03-01 10:00", "2022-03-01 11:00"], utc=True), "d": [1, -1]})
    s = np.array([400.0, 300.0]); g = v12.CONFIGS["C1 2R"]
    L = v12.etiquetas(b5, f5, ev, s, g)
    for k in range(2):
        r = simulate(b5, f5, pd.DatetimeIndex(ev["t"][k:k + 1]), ev["d"].to_numpy()[k:k + 1], s[k:k + 1], g)
        assert np.isclose(L["R"][k], r["R"].iloc[0])


def test_variables_causales(tramo):
    """Truncar los datos en T no cambia las variables ni la barrera de los eventos anteriores a T."""
    b5, _ = tramo
    ev = v12.agrupar(v12.señales(b5)); ev = ev[ev["t"] >= "2022-03-01"].reset_index(drop=True)
    T = pd.Timestamp("2022-04-01", tz="UTC"); e = ev[ev["t"] <= T].reset_index(drop=True)
    s1 = v12.barrera(b5, e); X1 = v12.variables(b5, e, s1)
    b5t = b5[b5.index < T]; s2 = v12.barrera(b5t, e); X2 = v12.variables(b5t, e, s2)
    assert np.allclose(s1, s2, equal_nan=True)
    pd.testing.assert_frame_equal(X1, X2)
    ev2 = v12.agrupar(v12.señales(b5t)); ev2 = ev2[(ev2["t"] >= "2022-03-01") & (ev2["t"] <= T - pd.Timedelta("2h"))].reset_index(drop=True)
    e1 = e[e["t"] <= T - pd.Timedelta("2h")].reset_index(drop=True)
    pd.testing.assert_frame_equal(e1[["t", "d"]], ev2[["t", "d"]])


def test_cartera_limites():
    t0 = pd.Timestamp("2024-01-01", tz="UTC"); H = pd.Timedelta("1h")
    ops = pd.DataFrame({"t": [t0, t0 + H, t0 + 2 * H, t0 + 3 * H, t0 + 10 * H], "salida": [t0 + 5 * H] * 4 + [t0 + 11 * H],
                        "d": [1, -1, 1, 1, 1], "tf": "1h", "R": 1.0, "riesgo": 0.01, "stop_pct": 0.005, "lu": 1.0})
    p = v12.cartera(ops)
    assert list(p["t"]) == [t0, t0 + 2 * H, t0 + 10 * H]                 # opuesta y tercera posición rechazadas
    assert (p["apal"] <= 5.0).all() and np.isclose(p["capital"].max(), 1030.2)
