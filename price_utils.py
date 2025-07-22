import os
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import requests


def fetch_recent_prices(region: str, hours: int = 24, api_key: Optional[str] = None) -> pd.DataFrame:
    """Retrieve recent hourly power prices from the EIA API.

    Parameters
    ----------
    region : str
        RTO or pricing region supported by the API (e.g. "NY", "PJM").
    hours : int, optional
        Number of hours of history to retrieve. Defaults to the last 24 hours.
    api_key : str, optional
        EIA API key. If not provided, the function looks for the
        ``EIA_API_KEY`` environment variable.

    Returns
    -------
    pandas.DataFrame
        DataFrame with ``timestamp`` and ``price`` columns.
    """
    if api_key is None:
        api_key = os.getenv("EIA_API_KEY")
    if not api_key:
        raise ValueError("An EIA API key is required. Set EIA_API_KEY env variable or pass api_key argument.")

    end = datetime.utcnow()
    start = end - timedelta(hours=hours)
    url = (
        "https://api.eia.gov/v2/electricity/rto/region-price/data/"
        f"?api_key={api_key}&data=price&frequency=hourly"
        f"&start={start.strftime('%Y-%m-%dT%H')}&end={end.strftime('%Y-%m-%dT%H')}"
        f"&region={region}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    payload = resp.json()
    data = payload.get("response", {}).get("data", [])
    df = pd.DataFrame(data)
    if df.empty:
        return df
    df = df.rename(columns={"timestamp": "timestamp", "value": "price"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df[["timestamp", "price"]]


def forecast_next_hour(prices: pd.DataFrame, window: int = 24) -> float:
    """Simple moving-average forecast of the next hour's price.

    Parameters
    ----------
    prices : pandas.DataFrame
        DataFrame produced by :func:`fetch_recent_prices`.
    window : int, optional
        Number of hours to include in the moving average. Defaults to 24.

    Returns
    -------
    float
        Forecasted price for the next hour.
    """
    if prices.empty:
        raise ValueError("No price data available for forecasting")
    return prices["price"].tail(window).mean()
