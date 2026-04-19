from src.data.repositories import get_assets, update_figis
from src.integrations.openfigi import OpenFIGIClient, get_figi_batch
from src.logger import get_logger
import time

_logger = get_logger(__name__)

def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def enrich(force: bool = False):
    client = OpenFIGIClient()
    asset_df = get_assets(cols=["exchange", "isin"])
    _logger.info(f"Starting FIGI enrichment for {len(asset_df)} assets...")

    updated = 0
    for batch in _chunks(list(asset_df.index), 10):
        results = get_figi_batch(asset_data=asset_df.loc[batch], client=client)
        figi_map = {
            ticker: figi_data["figi"]
            for ticker, figi_data in results.items()
            if figi_data and figi_data.get("figi")
        }
        update_figis(figi_map, force=force)
        updated += len(figi_map)
        time.sleep(2)

    _logger.info(f"FIGI enrichment complete. Updated {updated}/{len(asset_df)} assets.")