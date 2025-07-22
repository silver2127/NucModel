# NucModel

Simple financial model and data utilities for nuclear power plants.

## Getting Started

1. Install dependencies: `pip install pandas numpy numpy-financial statsmodels requests pytest`.
2. Run `python create_secrets.py` or set `EIA_API_KEY` to configure API access.
3. Execute `python plant.py` to perform a full financial calculation.

## Power price utilities

The `price_utils.py` module retrieves hourly or daily power prices from the U.S. Energy Information Administration (EIA) API and provides simple forecast utilities. Set the environment variable `EIA_API_KEY`, create a `secrets.json` file with the key, or pass the API key directly when calling the fetch functions.

Run `python create_secrets.py` to create the `secrets.json` file interactively. The module will read the key from this file if the environment variable is not set.

Example:

```python
from price_utils import fetch_recent_prices, forecast_next_hour, forecast_arima

prices = fetch_recent_prices(region="NY", hours=24, api_key="YOUR_KEY")
next_hour = forecast_next_hour(prices)
print("Forecasted price:", next_hour)

# Forecast using an ARIMA model with automatic parameter tuning
next_hour_arima = forecast_arima(prices)
print("ARIMA forecast:", next_hour_arima)
```

You can also retrieve daily prices over multiple years and compute a seasonal forecast:

```python
from price_utils import fetch_daily_prices, forecast_next_day_seasonal

# Pull three years of daily data and forecast tomorrow's price
prices_daily = fetch_daily_prices(region="NY", years=3, api_key="YOUR_KEY")
next_day = forecast_next_day_seasonal(prices_daily)
print("Seasonal forecast:", next_day)
```

## Plant operation simulation

`plant.py` includes a `simulate_plant_operation` function for modeling plant
profitability against hourly price data. The function accounts for scheduled
maintenance downtime, fuel costs, and the plant's capacity factor. Fuel costs
can be specified either directly in dollars per MWh or as a total cost per
refueling cycle, which is then converted to a per-MWh value.

Example:

```python
import pandas as pd
from plant import simulate_plant_operation

timestamps = pd.date_range("2024-01-01", periods=48, freq="H")
prices = pd.DataFrame({"timestamp": timestamps, "price": 50.0})
profit, results = simulate_plant_operation(prices, capacity_mw=1000,
                                           fuel_cost_per_mwh=10,
                                           maintenance_days=1)
print("Profit:", profit)
```

Fuel cost can also be provided per refueling cycle:

```python
refuel_cost = 10 * 1000 * 24 * 18 * 30  # equivalent to $10/MWh for a cycle
profit, _ = simulate_plant_operation(prices, capacity_mw=1000,
                                     fuel_cost_per_mwh=None,
                                     fuel_cost_per_refueling=refuel_cost,
                                     maintenance_days=1)
```

An example set of plant parameters is provided in `example_plant.json`. Running
`python plant.py` will load this file and execute a full financial calculation
using those values. Additional templates are available in the `plant_templates`
directory. Specify one with the `--params` flag:

```bash
python plant.py --params plant_templates/vogtle.json
```

## Development Notes

When contributing code:

1. Run `python -m py_compile plant.py` to ensure the main script compiles.
2. Execute `python plant.py` to verify the example parameters still work.
3. Run `pytest` to execute the test suite.


