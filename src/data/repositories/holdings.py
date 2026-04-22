import pandas as pd
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
        session.expunge_all()
    _logger.debug(f"Found {len(rows)} holdings for portfolio_id={portfolio_id}")
    return rows

def get_holdings_df(
    portfolio_id: int | None = None,
    ticker: str | None = None,
    snapshot_date: date | None = None,
) -> pd.DataFrame:
    with get_session() as session:
        query = select(PortfolioHolding)
        if portfolio_id is not None:
            query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
        if ticker is not None:
            query = query.where(PortfolioHolding.ticker == ticker)
        if snapshot_date is not None:
            query = query.where(PortfolioHolding.snapshot_date == snapshot_date)
        rows = session.execute(query).scalars().all()
        df = pd.DataFrame([{
            "portfolio_id": r.portfolio_id,
            "ticker": r.ticker,
            "weight": r.weight,
            "quantity": r.quantity,
            "cost_basis": r.cost_basis,
            "snapshot_date": r.snapshot_date
        } for r in rows])
    _logger.debug(f"Found {len(df)} holdings for portfolio_id={portfolio_id}")
    return df
