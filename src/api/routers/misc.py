from fastapi import APIRouter, HTTPException
from src.data.repositories import state
from src.services import fetch_and_enrich
from src.data.config import TEST_TICKERS
from src.data.database.db import get_engine
from src.api.schemas import AssetResponse
from src.logging.logger import get_logger
from sqlalchemy import text
from datetime import date

router = APIRouter()

_logger = get_logger(__name__)

@router.get("/sync")
def sync(force_refresh: bool = False):
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        _logger.error(f"Sync aborted: database unavailable: {str(e).splitlines()[0]}")
        raise HTTPException(status_code=503, detail="Database unavailable, sync aborted.")
    
    last_sync = state.get("last_sync_date")
    if last_sync and date.fromisoformat(last_sync) == date.today() and not force_refresh:
        return {"message": "Already synced today."}

    try:
        _logger.info("Starting sync process...")
        fetch_and_enrich(TEST_TICKERS)
        _logger.info("Sync process completed successfully.")
        if last_sync is None:
            state.set("last_sync_date", date.today().isoformat())
        else:
            state.update("last_sync_date", date.today().isoformat())
        return {"message": "Data sync and enrichment completed successfully."}
    except Exception as e:
        _logger.error(f"Error during sync process: {e}")
        raise HTTPException(status_code=500, detail="An error occurred during the sync process.")

