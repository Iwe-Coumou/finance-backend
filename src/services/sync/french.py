from datetime import date, timedelta
from src.integrations.french import DATASETS, fetch_factors
from src.data.repositories import get_last_stored_factor_data, store_factors
from src.logger import get_logger
import pandas as pd

_logger = get_logger(__name__)

def fetch_and_store_factors(
    start: date = date(2000, 1, 1),
    frequency: str = "daily",
    regions: list[str] | None = None,
) -> None:
    regions = regions or list(DATASETS.keys())

    for region in regions:
        _logger.info(f"[{region}] Starting {frequency} factor fetch...")

        if DATASETS[region][frequency] is None:
            _logger.info(f"[{region}] No {frequency} data available, skipping.")
            continue

        last_date = get_last_stored_factor_data(frequency, region)
        region_start = last_date + timedelta(days=1) if last_date is not None else start

        _logger.info(f"[{region}] Fetching from {region_start}...")
        df = fetch_factors(start=region_start, frequency=frequency, region=region)

        if df.empty:
            _logger.debug(f"[{region}] No new {frequency} factor data.")
            continue

        _logger.info(f"[{region}] Got {len(df)} rows. Storing...")
        inserted = store_factors(df, frequency=frequency, region=region)
        _logger.info(f"[{region}] Done. {inserted} new rows inserted.")