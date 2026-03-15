import yfinance as yf
from src.logger import get_logger
from src.data.config import TEST_TICKERS
import pandas as pd
from datetime import date, timedelta
import contextlib
import io
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert
from src.data.database.db import Asset, Prices, Returns, get_engine
from src.config import QUOTE_TYPE_MAP

logger = get_logger(__name__)


def get_ticker_prices(
    ticker: str, start: date = date(2000, 1, 1), end=None
) -> pd.DataFrame:
    end = end or date.today() + timedelta(days=1)

    logger.debug(f"Getting data for {ticker}...")
    try:
        yf_ticker = yf.Ticker(ticker)
        with contextlib.redirect_stderr(io.StringIO()):
            history = yf_ticker.history(start=start, end=end, auto_adjust=False)
        if history.empty:
            raise ValueError(f"No data returned for {ticker}")
        logger.debug(f"Data for {ticker} recieved")
        return history
    except Exception as e:
        logger.debug(f"{ticker} is not a valid ticker: {e}")
        raise


def get_ticker_info(ticker: str) -> dict:
    logger.debug(f"Getting info for {ticker}")
    try:
        yf_ticker = yf.Ticker(ticker)
        with contextlib.redirect_stderr(io.StringIO()):
            info = yf_ticker.info
            isin = yf_ticker.isin
        if not info or len(info) <= 1:
            raise ValueError(f"No data returned for {ticker}")
        logger.debug(f"Info for {ticker} recieved")

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
        logger.debug(f"{ticker} is not a valid ticker: {e}")
        raise


def fetch_prices(
    tickers: list, start: date = date(2000, 1, 1), end=None
) -> pd.DataFrame | None:
    end = end or date.today() + timedelta(days=1)

    logger.info("Downloading data from yfinance...")

    succes_count = 0
    failed = []
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = get_ticker_prices(ticker, start, end)
            succes_count += 1
        except Exception as e:
            logger.warning(f"Skipping {ticker}: {e}")
            failed.append(ticker)

    logger.info(f"Succesfully downloaded data from yfinance for {succes_count} tickers")
    if failed:
        logger.warning(f"Failed tickers: {failed}")
    if not results:
        return None

    df = pd.concat(results.values(), keys=results.keys(), axis=0)
    df.columns = df.columns.str.lower()
    df = df.rename(columns={"adj close": "close_adjusted"})
    df.index.names = ["ticker", "date"]

    return df


def fetch_info(tickers: list) -> pd.DataFrame | None:
    logger.info("Fetching ticker info from yfinance")

    success_count = 0
    failed = []
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = get_ticker_info(ticker)
            success_count += 1
        except Exception as e:
            logger.warning(f"Skipping {ticker}: {e}")
            failed.append(ticker)

    logger.info(
        f"Succesfully downloaded ticker info from yfinance for {success_count} tickers"
    )
    if failed:
        logger.warning(f"Failed tickers: {failed}")
    if not results:
        return None

    df = pd.DataFrame(results.values(), index=list(results.keys()))
    df.index.name = "ticker"
    return df


