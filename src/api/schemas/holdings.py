from pydantic import BaseModel
from datetime import date

class HoldingResponse(BaseModel):
    ticker: str
    weight: float
    quantity: float
    cost_basis: float | None
    snapshot_date: date