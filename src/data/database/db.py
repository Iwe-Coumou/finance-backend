from sqlalchemy import (
    UniqueConstraint,
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Float,
    Date,
    Enum,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.config import DB_URL, AssetType

from src.logger import get_logger

logger = get_logger(__name__)

try:
    engine = create_engine(DB_URL)
    logger.info(f"Connected to database")
except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    raise


class Base(DeclarativeBase):
    pass


class Asset(Base):
    """One row per known ticker. Static metadata"""

    __tablename__ = "assets"

    ticker = Column(String, primary_key=True)
    name = Column(String)
    asset_type = Column(Enum(AssetType), nullable=False)
    currency = Column(String(3), default="XXX")
    exchange = Column(String)
    country = Column(String)
    sector = Column(String)
    industry = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class Prices(Base):
    """Daily price history. One row per ticker per date"""

    __tablename__ = "prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("assets.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    close_adjusted = Column(Float)
    close_raw = Column(Float)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_price_ticker_data"),
        Index("ix_price_ticker_date", "ticker", "date"),
    )


class Returns(Base):
    """Computed returns. Derived from prices, cached here"""

    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("assets.ticker"), nullable=False)
    date = Column(Date, nullable=False)
    daily_return = Column(Float)
    monthly_return = Column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_return_ticker_date"),
        Index("ix_return_ticker_date", "ticker", "date"),
    )


class FactorReturn(Base):
    """Fama-French factor returns. One row per factor per date"""

    __tablename__ = "factor_returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factor = Column(String, nullable=False)  # 'mkt', 'smb', 'hml', 'rmw', 'cma', 'mom'
    date = Column(Date, nullable=False)
    value = Column(Float)
    frequency = Column(String, default="daily")  # 'daily' or 'monthly'

    __table_args__ = (
        UniqueConstraint("factor", "date", "frequency", name="uq_factor_date_freq"),
        Index("ix_factor_date", "factor", "date"),
    )


class MacroIndicator(Base):
    """Macro time series from FRED. One row per series per date."""

    __tablename__ = "macro_indicators"

    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String, nullable=False)  # FRED series ID e.g. "T10Y2Y"
    date = Column(Date, nullable=False)
    value = Column(Float)
    description = Column(String)

    __table_args__ = (
        UniqueConstraint("series_id", "date", name="uq_macro_series_date"),
        Index("ix_macro_series_date", "series_id", "date"),
    )


class EnrichedPosition(Base):
    """Cached output of the enrichment pipeline per ticker."""

    __tablename__ = "enriched_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String, ForeignKey("assets.ticker"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    asset_type = Column(Enum(AssetType))
    geographic_weights = Column(JSON)  # {"US": 0.62, "EU": 0.22, ...}
    sector_weights = Column(JSON)  # {"Technology": 0.28, ...}

    __table_args__ = (
        UniqueConstraint("ticker", "snapshot_date", name="uq_enriched_ticker_date"),
    )


class RegimeHistory(Base):
    """Daily regime classification history."""

    __tablename__ = "regime_history"
    date = Column(Date, primary_key=True)
    regime = Column(Integer, nullable=False)  # raw state index (0-3)
    label = Column(String)  # e.g. "Bull / Low Vol"
    confidence = Column(Float)  # probability of assigned state
    created_at = Column(DateTime, server_default=func.now())


def create_tables():
    """Create all tables. Safe to run multiple times."""
    logger.info("Creating tables...")
    try:
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def get_engine():
    logger.debug("Enging requested")
    return engine


if __name__ == "__main__":
    create_tables()
