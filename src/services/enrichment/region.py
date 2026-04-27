from src.data.repositories import get_assets, update_asset_region
from src.logging.logger import get_logger
from src.data.config import COUNTRY_TO_REGION
import pandas as pd


_logger = get_logger(__name__)

def _derive_region(asset: pd.Series) -> str:
    asset_type = asset.get("asset_type")
    
    if asset_type == "equity":
        return _equity_region(asset)
    elif asset_type == "etf":
        return _etf_region(asset)
    else:
        return "global"

def _equity_region(asset: pd.Series) -> str:
    country = asset.get("country")
    return COUNTRY_TO_REGION.get(country, "global") if country else "global"

def _etf_region(asset: pd.Series) -> str:
    return "global"



def enrich(force: bool = False):
    asset_df = get_assets(cols=["asset_type", "country", "name", "region"])
    _logger.info(f"Starting region enrichment for {len(asset_df)} assets...")

    for ticker, asset in asset_df.iterrows():
        ticker = str(ticker)
        region = _derive_region(asset)
        if region:
            update_asset_region(ticker, region, force=force)

    _logger.info("Region enrichment complete.")
            
def main():
    enrich(force=False)

if __name__ == "__main__":
    main()