def compute_returns(prices: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Compute daily and monthly returns from adjusted close prices
    """
    daily = (
        prices["close_adjusted"]
        .groupby(level='ticker')
        .pct_change()
        .dropna()
        .rename("value")
        .reset_index()
        .assign(frequency="daily")
    )
    monthly = (
        prices["close_adjusted"]
        .groupby(level="ticker")
        .resample("ME", level="date")
        .last()
        .pct_change()
        .dropna()
        .rename("value")
        .reset_index()
        .assign(frequency="monthly")
    )
    return pd.concat([daily, monthly], ignore_index=True)


def store_price_data(ticker: str, df: pd.DataFrame) -> int:
    """Store price rows, skipping any that already exist."""
    engine = get_engine()
    logger.debug(f"Storing {len(df)} rows for {ticker}...")

    rows = [
        {
            "ticker": ticker,
            "date": date_idx.date(),  # type: ignore
            "close_adjusted": float(row["close_adjusted"])
            if pd.notna(row["close_adjusted"])
            else None,
            "close_raw": float(row["close"]) if pd.notna(row["close"]) else None,
            "open": float(row["open"]) if pd.notna(row["open"]) else None,
            "high": float(row["high"]) if pd.notna(row["high"]) else None,
            "low": float(row["low"]) if pd.notna(row["low"]) else None,
            "volume": float(row["volume"]) if pd.notna(row["volume"]) else None,
        }
        for date_idx, row in df.iterrows()
    ]
    stmt = (
        insert(Prices)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["ticker", "date"])
    )
    with Session(engine) as session:
        result = session.execute(stmt)
        session.commit()
        rowcount = max(result.rowcount, 0)  # type: ignore[union-attr]
        logger.debug(f"Stored {rowcount} rows for {ticker}")
        return rowcount


def store_all_prices(tickers: list, df: pd.DataFrame):
    success_count = 0
    failed = []

    for ticker in tickers:
        try:
            ticker_df = df.loc[ticker]
            inserted = store_price_data(ticker, ticker_df)
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to store prices for {ticker}: {e}")
            failed.append(ticker)

    logger.info(f"Stored prices for {success_count}/{len(tickers)} tickers")
    if failed:
        logger.warning(f"Failed tickers: {failed}")


def store_asset_data(df: pd.DataFrame) -> int:
    engine = get_engine()
    logger.debug(f"Storing {len(df)} assets...")
    rows = df.to_dict(orient="records")
    stmt = (insert(Asset)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["ticker"],
            set_={
                "name": insert(Asset).excluded.name,
                "currency": insert(Asset).excluded.currency,
                "exchange": insert(Asset).excluded.exchange,
                "country": insert(Asset).excluded.country,
                "sector": insert(Asset).excluded.sector,
                "industry": insert(Asset).excluded.industry,
                "isin": insert(Asset).excluded.isin,
                "updated_at": func.now(),               
            }
        )
    )
    with Session(engine) as session:
        result = session.execute(stmt)
        session.commit()
        rowcount = max(result.rowcount, 0)  # type: ignore[union-attr]
        logger.debug(f"Stored/updated {rowcount} assets")
        return rowcount


def store_return_data(ticker: str, df: pd.DataFrame) -> int:
    engine = get_engine()
    rows = [
        {
            "ticker": ticker,
            "date": row["date"].date() if hasattr(row["date"], "date") else row["date"],
            "frequency": row["frequency"],
            "value": float(row["value"]) if pd.notna(row["value"]) else None
        }
        for _, row in df.iterrows()
    ]
    stmt = (
        insert(Returns)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["ticker", "date", "frequency"])
    )
    with Session(engine) as session:
        result = session.execute(stmt)
        session.commit()
        return max(result.rowcount, 0)  # type: ignore[union-attr]


def store_all_returns(tickers: list, df: pd.DataFrame) -> None:
    success_count = 0
    failed = []

    for ticker in tickers:
        try:
            ticker_df = df[df["ticker"] == ticker]
            inserted = store_return_data(ticker, ticker_df)
            logger.debug(f"Stored {inserted} rows for {ticker}")
            success_count += 1
        except Exception as e:
            logger.error(f"Failed to store returns for {ticker}: {e}")
            failed.append(ticker)

    logger.info(f"Stored returns for {success_count}/{len(tickers)} tickers")
    if failed:
        logger.warning(f"Failed tickers: {failed}")


def fetch_and_store(tickers: list, start: date = date(2000, 1, 1), end=None) -> None:
    logger.info("Starting fetch and store pipeline...")

    prices_df = fetch_prices(tickers)
    info_df = fetch_info(tickers)

    if prices_df is None:
        logger.error("No price data fetched, aborting pipeline")
        return
    if info_df is None:
        logger.error("No asset info fetched, aborting pipeline")
        return

    returns_df = compute_returns(prices_df)

    store_asset_data(info_df)
    store_all_prices(tickers, prices_df)
    store_all_returns(tickers, returns_df)

    logger.info("Pipeline complete")


if __name__ == "__main__":
    fetch_and_store(TEST_TICKERS)
