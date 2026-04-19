from src.integrations.fmp import FMPClient, get_profile
from src.data.repositories import get_assets, update_isins
from src.logger import get_logger

_logger = get_logger(__name__)

def enrich(force: bool = False) -> None:
    asset_df = get_assets(cols=["isin"])
    
    if not force:
        asset_df = asset_df[asset_df["isin"].isna()]
    
    _logger.info(f"Starting ISIN enrichment for {len(asset_df)} assets...")
    
    client = FMPClient()
    isin_map = {}
    
    for ticker in asset_df.index:
        try:
            profile = get_profile(ticker, client)
            isin = profile.get("isin")
            if isin:
                isin_map[ticker] = isin
            else:
                _logger.debug(f"[{ticker}] No ISIN in FMP profile")
        except Exception as e:
            _logger.warning(f"[{ticker}] Failed to fetch profile: {e}")
    
    update_isins(isin_map, force=force)
    _logger.info(f"ISIN enrichment complete. Updated {len(isin_map)}/{len(asset_df)} assets.")