from src.data.fetchers import fred, yf, french
from datetime import date
from src.logger import get_logger

logger = get_logger(__name__)


def fetch_all(tickers: list, start: date = date(2000, 1, 1), end=None):
    logger.info("Starting full data fetch pipelin...")

    yf.fetch_and_store(tickers, start, end)
    fred.fetch_and_store_macros(start)
    french.fetch_and_store_factors(start=start, frequency="daily")
    french.fetch_and_store_factors(start=start, frequency="monthly")

    logger.info("Fetching complete.")


def main():
    from src.data.config import TEST_TICKERS

    fetch_all(TEST_TICKERS)


if __name__ == "__main__":
    main()
