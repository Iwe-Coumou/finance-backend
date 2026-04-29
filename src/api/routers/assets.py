from fastapi import APIRouter, HTTPException
from src.data.repositories import get_assets
from src.api.schemas import AssetResponse
from src.logging.logger import get_logger

router = APIRouter()
_logger = get_logger(__name__)

@router.get("/", response_model=list[AssetResponse])
def list_assets():
    return get_assets().to_dict(orient="records")

@router.get("/{ticker}", response_model=AssetResponse)
def get_asset(ticker: str) -> AssetResponse:
    df = get_assets(tickers=ticker)
    if df.empty:
        _logger.warning(f"Asset not found | ticker={ticker}")
        raise HTTPException(status_code=404, detail="Asset not found")
    return df.iloc[0].to_dict()