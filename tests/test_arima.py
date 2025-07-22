import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from price_utils import forecast_arima


def test_forecast_arima_constant():
    # Constant price should forecast same value
    data = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=30, freq="H"),
        "price": [5.0]*30
    })
    forecast = forecast_arima(data, order=(1,0,0))
    assert abs(forecast - 5.0) < 1e-1
