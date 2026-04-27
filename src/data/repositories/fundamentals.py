import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from src.data.database import Fundamentals, get_session
from src.logging.logger import get_logger
from datetime import date

_logger = get_logger(__name__)


def store_fundamentals(df: pd.DataFrame, snapshot_date: date) -> int:
    _logger.debug(f"Storing fundamentals for {len(df)} tickers...")
    rows = df.reset_index(drop=True)
    rows["snapshot_date"] = snapshot_date
    rows = rows.where(pd.notna(rows), None).to_dict(orient="records")

    stmt = (
        insert(Fundamentals)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["ticker", "snapshot_date"],
            set_={
                "market_cap": insert(Fundamentals).excluded.market_cap,
                "beta": insert(Fundamentals).excluded.beta,
                "pe_ratio": insert(Fundamentals).excluded.pe_ratio,
                "eps": insert(Fundamentals).excluded.eps,
                "dividend_yield": insert(Fundamentals).excluded.dividend_yield,
                "avg_volume": insert(Fundamentals).excluded.avg_volume,
                "revenue": insert(Fundamentals).excluded.revenue,
                "net_income": insert(Fundamentals).excluded.net_income,
                "debt_to_equity": insert(Fundamentals).excluded.debt_to_equity,
                "roe": insert(Fundamentals).excluded.roe,
                "operating_margin": insert(Fundamentals).excluded.operating_margin,
                "updated_at": insert(Fundamentals).excluded.updated_at,
            }
        )
    )
    with get_session() as session:
        result = session.execute(stmt)
        rowcount = max(result.rowcount, 0)  # type: ignore[union-attr]
    _logger.info(f"Stored/updated fundamentals for {rowcount} tickers | snapshot_date={snapshot_date}")
    return rowcount
