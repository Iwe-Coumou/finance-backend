from pydantic import BaseModel, model_validator, RootModel
from datetime import datetime, date

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
    

class PortfolioKPIResponse(BaseModel):
    portfolio_value: float
    num_holdings: int
    raw_return: float
    pct_return: float
    annualized_return: float
    vs_benchmark: float
    ytd_raw: float
    ytd_pct: float
    volatility: float
    sharpe: float | None
    sortino: float | None
    max_drawdown: float
    max_drawdown_start: date
    max_drawdown_end: date
    beta: float
