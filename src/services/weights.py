from src.services.currency_interface import get_holdings_eur
from src.data.repositories import get_portfolios
from src.logging import get_logger
import pandas as pd

_logger = get_logger(__name__)

def portfolio_weights(name: str | None = None, source: str | None = None) -> dict[str, float] | None:
    if name or source:
        portfolios = get_portfolios(name=name, source=source)
        if not portfolios:
            _logger.error(f"No portfolios found | name={name} source={source}")
            return None
        frames = [get_holdings_eur(portfolio_id=p.id) for p in portfolios]
        holdings = pd.concat(frames, ignore_index=True)
    else:
        holdings = get_holdings_eur()

    if holdings.empty:
        return None
    holdings['value'] = holdings['quantity'] * holdings['cost_basis']
    total = holdings['value'].sum()
    by_ticker = holdings.groupby('ticker')['value'].sum()
    return {ticker: round(val / total, 2) for ticker, val in by_ticker.items()}

if __name__ == "__main__":
    print(portfolio_weights())