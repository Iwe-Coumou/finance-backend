import json
import hashlib
from datetime import date, timedelta
from dataclasses import asdict
from src.data.config import TEST_TICKERS

import redis

from src.services.factor.data_alignment import load_aligned_data
from src.models.factor import run_regressions, FactorRegressionResult
from src.config import get_env_var
from src.logger import get_logger

_logger = get_logger(__name__)
REDIS_URL = get_env_var("REDIS_URL", _logger)

redis_client: redis.Redis = redis.Redis.from_url(REDIS_URL)  # type: ignore[type-arg]

CACHE_TTL = {
    "daily": 60*60*24,
    "monthly": 60*60*24*7
}

def _cache_key(
    tickers: list[str],
    region: str,
    frequency: str,
    start: date,
    end: date,
) -> str:
    raw = f"{sorted(tickers)}:{region}:{frequency}:{start}:{end}"
    digest = hashlib.md5(raw.encode()).hexdigest()[:10]
    return f"factor_result:{digest}"

def get_factor_results(
    tickers: str | list[str],
    region: str,
    frequency: str="daily",
    start: date=date(2000,1,1),
    end=None,
    force_refresh: bool=False
) -> dict[str, FactorRegressionResult]:
    end = end or date.today()+timedelta(days=1)
    if isinstance(tickers, str):
        tickers = [tickers]
        
    cache_key = _cache_key(tickers, region, frequency, start, end)
    _logger.debug(f"Cache key: {cache_key}")
    
    if not force_refresh:
        try:
            cached = redis_client.get(cache_key)
            if cached:
                _logger.info(f"Cache hit for {tickers} | region={region} frequency={frequency}")
                raw = json.loads(cached)  # type: ignore[arg-type]
                return {ticker: FactorRegressionResult(**data) for ticker, data in raw.items()}
        except Exception as e:
            _logger.warning(f"Redis read failed, falling through to regression: {e}")
    
    _logger.info(f"Cache miss for {tickers} | region={region} frequency={frequency} — running regression")
    
    excess_returns, factors = load_aligned_data(tickers, region, frequency, start, end)
    
    if excess_returns.empty:
        _logger.warning(f"No data returned from loader for {tickers}, aborting")
        return {}
    
    results = run_regressions(excess_returns, factors)
    
    try:
        serialized = {ticker: asdict(r) for ticker, r in results.items()}
        redis_client.setex(cache_key, CACHE_TTL[frequency], json.dumps(serialized))
        _logger.debug(f"Cached results for {tickers} with TTL={CACHE_TTL[frequency]}s")
    except Exception as e:
        _logger.warning(f"Redis write failed, results not cached: {e}")
        
    return results

if __name__ == "__main__":
    results = get_factor_results(
        tickers=TEST_TICKERS,
        region="us",
        frequency="daily",
        start=date(2020, 1, 1),
        end=date(2024, 12, 31),
    )

    for ticker, r in results.items():
        print(f"\n{'='*40}")
        print(f"  {ticker}")
        print(f"{'='*40}")
        print(f"  Alpha:        {r.alpha:.6f}  (t={r.alpha_tstat:.2f}, p={r.alpha_pvalue:.3f})")
        print(f"  R²:           {r.r_squared:.3f}  (adj={r.r_squared_adj:.3f})")
        print(f"  Observations: {r.observations}")
        print(f"  Info Ratio:   {r.information_ratio:.3f}")
        print(f"\n  Betas:")
        for factor, beta in r.betas.items():
            t = r.tstats[factor]
            p = r.pvalues[factor]
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
            print(f"    {factor:<6} {beta:>8.4f}  (t={t:.2f}) {sig}")