from src.logging.logger import get_logger
from datetime import date
from src.integrations.yf import fetch_prices, fetch_info, fetch_fundamentals
from src.data.repositories import store_all_returns, store_asset_data, store_all_prices, store_fundamentals
from src.services.transforms import compute_returns
from datetime import date as date_type
from src.data.config import TEST_TICKERS 

_logger = get_logger(__name__)

def fetch_and_store(tickers: list, start: date = date(2000, 1, 1), end=None) -> None:
    _logger.info("Starting fetch and store pipeline...")


    prices_df = fetch_prices(tickers)
    if prices_df is None:
        _logger.error("No price data fetched, aborting pipeline")
        return
    
    successful_tickers = prices_df.index.get_level_values("ticker").unique().to_list()
    
    info_df = fetch_info(successful_tickers)
    if info_df is None:
        _logger.error("No asset info fetched, aborting pipeline")
        return


    returns_df = compute_returns(prices_df)

    fundamentals_df = fetch_fundamentals(successful_tickers)

    store_asset_data(info_df)
    store_all_prices(successful_tickers, prices_df)
    store_all_returns(successful_tickers, returns_df)
    if fundamentals_df is not None:
        store_fundamentals(fundamentals_df, snapshot_date=date_type.today())

    _logger.info("Pipeline complete")
    
if __name__ == "__main__":
    fetch_and_store(TEST_TICKERS)