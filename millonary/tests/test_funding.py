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


def test_rejects_naive_index_and_unassigned_in_range():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 08:00"], utc=True), "funding_rate": [0.0001]})
    with pytest.raises(ValueError):
        align_funding(_bars(None), pd.Timedelta("1h"), f)
    g = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 08:30"], utc=True), "funding_rate": [0.0001]})
    with pytest.raises(ValueError):                       # marca dentro del rango sin vela exacta
        align_funding(_bars(), pd.Timedelta("1h"), g)


def test_trim_to_funding_drops_bars_without_funding():
    f = pd.DataFrame({"time": pd.to_datetime(["2024-01-01 16:00"], utc=True), "funding_rate": [0.0001]})
    df = pd.DataFrame({"x": range(30)}, index=_bars())
    assert df.index.max() > trim_to_funding(df, f, pd.Timedelta("1h")).index.max()
