import yfinance as yf
from src.logger import get_logger
import pandas as pd
from datetime import date, timedelta
import contextlib
import io
from src.config import QUOTE_TYPE_MAP

_logger = get_logger(__name__)

def get_ticker_prices(
    ticker: str, start: date = date(2000, 1, 1), end=None
) -> pd.DataFrame:
    end = end or date.today() + timedelta(days=1)

    _logger.debug(f"Getting data for {ticker}...")
    try:
        yf_ticker = yf.Ticker(ticker)
        with contextlib.redirect_stderr(io.StringIO()):
            history = yf_ticker.history(start=start, end=end, auto_adjust=False)
        if history.empty:
            raise ValueError(f"No data returned for {ticker}")
        _logger.debug(f"Data for {ticker} recieved")
        return history
    except Exception as e:
        _logger.debug(f"{ticker} is not a valid ticker: {e}")
        raise
    
def fetch_prices(
    tickers: list, start: date = date(2000, 1, 1), end=None
) -> pd.DataFrame | None:
    end = end or date.today() + timedelta(days=1)

    _logger.info("Downloading data from yfinance...")

    succes_count = 0
    failed = []
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = get_ticker_prices(ticker, start, end)
            succes_count += 1
        except Exception as e:
            _logger.warning(f"Skipping {ticker}: {e}")
            failed.append(ticker)

    _logger.info(f"Succesfully downloaded data from yfinance for {succes_count} tickers")
    if failed:
        _logger.warning(f"Failed tickers: {failed}")
    if not results:
        return None

    df = pd.concat(results.values(), keys=results.keys(), axis=0)
    df.columns = df.columns.str.lower()
    df = df.rename(columns={"adj close": "close_adjusted"})
    df.index.names = ["ticker", "date"]

    # strip timezones from date level immediately after concat
    df = df.reset_index()
    df["date"] = pd.to_datetime(df["date"], utc=True).dt.tz_localize(None)
    df = df.set_index(["ticker", "date"])

    return df

def get_ticker_info(ticker: str) -> dict:
    _logger.debug(f"Getting info for {ticker}")
    try:
        yf_ticker = yf.Ticker(ticker)
        with contextlib.redirect_stderr(io.StringIO()):
            info = yf_ticker.info
            isin = yf_ticker.isin
        if not info or len(info) <= 1:
            raise ValueError(f"No data returned for {ticker}")
        _logger.debug(f"Info for {ticker} recieved")

        return {
            "ticker": ticker,
            "name": info.get("longName"),
            "asset_type": QUOTE_TYPE_MAP.get(info.get("quoteType", "unknown")),
            "currency": info.get("currency", "XXX"),
            "exchange": info.get("exchange"),
            "country": info.get("country"),
            "sector": info.get("sector", "unknown"),
            "industry": info.get("industry", "unknown"),
            "isin": isin if isin != '-' else None,
        }
    except Exception as e:
        _logger.debug(f"{ticker} is not a valid ticker: {e}")
        raise
    
def fetch_info(tickers: list) -> pd.DataFrame | None:
    _logger.info("Fetching ticker info from yfinance")

    success_count = 0
    failed = []
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = get_ticker_info(ticker)
            success_count += 1
        except Exception as e:
            _logger.warning(f"Skipping {ticker}: {e}")
            failed.append(ticker)

    _logger.info(
        f"Succesfully downloaded ticker info from yfinance for {success_count} tickers"
    )
    if failed:
        _logger.warning(f"Failed tickers: {failed}")
    if not results:
        return None

    df = pd.DataFrame(results.values(), index=list(results.keys()))
    df.index.name = "ticker"
    return df