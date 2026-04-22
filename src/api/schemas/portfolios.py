from pydantic import BaseModel
from src.api.schemas.holdings import HoldingResponse
from datetime import datetime

class PortfolioResponse(BaseModel):
    id: int
    name: str
    source: str
    created_at: datetime | None