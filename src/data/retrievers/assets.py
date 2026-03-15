import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.data.database.db import get_engine, Asset
from src.logger import get_logger
from src.config import AssetType

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

    with Session(get_engine()) as session:
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
            
            
def main():
    print(get_assets())
    
if __name__ == "__main__":
    main()
                
            
    
    