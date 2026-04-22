from fastapi import APIRouter, HTTPException
from src.services.currency_interface import get_holdings_eur
from src.api.schemas import HoldingResponse
from datetime import date

router = APIRouter()

@router.get("/", response_model=list[HoldingResponse])
def get_holdings_all(portfolio_id: int | None = None, ticker: str | None = None, snapshot_date: date | None = None):
    holdings = get_holdings_eur(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date)
    if holdings.empty:
        raise HTTPException(status_code=404, detail="No holdings found")
    return holdings.to_dict(orient="records")
        