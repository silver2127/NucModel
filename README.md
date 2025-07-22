# NucModel

Nuclear Power Plant Financial Model maker

## Power price utilities

The `price_utils.py` module retrieves hourly power prices from the U.S. Energy Information Administration (EIA) API and provides a simple forecast utility. Set the environment variable `EIA_API_KEY` or pass the API key directly when calling `fetch_recent_prices`.

Example:

```python
from price_utils import fetch_recent_prices, forecast_next_hour

prices = fetch_recent_prices(region="NY", hours=24, api_key="YOUR_KEY")
next_hour = forecast_next_hour(prices)
print("Forecasted price:", next_hour)
```
