import pandas as pd
import requests

ALPHA_URL = "https://www.alphavantage.co/query"

def fetch_daily_ohlcv(symbol: str, api_key: str) -> pd.DataFrame:
    """Fetch daily adjusted OHLCV from Alpha Vantage and normalize columns.
    Falls back to empty DataFrame on any error.
    """
    try:
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": "compact",
            "datatype": "json",
            "apikey": api_key,
        }
        r = requests.get(ALPHA_URL, params=params, timeout=15)
        r.raise_for_status()
        js = r.json()
        series = js.get("Time Series (Daily)", {})
        if not series:
            return pd.DataFrame()
        rows = []
        for date, vals in series.items():
            rows.append({
                "symbol": symbol,
                "timestamp": pd.to_datetime(date),
                "open": float(vals.get("1. open", 0)),
                "high": float(vals.get("2. high", 0)),
                "low": float(vals.get("3. low", 0)),
                "close": float(vals.get("4. close", 0)),
                "volume": float(vals.get("6. volume", vals.get("5. volume", 0))),
            })
        df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
        return df
    except Exception:
        return pd.DataFrame()
