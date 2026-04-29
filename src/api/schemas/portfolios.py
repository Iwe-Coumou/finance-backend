from pydantic import BaseModel, model_validator, RootModel
from src.api.schemas.holdings import HoldingResponse
from datetime import datetime

class PortfolioResponse(BaseModel):
    id: int
    name: str
    source: str
    created_at: datetime | None
    
class PortfolioWeightsResponse(RootModel[dict[str, float]]):
    @model_validator(mode='after')
    def weights_sum_to_one(self) -> "PortfolioWeightsResponse":
        total = sum(self.root.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Weights must sum to 1.0, got {total:.4f}")
        return self