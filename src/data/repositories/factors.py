from src.data.database import FactorReturn, get_session
from src.logger import get_logger
from datetime import date
import pandas as pd
from sqlalchemy import select

_logger = get_logger(__name__)

def get_last_stored_factor_data(frequency: str, region: str) -> date | None:
    with get_session() as session:
        result = session.execute(
            select(FactorReturn.date)
            .where(FactorReturn.frequency == frequency)
            .where(FactorReturn.region == region)
            .order_by(FactorReturn.date.desc())
            .limit(1)
        ).scalar()
    _logger.debug(f"Last stored {frequency} factor date for {region}: {result}")
    return result


def store_factors(df: pd.DataFrame, frequency: str = "daily", region: str='us') -> int:
    _logger.debug(f"Storing {frequency} factors for {region}...")
    inserted = 0

    with get_session() as session:
        for date_idx, row in df.iterrows():
            for factor_name, value in row.items():
                if pd.isna(value):
                    continue
                session.add(
                    FactorReturn(
                        factor=factor_name,
                        date=date_idx.date(),
                        value=float(value),
                        frequency=frequency,
                        region=region,
                    )
                )
                inserted += 1

    _logger.debug(f"Stored {inserted} factor rows for {region} ({frequency})")
    return inserted

def get_factor_returns(region: str, frequency: str, start: date, end: date) -> pd.DataFrame:
    _logger.debug(f"Fetching factor returns | region={region} frequency={frequency} range={start} to {end}")
    with get_session() as session:
        rows = session.execute(
            select(FactorReturn.date, FactorReturn.factor, FactorReturn.value)
            .where(FactorReturn.region == region)
            .where(FactorReturn.frequency == frequency)
            .where(FactorReturn.date >= start)
            .where(FactorReturn.date <= end)
        ).all()
    df = pd.DataFrame(rows, columns=["date", "factor", "value"])
    _logger.debug(f"Fetched {len(df)} factor returns")
    return df