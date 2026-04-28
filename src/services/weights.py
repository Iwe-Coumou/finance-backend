from src.services.currency_interface import get_holdings_eur
from src.data.repositories import get_portfolio
from src.logging import get_logger
import pandas as pd

_logger = get_logger(__name__)

def portfolio_weights(portfolio_id: int | None=None, portfolio_name: str | None=None) -> dict[str, float]:
    if not portfolio_id and not portfolio_name:
        _logger.error(f"Need either portfolio id or portfolio name to get weights")
    

    if portfolio_name:
        portfolio = get_portfolio(name=portfolio_name)
        if portfolio is None:
            _logger.error(f"No portfolio found | name={portfolio_name}")
        
        portfolio_id = portfolio.id
    
    holdings = get_holdings_eur(portfolio_id=portfolio_id)
    holdings['value'] = holdings['quantity']*holdings['cost_basis']
    total = holdings['value'].sum()
    return dict(zip(holdings['ticker'], round(holdings['value']/total,2)))
    
if __name__ == "__main__":
    print(portfolio_weights(portfolio_name="equity"))