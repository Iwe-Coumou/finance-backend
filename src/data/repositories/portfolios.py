from src.logger import get_logger
from src.data.database import Portfolio, get_session
from sqlalchemy import select
import pandas as pd

_logger = get_logger(__name__)

def get_portfolios(name: str | None = None, source: str | None = None) -> list[Portfolio]:
    _logger.debug(f"Fetching portfolios | name={name} source={source}")
    query = select(Portfolio)
    if name:
        query = query.where(Portfolio.name == name)
    if source:
        query = query.where(Portfolio.source == source)
        
    with get_session() as session:
        rows = session.execute(query).scalars().all()
    _logger.debug(f"Found {len(rows)} portfolios")  
    return rows