from fastapi import APIRouter, HTTPException
from src.services import fetch_and_enrich
from src.data.config import TEST_TICKERS
from src.data.database.db import get_engine
from src.api.schemas import AssetResponse
from src.logging.logger import get_logger
from sqlalchemy import text

router = APIRouter()

_logger = get_logger(__name__)

@router.get("/sync")
def sync():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        _logger.error(f"Sync aborted: database unavailable: {str(e).splitlines()[0]}")
        raise HTTPException(status_code=503, detail="Database unavailable, sync aborted.")

    try:
        _logger.info("Starting sync process...")
        fetch_and_enrich(TEST_TICKERS)
        _logger.info("Sync process completed successfully.")
        return {"message": "Data sync and enrichment completed successfully."}
    except Exception as e:
        _logger.error(f"Error during sync process: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the sync process.")

