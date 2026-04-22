from pydantic import BaseModel
from datetime import date

class FactorRegressionResponse(BaseModel):
    ticker: str
    alpha: float
    alpha_tstat: float
    alpha_pvalue: float
    betas: dict[str, float]
    tstats: dict[str, float]
    pvalues: dict[str, float]
    r_squared: float
    r_squared_adj: float
    observations: int
    information_ratio: float
    

class FactorRequest(BaseModel):
    tickers: list[str]
    region: str
    frequency: str="daily"
    start: date=date(2000, 1, 1)
    end: date | None = None
    force_refresh: bool = False  
    
    