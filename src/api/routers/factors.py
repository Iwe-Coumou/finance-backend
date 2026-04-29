from fastapi import APIRouter, HTTPException
from src.api.schemas.factors import FactorRegressionResponse, FactorRequest
from src.services.factor import get_factor_results
from src.data.repositories import get_holdings
from src.logging.logger import get_logger
from datetime import date

router = APIRouter()
_logger = get_logger(__name__)

@router.post("/analyze", response_model=dict[str, FactorRegressionResponse])
def get_factor_result(request: FactorRequest, portfolio_id: int | None = None):
    if portfolio_id is None and request.tickers is None:
        _logger.warning("Factor analyze request missing both tickers and portfolio_id")
        raise HTTPException(status_code=400, detail="Provide either tickers or portfolio_id")
    if portfolio_id is not None and request.tickers is not None:
        _logger.warning(f"Factor analyze request has both tickers and portfolio_id | portfolio_id={portfolio_id}")
        raise HTTPException(status_code=400, detail="Provide either tickers or portfolio_id, not both")

    if portfolio_id is not None:
        tickers = [h.ticker for h in get_holdings(portfolio_id=portfolio_id)]
        _logger.debug(f"Resolved {len(tickers)} tickers from portfolio_id={portfolio_id}")
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
        _logger.warning(f"No factor results | tickers={tickers} region={request.region} frequency={request.frequency}")
        raise HTTPException(status_code=404, detail="No factor results")

    return factor_results
    