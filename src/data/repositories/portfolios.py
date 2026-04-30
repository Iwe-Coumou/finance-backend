from src.logging.logger import get_logger
from src.data.database import Portfolio, get_session
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
import pandas as pd

_logger = get_logger(__name__)

def get_portfolios(name: list[str] | None = None, source: list[str] | None = None) -> list[Portfolio]:
    _logger.debug(f"Fetching portfolios | name={name} source={source}")
    query = select(Portfolio)
    if name:
        query = query.where(Portfolio.name.in_(name))
    if source:
        query = query.where(Portfolio.source.in_(source))
        
    with get_session() as session:
        rows = session.execute(query).scalars().all()
        session.expunge_all()
    _logger.debug(f"Found {len(rows)} portfolios")
    return rows

def get_portfolio(name: str | None = None, source: str | None = None) -> Portfolio | None:
    _logger.debug(f"Fetching portfolio | name={name} source={source}")
    query = select(Portfolio)
    if name:
        query = query.where(Portfolio.name == name)
    if source:
        query = query.where(Portfolio.source == source)

    with get_session() as session:
        row = session.execute(query).scalar_one_or_none()
        if row is not None:
            session.expunge(row)

    if row is not None:
        _logger.debug(f"Found portfolio | name={name} source={source}")
    else:
        _logger.warning(f"Portfolio not found | name={name} source={source}")

    return row

def write_portfolio(name: str, source: str):
    _logger.debug(f"Creating portfolio | name={name} source={source}")
    stmt = (insert(Portfolio)
            .values(name=name, source=source)
            .on_conflict_do_nothing(constraint="uq_portfolio_name_source")
    )
    
    with get_session() as session:
        result = session.execute(stmt)
        session.commit()
        if result.rowcount == 0:
            _logger.warning(f"Portfolio already exists | name={name} source={source}")
            return 
    _logger.info(f"Added Portfolio | name={name} source={source}")
