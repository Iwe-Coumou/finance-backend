import datetime as dt
from sqlalchemy import (
    UniqueConstraint,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    Enum,
    JSON,
    Index,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from src.config import AssetType


class Base(DeclarativeBase):
    pass


class Asset(Base):
    __tablename__ = "assets"

    ticker: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str | None] = mapped_column(String)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3), default="XXX")
    exchange: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    region_override: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(String)
    industry: Mapped[str | None] = mapped_column(String)
    isin: Mapped[str | None] = mapped_column(String, nullable=True)
    figi: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime, onupdate=func.now())


class Prices(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, ForeignKey("assets.ticker"), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    close_adjusted: Mapped[float | None] = mapped_column(Float)
    close_raw: Mapped[float | None] = mapped_column(Float)
    open: Mapped[float | None] = mapped_column(Float)
    high: Mapped[float | None] = mapped_column(Float)
    low: Mapped[float | None] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_price_ticker_data"),
        Index("ix_price_ticker_date", "ticker", "date"),
    )


class Returns(Base):
    __tablename__ = "returns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, ForeignKey("assets.ticker"), nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("ticker", "date", "frequency", name="uq_return_ticker_date_freq"),
        Index("ix_return_ticker_date", "ticker", "date"),
    )


class FactorReturn(Base):
    __tablename__ = "factor_returns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    factor: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    frequency: Mapped[str | None] = mapped_column(String, default="daily")
    region: Mapped[str | None] = mapped_column(String, nullable=False, default="us")

    __table_args__ = (
        UniqueConstraint("factor", "date", "frequency", "region", name="uq_factor_date_freq_region"),
        Index("ix_factor_date", "factor", "date"),
    )


class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    series_id: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    value: Mapped[float | None] = mapped_column(Float)
    description: Mapped[str | None] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint("series_id", "date", name="uq_macro_series_date"),
        Index("ix_macro_series_date", "series_id", "date"),
    )


class EnrichedPosition(Base):
    __tablename__ = "enriched_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, ForeignKey("assets.ticker"), nullable=False)
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    asset_type: Mapped[AssetType | None] = mapped_column(Enum(AssetType))
    geographic_weights: Mapped[dict | None] = mapped_column(JSON)
    sector_weights: Mapped[dict | None] = mapped_column(JSON)

    __table_args__ = (
        UniqueConstraint("ticker", "snapshot_date", name="uq_enriched_ticker_date"),
    )


class RegimeHistory(Base):
    __tablename__ = "regime_history"

    date: Mapped[dt.date] = mapped_column(Date, primary_key=True)
    regime: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, server_default=func.now())


class Fundamentals(Base):
    __tablename__ = "fundamentals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String, ForeignKey("assets.ticker"), nullable=False)
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    market_cap: Mapped[float | None] = mapped_column(Float)
    beta: Mapped[float | None] = mapped_column(Float)
    pe_ratio: Mapped[float | None] = mapped_column(Float)
    eps: Mapped[float | None] = mapped_column(Float)
    dividend_yield: Mapped[float | None] = mapped_column(Float)
    avg_volume: Mapped[float | None] = mapped_column(Float)
    revenue: Mapped[float | None] = mapped_column(Float)
    net_income: Mapped[float | None] = mapped_column(Float)
    debt_to_equity: Mapped[float | None] = mapped_column(Float)
    roe: Mapped[float | None] = mapped_column(Float)
    operating_margin: Mapped[float | None] = mapped_column(Float)
    updated_at: Mapped[dt.datetime | None] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "snapshot_date", name="uq_fundamentals_ticker_date"),
        Index("ix_fundamentals_ticker", "ticker"),
    )


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime | None] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("name", name="uq_portfolio_name"),
    )


class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    portfolio_id: Mapped[int] = mapped_column(Integer, ForeignKey("portfolios.id"), nullable=False)
    ticker: Mapped[str] = mapped_column(String, ForeignKey("assets.ticker"), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    cost_basis: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_date: Mapped[dt.date] = mapped_column(Date, nullable=False)

    __table_args__ = (
        UniqueConstraint("portfolio_id", "ticker", "snapshot_date", name="uq_holding_portfolio_ticker_date"),
        Index("ix_holding_portfolio_date", "portfolio_id", "snapshot_date"),
    )
