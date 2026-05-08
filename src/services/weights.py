from src.services.currency_interface import get_holdings_eur
from src.data.repositories import get_portfolios, cache_get, cache_set
from src.logging import get_logger
from datetime import date
import hashlib
import pandas as pd

_logger = get_logger(__name__)

def _cache_key(names: list[str] | None, sources: list[str] | None) -> str:
    raw = f"{sorted(names or [])}:{sorted(sources or [])}:{date.today()}"
    return f"weights:{hashlib.md5(raw.encode()).hexdigest()[:10]}"

def portfolio_weights(names: list[str] | None = None, sources: list[str] | None = None, force_refresh: bool = False) -> dict[str, float] | None:
    cache_key = _cache_key(names, sources)
    if not force_refresh:
        cached = cache_get(cache_key)
        if cached:
            _logger.info(f"Cache hit for portfolio weights | names={names} sources={sources}")
            return cached
        _logger.info(f"Cache miss for portfolio weights | names={names} sources={sources}")
    
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
    
    weights = {ticker: round(val / total, 2) for ticker, val in by_ticker.items()}
    cache_set(cache_key, weights, ttl=60*60*4)
    return weights

if __name__ == "__main__":
    print(portfolio_weights())