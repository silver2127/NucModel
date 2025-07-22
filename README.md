# NucModel

Nuclear Power Plant Financial Model maker

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
