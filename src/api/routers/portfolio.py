from fastapi import APIRouter, HTTPException
from src.data.repositories import get_portfolios
from src.services.weights import portfolio_weights
from src.api.schemas import PortfolioResponse, PortfolioWeightsResponse
from src.logging.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)

@router.get("/", response_model=list[PortfolioResponse])
def get_portfolios_all(source: str | None = None, name: str | None = None):
    portfolios = get_portfolios(name=name, source=source)
    if not portfolios:
        _logger.warning(f"No portfolios found | name={name} source={source}")
        raise HTTPException(status_code=404, detail="No portfolios found")
    return portfolios

@router.get("/weights", response_model=PortfolioWeightsResponse)
def get_portfolio_weights(name: str | None = None, source: str | None = None):
    try:
        weights = portfolio_weights(name=name, source=source)
    except LookupError:
        raise HTTPException(status_code=404, detail="No portfolio found")
    if not weights:
        _logger.warning(f"Portfolio exists but has no holdings | name={name} source={source}")
        raise HTTPException(status_code=404, detail="Portfolio has no holdings")
    return PortfolioWeightsResponse(weights)
