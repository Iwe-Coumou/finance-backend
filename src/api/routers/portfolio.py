from fastapi import APIRouter, HTTPException
from src.data.repositories import get_portfolios
from src.api.schemas import PortfolioResponse

router = APIRouter()

@router.get("/", response_model=list[PortfolioResponse])
def get_portfolios_all(source: str | None = None):
    portfolios =  get_portfolios(source=source)
    if not portfolios:
        raise HTTPException(status_code=404, detail="No portfolios found")
    return portfolios

@router.get("/{name}", response_model=PortfolioResponse)
def get_portfolio(name: str):
    portfolio = get_portfolios(name=name)
    if not portfolio:
        raise HTTPException(status_code=404, detail="No portfolio found")
    return portfolio[0]