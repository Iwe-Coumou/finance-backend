from datetime import date
from fredapi import Fred
from src.config import get_env_var
from src.logging.logger import get_logger
from src.integrations.fred import SERIES, fetch_series
from src.data.repositories import store_macro_data

_logger = get_logger(__name__)

def fetch_and_store_macros(start: date = date(2000, 1, 1)) -> None:
    _logger.info(f"Starting macro sync from {start}...")
    fred_client = Fred(api_key=get_env_var("FRED_API_KEY", logger=_logger))
    
    for series_id, description in SERIES.items():
        try:
            data = fetch_series(series_id, fred_client, start)
            inserted = store_macro_data(series_id, description, data)
            _logger.info(f"{series_id}: {inserted} new rows inserted")
        except Exception as e:
            _logger.error(f"Failed to fetch/store {series_id}: {e}")
    
    _logger.info("Macro sync complete.")