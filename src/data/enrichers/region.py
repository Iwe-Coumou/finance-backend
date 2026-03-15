from src.data.retrievers.assets import get_assets
from src.config import get_logger, AssetType
from src.data.config import COUNTRY_TO_REGION
from src.data.database.db import get_engine, Asset
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, update, func

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

def _update_region(ticker: str, region: str, force: bool = False) -> None:
    engine = get_engine()
    with Session(engine) as session:
        asset = session.execute(
            select(Asset).where(Asset.ticker == ticker)
        ).scalar_one_or_none()
        
        if not asset:
            _logger.warning(f"[{ticker}] Asset not found")
            return
        if str(asset.region) and not force:
            _logger.debug(f"[{ticker}] Region already set to '{asset.region}', skipping")
            return
        
        session.execute(
            update(Asset)
            .where(Asset.ticker == ticker)
            .values(region=region, updated_at=func.now())
        )
        session.commit()
    _logger.debug(f"[{ticker}] Region set to '{region}'")

def enrich(force: bool = False):
    asset_df = get_assets(cols=["asset_type", "country", "name", "region"])
    
    for ticker, asset in asset_df.iterrows():
        ticker = str(ticker)
        region = _derive_region(asset)
        if region:
            _update_region(ticker, region, force=force)
            
def main():
    enrich(force=False)

if __name__ == "__main__":
    main()