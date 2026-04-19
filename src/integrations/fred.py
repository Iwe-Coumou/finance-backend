from src.logger import get_logger
from fredapi import Fred
from datetime import date
import pandas as pd

_logger = get_logger(__name__)

SERIES = {
    "T10Y2Y": "Yield curve slope (10y minus 2y treasury",
    "BAMLC0A0CM": "IG corporate bond credit spread",
    "CPIAUCSL": " CPI - consumer price index (inflation)",
    "UNRATE": "US unemployment rate",
    "VIXCLS": "CBOE VIX volatility index",
    "T10YIE": "10-year breakeven inflation rate",
    "DPCREDIT": "Discount window primary credit rate",
}

def fetch_series(series_id: str, fred_client: Fred, start: date = date(2000, 1, 1)) -> pd.Series:
    _logger.debug(f"Fetching {series_id} from FRED (start={start})...")
    data = fred_client.get_series(series_id, observation_start=start)
    return data.dropna()