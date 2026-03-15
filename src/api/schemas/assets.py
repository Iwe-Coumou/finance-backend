from pydantic import BaseModel

class AssetResponse(BaseModel):
    name: str | None
    asset_type: str
    currency: str | None
    exchange: str | None
    country: str | None
    region: str | None
    sector: str | None
    industry: str | None
    isin: str | None