from src.services.currency_interface import get_holdings_eur
from src.data.repositories import get_portfolios
from src.logging import get_logger
import pandas as pd

_logger = get_logger(__name__)

def portfolio_weights(names: list[str] | None = None, sources: list[str] | None = None) -> dict[str, float] | None:
    if names or sources:
        portfolios = get_portfolios(name=names, source=sources)
        if not portfolios:
            _logger.error(f"No portfolios found | names={names} sources={sources}")
            raise LookupError(f"No portfolio found | names={names} sources={sources}")
        frames = [get_holdings_eur(portfolio_id=p.id) for p in portfolios]
        holdings = pd.concat(frames, ignore_index=True)
    else:
        holdings = get_holdings_eur()

    if holdings.empty:
        _logger.warning(f"No holdings available to compute weights | names={names} sources={sources}")
        return None
    holdings['value'] = holdings['quantity'] * holdings['cost_basis']
    total = holdings['value'].sum()
    by_ticker = holdings.groupby('ticker')['value'].sum()
    return {ticker: round(val / total, 2) for ticker, val in by_ticker.items()}

if __name__ == "__main__":
    print(portfolio_weights())