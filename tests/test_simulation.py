import pandas as pd
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from plant import simulate_plant_operation


def test_simulate_plant_operation():
    timestamps = pd.date_range("2024-01-01", periods=48, freq="H")
    prices = pd.DataFrame({"timestamp": timestamps, "price": 50.0})
    profit, _ = simulate_plant_operation(prices, capacity_mw=1000,
                                         fuel_cost_per_mwh=10,
                                         maintenance_days=1,
                                         capacity_factor=1.0)
    # 24 hours offline -> 24 hours running at 1000 MW
    energy = 24 * 1000
    expected = (50.0 * energy) - (10 * energy)
    assert abs(profit - expected) < 1e-6

def test_simulate_refueling_cost():
    timestamps = pd.date_range("2024-01-01", periods=48, freq="H")
    prices = pd.DataFrame({"timestamp": timestamps, "price": 50.0})
    hours_per_cycle = 18 * 30 * 24
    energy_cycle = 1000 * 1.0 * hours_per_cycle
    refuel_cost = 10 * energy_cycle
    profit_mwh, _ = simulate_plant_operation(
        prices,
        capacity_mw=1000,
        fuel_cost_per_mwh=None,
        maintenance_days=1,
        capacity_factor=1.0,
        fuel_cost_per_refueling=refuel_cost,
    )
    energy = 24 * 1000
    expected = (50.0 * energy) - (10 * energy)
    assert abs(profit_mwh - expected) < 1e-6
