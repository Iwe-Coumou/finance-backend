from fastapi import APIRouter, HTTPException
from src.api.schemas.factors import FactorRegressionResponse, FactorRequest
from src.services.factor import get_factor_results
from src.data.repositories import get_holdings
from datetime import date

router = APIRouter()

@router.post("/analyze", response_model=dict[str, FactorRegressionResponse])
def get_factor_result(request: FactorRequest, portfolio_id: int | None = None):
    if portfolio_id is None and request.tickers is None:
        raise HTTPException(status_code=400, detail="Provide either tickers or portfolio_id")
    if portfolio_id is not None and request.tickers is not None:
        raise HTTPException(status_code=400, detail="Provide either tickers or portfolio_id, not both")
    
    if portfolio_id is not None:
        tickers = [h.ticker for h in get_holdings(portfolio_id=portfolio_id)]
    else:
        tickers = request.tickers
    
    factor_results = get_factor_results(
        tickers=tickers,
        region=request.region,
        frequency=request.frequency,
        start=request.start,
        end=request.end,
        force_refresh=request.force_refresh,
    )
    
    if not factor_results:
        raise HTTPException(status_code=404, detail="No factor results")
    
    return factor_results
    