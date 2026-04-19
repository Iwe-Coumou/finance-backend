import pandas as pd
from src.logger import get_logger
from src.data.database import get_session, MacroIndicator
from sqlalchemy.dialects.postgresql import insert

_logger = get_logger(__name__)

def store_macro_data(series_id: str, description: str, data: pd.Series) -> int:
    _logger.debug(f"Storing {series_id}...")
    
    rows = [
        {
            "series_id": series_id,
            "date": date_idx.date(),
            "value": float(value),
            "description": description,
        }
        for date_idx, value in data.items()
    ]

    stmt = (
        insert(MacroIndicator)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["series_id", "date"])
    )

    with get_session() as session:
        result = session.execute(stmt)
        inserted = max(result.rowcount, 0)

    _logger.debug(f"Stored {inserted} new rows for {series_id}")
    return inserted