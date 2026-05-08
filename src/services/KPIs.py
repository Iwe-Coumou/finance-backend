import pandas as pd
from src.logging import get_logger
from datetime import date
from src.services import get_holdings_eur, get_prices_eur, portfolio_weights, fetch_and_enrich
from src.data.repositories import get_returns, get_factor_returns, cache_get, cache_set
from src.data.repositories import state
import hashlib

_logger = get_logger(__name__)

def total_return(holdings: pd.DataFrame, current_price: pd.DataFrame) -> tuple[float, float]:
    cost_value = (holdings['quantity']*holdings['cost_basis']).sum()
    current_value = (holdings['quantity']*holdings['ticker'].map(current_price.set_index("ticker")['close_adjusted'])).sum()
    raw = current_value - cost_value
    pct = raw / cost_value
    return raw, pct

def annualized_return(pct_return: float, days_held: int) -> float:
    return (1+pct_return) ** (365 / days_held) - 1
    
def ytd_return(holdings: pd.DataFrame, ytd_start_prices: pd.DataFrame, current_prices: pd.DataFrame) -> tuple[float, float]:
    start_value = (holdings["quantity"]*holdings["ticker"].map(ytd_start_prices.set_index("ticker")["close_adjusted"])).sum()
    current_value = (holdings["quantity"]*holdings["ticker"].map(current_prices.set_index("ticker")["close_adjusted"])).sum()
    raw = current_value - start_value
    pct = raw / start_value
    return raw, pct

def volatility(returns: pd.Series) -> float:
    return returns.std() * (252 ** 0.5)
    
def sharpe_ratio(returns: pd.Series, risk_free_rate: pd.Series) -> float:
    rf_aligned = risk_free_rate.reindex(returns.index).ffill()
    excess = returns - rf_aligned
    return (excess.mean() / excess.std()) * (252 ** 0.5)

def sortino_ratio(returns: pd.Series, risk_free_rate: pd.Series) -> float:
    rf_aligned = risk_free_rate.reindex(returns.index).ffill()
    excess = returns - rf_aligned
    downside = excess[excess < 0].std()
    return (excess.mean() / downside) * (252 ** 0.5)

def max_drawdown(returns: pd.Series) -> tuple[float, date, date]:
    cumulative = (1 + returns).cumprod()
    peak = cumulative.cummax()
    drawdown = (cumulative - peak) / peak
    trough_idx = drawdown.idxmin()
    peak_idx = cumulative[:trough_idx].idxmax()
    return drawdown.min(), peak_idx, trough_idx  # index values are already dates

