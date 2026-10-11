import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np, pandas as pd, pytest
from src.backtest.funding import align_funding, trim_to_funding


def _bars(tz="UTC"):
    return pd.date_range("2024-01-01", periods=30, freq="1h", tz=tz)


def test_alignment_with_millisecond_timestamps():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 08:00:00.001", "2024-01-01 16:00:00.001"], utc=True),
                      "funding_rate": [0.0001, -0.0002]})
    out = align_funding(_bars(), pd.Timedelta("1h"), f)
    assert out[7] == 0.0001 and out[15] == -0.0002 and out.sum() == pytest.approx(-0.0001)


def test_rejects_naive_index():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 08:00"], utc=True), "funding_rate": [0.0001]})
    with pytest.raises(ValueError):
        align_funding(_bars(None), pd.Timedelta("1h"), f)


def test_event_inside_bar_goes_to_that_bar():
    g = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 08:30"], utc=True), "funding_rate": [0.0001]})
    out = align_funding(_bars(), pd.Timedelta("1h"), g)      # 08:30 cae en la vela 08:00-09:00
    assert out[8] == 0.0001 and out.sum() == pytest.approx(0.0001)


def test_daily_and_4h_bars_collect_all_events():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-02 00:00:00.001", "2024-01-02 08:00:00.000", "2024-01-02 16:00:00.000"], utc=True),
                      "funding_rate": [0.0001, 0.0002, 0.0003]})
    d1 = pd.date_range("2024-01-01", periods=5, freq="1D", tz="UTC")
    o1 = align_funding(d1, pd.Timedelta("1D"), f)
    assert o1[0] == pytest.approx(0.0001)                      # el de 00:00 cierra el día 1
    assert o1[1] == pytest.approx(0.0005)                      # los de 08:00 y 16:00 son del día 2
    h4 = pd.date_range("2024-01-01", periods=12, freq="4h", tz="UTC")
    o4 = align_funding(h4, pd.Timedelta("4h"), f)
    assert o4.sum() == pytest.approx(0.0006) and o4[5] == 0.0001 and o4[7] == 0.0002 and o4[9] == 0.0003


def test_trim_to_funding_drops_bars_without_funding():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 16:00"], utc=True), "funding_rate": [0.0001]})
    df = pd.DataFrame({"x": range(30)}, index=_bars())
    assert df.index.max() > trim_to_funding(df, f, pd.Timedelta("1h")).index.max()
