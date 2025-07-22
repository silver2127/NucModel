import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from price_utils import forecast_next_hour, backcast


def test_backcast_constant_series():
    timestamps = pd.date_range("2024-01-01", periods=30, freq="H")
    prices = pd.DataFrame({"timestamp": timestamps, "price": 5.0})
    result = backcast(prices, forecast_next_hour, window=24)
    assert len(result) == 6
    assert all(abs(result["predicted"] - 5.0) < 1e-6)
    assert all(abs(result["error"]) < 1e-6)
