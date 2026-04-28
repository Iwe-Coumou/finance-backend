from pydantic import BaseModel
from datetime import datetime

class HoldingResponse(BaseModel):
    ticker: str
    quantity: float
    cost_basis: float | None
    snapshot_date: datetime