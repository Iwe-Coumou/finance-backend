import pandas as pd
from sqlalchemy import select
from src.data.database import Asset, get_session
from src.logger import get_logger
from src.config import AssetType
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func, update

_logger = get_logger(__name__)

def get_assets(
    tickers: str | list[str] | None = None,
    asset_types: AssetType | list[AssetType] | None = None,
    cols: str | list[str] | None = None,
) -> pd.DataFrame:
    if isinstance(tickers, str):
        tickers = [tickers]
    if isinstance(cols, str):
        cols = [cols]
    if cols and 'ticker' not in cols:
        cols = ['ticker']+cols
    if isinstance(asset_types, AssetType):
        asset_types = [asset_types]

    _logger.debug(
        f"get_assets called | tickers={tickers} asset_types={asset_types} cols={cols}"
    )

    with get_session() as session:
        if cols:
            col_attrs = []
            for c in cols:
                attr = getattr(Asset, c, None)
                if attr is None:
                    raise ValueError(f"Asset has no column '{c}'")
                col_attrs.append(attr)
            query = select(*col_attrs)

            if tickers:
                query = query.where(Asset.ticker.in_(tickers))
            if asset_types:
                query = query.where(Asset.asset_type.in_(asset_types))

            rows = session.execute(query).all()
            df = pd.DataFrame(rows, columns=cols)

        else:
            query = select(Asset)

            if tickers:
                query = query.where(Asset.ticker.in_(tickers))
            if asset_types:
                query = query.where(Asset.asset_type.in_(asset_types))

            rows = session.execute(query).scalars().all()  # scalars() gives Asset objects
            df = pd.DataFrame([{
                c.name: getattr(row, c.name)
                for c in Asset.__table__.columns
            } for row in rows])

    _logger.debug(f"Returning DataFrame with {len(df)} rows, cols={df.columns.tolist()}")
    
    df = df.set_index("ticker")
    if "asset_type" in df.columns:
        df["asset_type"] = df["asset_type"].map(lambda x: x.value if x else None)
    
    _logger.info(f"Fetched {len(df)} assets | tickers={tickers if tickers is not None else "All"} asset_types={asset_types if asset_types is not None else "All"} cols={cols if cols is not None else "All"}")
    return df
            

def store_asset_data(df: pd.DataFrame) -> int:
    _logger.debug(f"Storing {len(df)} assets...")
    rows = df.to_dict(orient="records")
    stmt = (insert(Asset)
        .values(rows)
        .on_conflict_do_update(
            index_elements=["ticker"],
            set_={
                "name": insert(Asset).excluded.name,
                "currency": insert(Asset).excluded.currency,
                "exchange": insert(Asset).excluded.exchange,
                "country": insert(Asset).excluded.country,
                "sector": insert(Asset).excluded.sector,
                "industry": insert(Asset).excluded.industry,
                "isin": insert(Asset).excluded.isin,
                "updated_at": func.now(),               
            }
        )
    )
    with get_session() as session:
        result = session.execute(stmt)
        rowcount = max(result.rowcount, 0)  # type: ignore[union-attr]
        _logger.debug(f"Stored/updated {rowcount} assets")
        return rowcount
    
def update_figis(figi_map: dict[str, str], force: bool = False) -> None:
    with get_session() as session:
        for ticker, figi in figi_map.items():
            asset = session.execute(
                select(Asset).where(Asset.ticker == ticker)
            ).scalar_one_or_none()

            if not asset:
                _logger.warning(f"[{ticker}] Asset not found")
                continue
            if asset.figi and not force:
                _logger.debug(f"[{ticker}] FIGI already set to '{asset.figi}', skipping")
                continue

            asset.figi = figi
            asset.updated_at = func.now()
            _logger.debug(f"[{ticker}] FIGI set to '{figi}'")
            
def update_asset_region(ticker: str, region: str, force: bool = False) -> None:
    with get_session() as session:
        asset = session.execute(
            select(Asset).where(Asset.ticker == ticker)
        ).scalar_one_or_none()

        if not asset:
            _logger.warning(f"[{ticker}] Asset not found")
            return
        if str(asset.region) and not force:
            _logger.debug(f"[{ticker}] Region already set to '{asset.region}', skipping")
            return

        session.execute(
            update(Asset)
            .where(Asset.ticker == ticker)
            .values(region=region, updated_at=func.now())
        )
    _logger.debug(f"[{ticker}] Region set to '{region}'")
    
def update_isins(isin_map: dict[str, str], force: bool = False) -> None:
    with get_session() as session:
        for ticker, isin in isin_map.items():
            asset = session.execute(
                select(Asset).where(Asset.ticker == ticker)
            ).scalar_one_or_none()

            if not asset:
                _logger.warning(f"[{ticker}] Asset not found")
                continue
            if asset.isin and not force:
                _logger.debug(f"[{ticker}] ISIN already set to '{asset.isin}', skipping")
                continue

            asset.isin = isin
            asset.updated_at = func.now()
            _logger.debug(f"[{ticker}] ISIN set to '{isin}'")