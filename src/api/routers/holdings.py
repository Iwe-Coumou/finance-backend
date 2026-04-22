from fastapi import APIRouter, HTTPException
from src.data.repositories import get_holdings
from src.api.schemas import HoldingResponse
from datetime import date

router = APIRouter()

@router.get("/", response_model=list[HoldingResponse])
def get_holdings_all(portfolio_id: int | None = None, ticker: str | None = None, snapshot_date: date | None = None):
    holdings = get_holdings(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date)
    if not holdings:
        raise HTTPException(status_code=404, detail="No holdings found")
    return holdings
        