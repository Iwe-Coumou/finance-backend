from src.services.currency_interface import get_holdings_eur
from src.data.repositories import cache_get, cache_set
from src.logging import get_logger
from datetime import date
import hashlib
import pandas as pd

_logger = get_logger(__name__)

def _cache_key(portfolio_ids: list[int] | None) -> str:
    if portfolio_ids is not None:
        raw = f"ids:{sorted(portfolio_ids)}:{date.today()}"
    else:
        raw = f"all:{date.today()}"
    return f"weights:{hashlib.md5(raw.encode()).hexdigest()[:10]}"

def portfolio_weights(portfolio_ids: list[int] | None = None, force_refresh: bool = False) -> dict[str, float] | None:
    cache_key = _cache_key(portfolio_ids)
    if not force_refresh:
        cached = cache_get(cache_key)
        if cached:
            _logger.info(f"Cache hit for portfolio weights | portfolio_ids={portfolio_ids}")
            return cached
        _logger.info(f"Cache miss for portfolio weights | portfolio_ids={portfolio_ids}")

    if portfolio_ids is not None:
        frames = [get_holdings_eur(portfolio_id=pid) for pid in portfolio_ids]
        holdings = pd.concat(frames, ignore_index=True)
    else:
        holdings = get_holdings_eur()

    if holdings.empty:
        _logger.warning(f"No holdings available to compute weights | portfolio_ids={portfolio_ids}")
        return None
    holdings['value'] = holdings['quantity'] * holdings['cost_basis']
    total = holdings['value'].sum()
    by_ticker = holdings.groupby('ticker')['value'].sum()

    weights = {ticker: round(val / total, 2) for ticker, val in by_ticker.items()}
    cache_set(cache_key, weights, ttl=60*60*4)
    return weights

if __name__ == "__main__":
    print(portfolio_weights())
