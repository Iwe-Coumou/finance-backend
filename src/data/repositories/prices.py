from src.logging.logger import get_logger
import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from src.data.database import Prices, get_session
from datetime import date


_logger = get_logger(__name__)

def store_price_data(ticker: str, df: pd.DataFrame) -> int:
    """Store price rows, skipping any that already exist."""
    _logger.debug(f"Storing {len(df)} rows for {ticker}...")

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
    with get_session() as session:
        result = session.execute(stmt)
        rowcount = max(result.rowcount, 0)  # type: ignore[union-attr]
        _logger.debug(f"Stored {rowcount} rows for {ticker}")
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
            _logger.error(f"Failed to store prices for {ticker}: {e}")
            failed.append(ticker)

    _logger.info(f"Stored prices for {success_count}/{len(tickers)} tickers")
    if failed:
        _logger.warning(f"Failed tickers: {failed}")
        
def get_prices(
    tickers: list[str] | None = None,
    start: date | None = None,
    end: date | None = None
) -> pd.DataFrame:
    _logger.debug(f"Fetching prices | tickers={tickers} range={start} to {end}")
    query = select(Prices)
    if tickers is not None:
        query = query.where(Prices.ticker.in_(tickers))
    if start is not None:
        query = query.where(Prices.date >= start)
    if end is not None:
        query = query.where(Prices.date <= end)
    with get_session() as session:
        rows = session.execute(query).scalars().all()
        df = pd.DataFrame([{
            "ticker": r.ticker, "date": r.date, "close_adjusted": r.close_adjusted,
            "close_raw": r.close_raw, "open": r.open, "high": r.high,
            "low": r.low, "volume": r.volume
        } for r in rows])
    _logger.info(f"Fetched {len(df)} price rows | tickers={tickers} range={start} to {end}")
    return df
