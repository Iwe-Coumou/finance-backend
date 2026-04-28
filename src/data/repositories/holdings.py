import pandas as pd
from src.logging.logger import get_logger
from src.data.database import get_session, PortfolioHolding, Portfolio
from src.data.repositories import get_portfolio
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

_logger = get_logger(__name__)

def get_holdings(
    portfolio_id: int | None = None,
    ticker: str | None = None,
    snapshot_date: datetime | None = None,
    all_snapshots: bool = False,
) -> list[PortfolioHolding]:
    _logger.debug(f"Fetching holdings | portfolio_id={portfolio_id}")
    query = select(PortfolioHolding)

    if portfolio_id is not None:
        query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
    if ticker is not None:
        query = query.where(PortfolioHolding.ticker == ticker)
    if not all_snapshots:
        if snapshot_date is not None:
            query = query.where(PortfolioHolding.snapshot_date == snapshot_date)
        else:
            query = (query
                .distinct(PortfolioHolding.portfolio_id, PortfolioHolding.ticker)
                .order_by(PortfolioHolding.portfolio_id, PortfolioHolding.ticker, PortfolioHolding.snapshot_date.desc())
            )
    with get_session() as session:
        rows = session.execute(query).scalars().all()
        session.expunge_all()
    _logger.debug(f"Found {len(rows)} holdings for portfolio_id={portfolio_id}")
    return rows

def get_holdings_df(
    portfolio_id: int | None = None,
    ticker: str | None = None,
    snapshot_date: datetime | None = None,
    all_snapshots: bool = False,
) -> pd.DataFrame:
    with get_session() as session:
        query = select(PortfolioHolding)
        if portfolio_id is not None:
            query = query.where(PortfolioHolding.portfolio_id == portfolio_id)
        if ticker is not None:
            query = query.where(PortfolioHolding.ticker == ticker)
        if not all_snapshots:
            if snapshot_date is not None:
                query = query.where(PortfolioHolding.snapshot_date == snapshot_date)
            else:
                query = (query
                    .distinct(PortfolioHolding.portfolio_id, PortfolioHolding.ticker)
                    .order_by(PortfolioHolding.portfolio_id, PortfolioHolding.ticker, PortfolioHolding.snapshot_date.desc())
                )
        rows = session.execute(query).scalars().all()
        df = pd.DataFrame([{
            "portfolio_id": r.portfolio_id,
            "ticker": r.ticker,
            "quantity": r.quantity,
            "cost_basis": r.cost_basis,
            "snapshot_date": r.snapshot_date
        } for r in rows])
    _logger.debug(f"Found {len(df)} holdings for portfolio_id={portfolio_id}")
    return df

def get_holding(
    portfolio_id: int,
    ticker: str,
    snapshot_date: datetime | None = None,
    all_snapshots: bool = False,
) -> PortfolioHolding | list[PortfolioHolding] | None:
    _logger.debug(f"Fetching holding | portfolio_id={portfolio_id} ticker={ticker}")
    query = (select(PortfolioHolding)
        .where(PortfolioHolding.portfolio_id == portfolio_id)
        .where(PortfolioHolding.ticker == ticker)
    )
    if not all_snapshots:
        if snapshot_date is not None:
            query = query.where(PortfolioHolding.snapshot_date == snapshot_date)
        else:
            query = (query
                .distinct(PortfolioHolding.portfolio_id, PortfolioHolding.ticker)
                .order_by(PortfolioHolding.portfolio_id, PortfolioHolding.ticker, PortfolioHolding.snapshot_date.desc())
            )
    with get_session() as session:
        if all_snapshots:
            rows = session.execute(query).scalars().all()
            session.expunge_all()
            _logger.debug(f"Found {len(rows)} snapshots | portfolio_id={portfolio_id} ticker={ticker}")
            return list(rows)
        row = session.execute(query).scalar_one_or_none()
        if row is not None:
            session.expunge(row)
    if row is not None:
        _logger.debug(f"Found holding | portfolio_id={portfolio_id} ticker={ticker}")
    else:
        _logger.warning(f"Holding not found | portfolio_id={portfolio_id} ticker={ticker}")
    return row

def write_holding(
    portfolio_id: int,
    ticker: str,
    quantity: float,
    cost_basis: float,
):
    _logger.debug(f"Inserting holding to portfolio {portfolio_id} for {ticker}")
    stmt = (insert(PortfolioHolding)
            .values(
                portfolio_id=portfolio_id,
                ticker=ticker,
                quantity=float(quantity),
                cost_basis=float(cost_basis),
                snapshot_date=datetime.now()
            )
            .on_conflict_do_nothing()
    )
    
    with get_session() as session:
        result = session.execute(stmt)
        session.commit()
    _logger.info(f"Added holding to portfolio {portfolio_id} for {ticker}")