from fastapi import APIRouter, HTTPException, Query
from src.data.repositories import get_portfolios
from src.services import portfolio_weights, get_portfolio_KPIs
from src.api.schemas import PortfolioResponse, PortfolioWeightsResponse, PortfolioKPIResponse
from src.logging.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)

def _resolve_ids(name: list[str] | None, source: list[str] | None, portfolio_id: list[int] | None) -> list[int]:
    if portfolio_id:
        return portfolio_id
    portfolios = get_portfolios(name=name, source=source)
    if not portfolios:
        raise LookupError(f"No portfolios found | name={name} source={source}")
    return [p.id for p in portfolios]

@router.get("/", response_model=list[PortfolioResponse])
def get_portfolios_all(source: list[str] | None = Query(None), name: list[str] | None = Query(None)):
    portfolios = get_portfolios(name=name, source=source)
    if not portfolios:
        _logger.warning(f"No portfolios found | name={name} source={source}")
        raise HTTPException(status_code=404, detail="No portfolios found")
    return portfolios

@router.get("/weights", response_model=PortfolioWeightsResponse)
def get_portfolio_weights(name: list[str] | None = Query(None), source: list[str] | None = Query(None), portfolio_id: list[int] | None = Query(None), force_refresh: bool = False):
    try:
        ids = _resolve_ids(name, source, portfolio_id) if (name or source or portfolio_id) else None
        weights = portfolio_weights(portfolio_ids=ids, force_refresh=force_refresh)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not weights:
        _logger.warning(f"Portfolio exists but has no holdings | name={name} source={source} portfolio_id={portfolio_id}")
        raise HTTPException(status_code=404, detail="Portfolio has no holdings")
    return PortfolioWeightsResponse(weights)

@router.get("/KPIs", response_model=PortfolioKPIResponse)
def get_kpis(name: list[str] | None = Query(None), source: list[str] | None = Query(None), portfolio_id: list[int] | None = Query(None), force_refresh: bool = False):
    try:
        ids = _resolve_ids(name, source, portfolio_id)
        return get_portfolio_KPIs(portfolio_ids=ids, force_refresh=force_refresh)
    except LookupError as e:
        _logger.warning(f"KPI lookup failed | name={name} source={source} portfolio_id={portfolio_id} | {e}")
        raise HTTPException(status_code=404, detail=str(e))