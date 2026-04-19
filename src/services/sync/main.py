from src.services.sync import yf, french, fred
from src.services.enrichment import enrich_all
from datetime import date
from src.logger import get_logger

_logger = get_logger(__name__)


def fetch_all(tickers: list, start: date = date(2000, 1, 1), end=None):
    _logger.info("Starting full data fetch pipeline...")

    yf.fetch_and_store(tickers, start, end)
    fred.fetch_and_store_macros(start)
    french.fetch_and_store_factors(start=start, frequency="daily")
    french.fetch_and_store_factors(start=start, frequency="monthly")

    _logger.info("Fetching complete.")


def main():
    from src.data.config import TEST_TICKERS
    fetch_all(TEST_TICKERS)
    enrich_all(False)    


if __name__ == "__main__":
    main()
