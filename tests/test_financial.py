import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from plant import calculate_npv, calculate_lcoe, calculate_discounted_payback_period
from price_utils import forecast_next_hour, forecast_next_day_seasonal


def test_calculate_npv():
    cash_flows = [-100, 60, 60]
    npv = calculate_npv(cash_flows, 0.1)
    # NPV = -100/(1+0.1)^1 + 60/(1+0.1)^2 + 60/(1+0.1)^3
    expected = cash_flows[0] / 1.1 + cash_flows[1] / 1.1**2 + cash_flows[2] / 1.1**3
    assert abs(npv - expected) < 1e-8


def test_calculate_lcoe():
    invest = [50, 0]
    op = [0, 10]
    energy = [0, 100]
    lcoe = calculate_lcoe(invest, op, energy, 0.1)
    # discounted costs: 50/(1.1) + 10/(1.1**2)
    costs = 50/1.1 + 10/(1.1**2)
    energy_discounted = 100/(1.1**2)
    expected = costs / energy_discounted
    assert abs(lcoe - expected) < 1e-8


def test_discounted_payback_period():
    cash_flows = [-100, 40, 40, 40]
    dpp = calculate_discounted_payback_period(cash_flows, 0.05)
    assert dpp == 3


def test_forecast_next_hour():
    timestamps = pd.date_range("2024-01-01", periods=24, freq="H")
    prices = pd.DataFrame({"timestamp": timestamps, "price": range(24)})
    assert forecast_next_hour(prices) == sum(range(0,24))/24


def test_forecast_next_day_seasonal():
    timestamps = pd.date_range("2023-01-01", periods=365, freq="D")
    prices = pd.DataFrame({"timestamp": timestamps, "price": 2.0})
    # All prices the same -> forecast should equal that price
    assert forecast_next_day_seasonal(prices) == 2.0
