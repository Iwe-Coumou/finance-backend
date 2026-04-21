from src.logger import get_logger
from src.data.database import get_session, PortfolioHolding
from sqlalchemy import select

_logger = get_logger(__name__)

def get_holdings(portfolio_id: int) -> list:
    _logger.debug(f"Fetching holdings | portfolio_id={portfolio_id}")
    with get_session() as session:
        rows = session.execute(
            select(PortfolioHolding)
            .where(PortfolioHolding.portfolio_id == portfolio_id)
        ).scalars().all()
        
    _logger.debug(f"Found {len(rows)} holdings for portfolio_id={portfolio_id}")
    return rows