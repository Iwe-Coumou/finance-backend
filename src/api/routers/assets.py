from fastapi import APIRouter, HTTPException
from src.data.retrievers.assets import get_assets

router = APIRouter()

@router.get("/")
def list_assets():
    return get_assets().to_dict(orient="records")

@router.get("/{ticker}")
def get_asset(ticker: str):
    df = get_assets(tickers=ticker)
    if df.empty:
        raise HTTPException(status_code=404, detail="Asset not found")
    return df.iloc[0].to_dict()