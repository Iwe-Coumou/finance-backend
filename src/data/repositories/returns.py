from src.data.database import get_session, Returns
from src.logger import get_logger
import pandas as pd
from sqlalchemy.dialects.postgresql import insert

_logger = get_logger(__name__)

def store_return_data(ticker: str, df: pd.DataFrame) -> int:
    _logger.debug(f"Storing {len(df)} return rows for {ticker}...")
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
    with get_session() as session:
        result = session.execute(stmt)
        return max(result.rowcount, 0)  # type: ignore[union-attr]


def store_all_returns(tickers: list, df: pd.DataFrame) -> None:
    success_count = 0
    failed = []

    for ticker in tickers:
        try:
            ticker_df = df[df["ticker"] == ticker]
            inserted = store_return_data(ticker, ticker_df)
            _logger.debug(f"Stored {inserted} rows for {ticker}")
            success_count += 1
        except Exception as e:
            _logger.error(f"Failed to store returns for {ticker}: {e}")
            failed.append(ticker)

    _logger.info(f"Stored returns for {success_count}/{len(tickers)} tickers")
    if failed:
        _logger.warning(f"Failed tickers: {failed}")