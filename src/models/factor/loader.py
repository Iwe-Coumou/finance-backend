import pandas as pd
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.data.database.db import FactorReturn, Returns, get_engine
from src.logger import get_logger

_logger = get_logger(__name__)

def load_aligned_data(
    tickers: str | list[str],
    region: str,
    frequency: str='daily',
    start: date=date(2000, 1, 1),
    end=None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    end = end or date.today()+timedelta(days=1)
    if isinstance(tickers, str):
        tickers = [tickers]
        
    return_col = Returns.daily_return if frequency == "daily" else Returns.monthly_return 
    
    engine = get_engine()
    
    with Session(engine) as session:
        factor_rows = session.execute(
            select(FactorReturn.date, FactorReturn.factor, FactorReturn.value)
            .where(FactorReturn.region == region)
            .where(FactorReturn.frequency == frequency)
            .where(FactorReturn.date >= start)
            .where(FactorReturn.date <= end)
        ).all()
        
        asset_rows = session.execute(
            select(Returns.ticker, Returns.date, return_col)
            .where(Returns.ticker.in_(tickers))
            .where(Returns.date >= start)
            .where(Returns.date <= end)
        ).all()
        
    factors_df = (
        pd.DataFrame(factor_rows, columns=["date", "factor", "value"])
        .pivot(index="date", columns="factor", values="value")
    )
    factors_df.index = pd.to_datetime(factors_df.index)
    factors_df.columns.name = None
    
    col_name = "daily_return" if frequency == "daily" else "monthly_return"
    asset_df = (
        pd.DataFrame(asset_rows, columns=["ticker", "date", col_name])
        .pivot(index="date", columns="ticker", values=col_name)
    )
    asset_df.index = pd.to_datetime(asset_df.index)
    asset_df.columns.name = None
    
    aligned = factors_df.join(asset_df, how="inner").dropna()
    
    rf = aligned['rf']
    factor_cols = [c for c in ['mkt', 'smb', 'hml', 'rmw', 'cma', 'mom'] if c in aligned.columns]
    factors = aligned[factor_cols]
    excess_returns = aligned[tickers].subtract(rf, axis=0)
    
    return excess_returns, factors

