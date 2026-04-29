from fastapi import APIRouter, HTTPException
from src.services.currency_interface import get_holdings_eur
from src.api.schemas import HoldingResponse
from src.logging.logger import get_logger
from datetime import datetime

router = APIRouter()
_logger = get_logger(__name__)

@router.get("/", response_model=list[HoldingResponse])
def get_holdings_all(portfolio_id: int | None = None, ticker: str | None = None, snapshot_date: datetime | None = None):
    holdings = get_holdings_eur(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date)
    if holdings.empty:
        _logger.warning(f"No holdings found | portfolio_id={portfolio_id} ticker={ticker} snapshot_date={snapshot_date}")
        raise HTTPException(status_code=404, detail="No holdings found")
    return holdings.to_dict(orient="records")
        