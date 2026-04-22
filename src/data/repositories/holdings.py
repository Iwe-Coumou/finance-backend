from src.logger import get_logger
from src.data.database import get_session, PortfolioHolding
from sqlalchemy import select
from datetime import date

_logger = get_logger(__name__)

def get_holdings(
    portfolio_id: int | None = None, 
    ticker: str | None = None,
    snapshot_date: date | None = None,
) -> list[PortfolioHolding]:
    _logger.debug(f"Fetching holdings | portfolio_id={portfolio_id}")
    query = select(PortfolioHolding)
    
    if portfolio_id is not None:
        query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
    if ticker is not None:
        query = query.where(PortfolioHolding.ticker == ticker)
    if snapshot_date is not None:
        query = query.where(PortfolioHolding.snapshot_date == snapshot_date)
    with get_session() as session:
        rows = session.execute(query).scalars().all()
        
    _logger.debug(f"Found {len(rows)} holdings for portfolio_id={portfolio_id}")
    return rows
