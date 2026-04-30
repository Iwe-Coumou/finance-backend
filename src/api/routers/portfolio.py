from fastapi import APIRouter, HTTPException, Query
from src.data.repositories import get_portfolios
from src.services import portfolio_weights, get_portfolio_KPIs
from src.api.schemas import PortfolioResponse, PortfolioWeightsResponse, PortfolioKPIResponse
from src.logging.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)

@router.get("/", response_model=list[PortfolioResponse])
def get_portfolios_all(source: list[str] | None = Query(None), name: list[str] | None = Query(None)):
    portfolios = get_portfolios(name=name, source=source)
    if not portfolios:
        _logger.warning(f"No portfolios found | name={name} source={source}")
        raise HTTPException(status_code=404, detail="No portfolios found")
    return portfolios

@router.get("/weights", response_model=PortfolioWeightsResponse)
def get_portfolio_weights(name: list[str] | None = Query(None), source: list[str] | None = Query(None)):
    try:
        weights = portfolio_weights(names=name, sources=source)
    except LookupError:
        raise HTTPException(status_code=404, detail="No portfolio found")
    if not weights:
        _logger.warning(f"Portfolio exists but has no holdings | name={name} source={source}")
        raise HTTPException(status_code=404, detail="Portfolio has no holdings")
    return PortfolioWeightsResponse(weights)

@router.get("/KPIs", response_model=PortfolioKPIResponse)
def get_kpis(name: list[str] | None = Query(None), source: list[str] | None = Query(None)):
    try:
        return get_portfolio_KPIs(names=name, sources=source)
    except LookupError as e:
        _logger.warning(f"KPI lookup failed | name={name} source={source} | {e}")
        raise HTTPException(status_code=404, detail=str(e))