def beta(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    cov = portfolio_returns.cov(benchmark_returns)
    return cov / benchmark_returns.var()


def _cache_key(portfolio_ids: list[int], benchmark_ticker: str) -> str:
    raw = f"ids:{sorted(portfolio_ids)}:{benchmark_ticker}:{date.today()}"
    return f"kpis:{hashlib.md5(raw.encode()).hexdigest()[:10]}"

def get_portfolio_KPIs(portfolio_ids: list[int], benchmark_ticker: str = "SPY", force_refresh: bool = False):
    _logger.info(f"Computing portfolio KPIs | portfolio_ids={portfolio_ids}")

    cache_key = _cache_key(portfolio_ids, benchmark_ticker)

    if not force_refresh:
        cached = cache_get(cache_key)
        if cached:
            _logger.info(f"Cache hit for portfolio KPIs | portfolio_ids={portfolio_ids}")
            return cached
        _logger.info(f"Cache miss for portfolio KPIs | portfolio_ids={portfolio_ids}")

    holdings_all = get_holdings_eur(portfolio_id=portfolio_ids, all_snapshots=True)
    if holdings_all.empty:
        raise LookupError("No holdings found for portfolio")
    _logger.debug(f"portfolio_ids={portfolio_ids} | holdings_all shape={holdings_all.shape}")
        
    tickers = list(holdings_all["ticker"].unique())
    last_sync = state.get("last_sync_date")
    if not last_sync or date.fromisoformat(last_sync) < date.today():
        _logger.info("Data not synced today, running fetch_and_enrich")
        fetch_and_enrich(tickers=tickers)
    
    # latest and earliest holdings
    latest = holdings_all.sort_values("snapshot_date").groupby("ticker").last().reset_index()
    earliest = holdings_all.sort_values("snapshot_date").groupby("ticker").first().reset_index()
    start_date = earliest["snapshot_date"].min().date()
    
    # price data
    prices = get_prices_eur(tickers + [benchmark_ticker])
    current_prices = prices.sort_values("date").groupby("ticker").last().reset_index()
    
    # return data
    returns = get_returns(tickers, "daily", start_date, date.today())
    if returns.empty:
        raise LookupError("No return data found for portfolio tickers")
    
    # portfolio weights
    weights = portfolio_weights(portfolio_ids=portfolio_ids, force_refresh=force_refresh)
    _logger.debug(f"Portfolio weights: {weights}")
    
    factors = get_factor_returns(region="us", frequency="daily", start=start_date, end=date.today())
    rf_series = factors[factors["factor"] == 'rf'].set_index("date")["value"]
    
    _logger.info(f"Fetched {len(holdings_all)} holdings accross {len(tickers)} tickers | start_date={start_date}")
    # KPIS
    
    raw_return, pct_return = total_return(holdings=latest, current_price=current_prices)
    days_held = (date.today() - start_date).days
    ann_return = annualized_return(pct_return=pct_return, days_held=days_held) if days_held > 30 else None

    
    benchmark_prices = prices[(prices["ticker"] == benchmark_ticker) & (prices["date"] >= start_date)].sort_values("date")
    if benchmark_prices.empty:
        raise LookupError(f"No price data found for benchmark {benchmark_ticker}")
    
    
    benchmark_start_price = benchmark_prices["close_adjusted"].iloc[0]
    benchmark_current_price = current_prices[current_prices["ticker"] == benchmark_ticker]["close_adjusted"].iloc[0]
    _logger.debug(f"Benchmark {benchmark_ticker} | start_price={benchmark_start_price:.4f} current_price={benchmark_current_price:.4f}")
    
    benchmark_return = (benchmark_current_price - benchmark_start_price) / benchmark_start_price
    vs_benchmark = pct_return - benchmark_return
    
    ytd_start = date(date.today().year, 1, 1)
    ytd_start_prices = prices[prices["date"] >= ytd_start].sort_values("date").groupby("ticker").first().reset_index()

    raw_return_ytd, pct_return_ytd = ytd_return(holdings=latest, ytd_start_prices=ytd_start_prices, current_prices=current_prices)
    
    returns_wide = returns.pivot(index="date", columns="ticker", values="value")
    _logger.debug(f"Returns matrix shape: {returns_wide.shape} | date range: {returns_wide.index.min()} to {returns_wide.index.max()}")
    
    portfolio_returns = returns_wide.mul(weights).sum(axis=1)
    _logger.debug(f"Portfolio returns: {portfolio_returns.isna().sum()} NaN values out of {len(portfolio_returns)} days")
    _logger.debug(f"RF series: {len(rf_series)} days | overlap with portfolio returns: {portfolio_returns.index.isin(rf_series.index).sum()} days")
    
    vol = volatility(returns=portfolio_returns)
    if rf_series.empty:
        _logger.warning("No RF data available for date range — sharpe and sortino will be None")
        sharpe = None
        sortino = None
    else:
        sharpe = sharpe_ratio(returns=portfolio_returns, risk_free_rate=rf_series)
        sortino = sortino_ratio(returns=portfolio_returns, risk_free_rate=rf_series)
    drawdown, dd_start, dd_end = max_drawdown(returns=portfolio_returns)
    
    portfolio_value = (latest["quantity"]*latest["ticker"].map(current_prices.set_index("ticker")["close_adjusted"])).sum()
    num_holdings = len(latest)
    
    benchmark_returns = get_returns(tickers=[benchmark_ticker], frequency="daily", start=start_date, end=date.today())
    benchmark_returns_series = benchmark_returns.set_index("date")["value"]
    beta_val = beta(portfolio_returns=portfolio_returns, benchmark_returns=benchmark_returns_series)
    
    _logger.info("KPI comptutation complete")
    kpis = {
        "portfolio_value": portfolio_value,
        "num_holdings": num_holdings,
        "raw_return": raw_return,
        "pct_return": pct_return,
        "annualized_return": ann_return,
        "vs_benchmark": vs_benchmark,
        "ytd_raw": raw_return_ytd,
        "ytd_pct": pct_return_ytd,
        "volatility": vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": drawdown,
        "max_drawdown_start": dd_start,
        "max_drawdown_end": dd_end,
        "beta": beta_val,
    }
    
    serialized = {
        k: v.isoformat() if isinstance(v, date) else v
        for k, v in kpis.items()
    }
    cache_set(cache_key, serialized, ttl=60*60*4)
    return kpis
    

    
    