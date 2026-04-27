import pandas as pd
from datetime import date, timedelta
from src.data.repositories import get_returns, get_factor_returns
from src.logging.logger import get_logger

_logger = get_logger(__name__)

def load_aligned_data(
    tickers: str | list[str],
    region: str,
    frequency: str='daily',
    start: date=date(2000, 1, 1),
    end=None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    end = end or date.today()+timedelta(days=1)
    if isinstance(tickers, str):
        tickers = [tickers]

    _logger.info(f"Loading aligned data for {tickers} | region={region} frequency={frequency} range={start} to {end}")
    
    factor_rows = get_factor_returns(region, frequency, start, end)
    asset_rows = get_returns(tickers, frequency, start, end)
        
    factors_df = factor_rows.pivot(index="date", columns="factor", values="value")
    asset_df = asset_rows.pivot(index="date", columns="ticker", values="value")
    
    factors_df.index = pd.to_datetime(factors_df.index)
    asset_df.index = pd.to_datetime(asset_df.index)

    aligned = factors_df.join(asset_df, how="inner").dropna()
    _logger.debug(f"Aligned data: {len(aligned)} rows after inner join and dropna")

    if aligned.empty:
        _logger.warning(f"No overlapping data for {tickers} in region={region} — check date range and region match")
        return pd.DataFrame(), pd.DataFrame()

    rf = aligned['rf']
    factor_cols = [c for c in ['mkt', 'smb', 'hml', 'rmw', 'cma', 'mom'] if c in aligned.columns]
    factors = aligned[factor_cols]
    excess_returns = aligned[tickers].subtract(rf, axis=0)

    _logger.info(f"Ready: {len(aligned)} observations, factors={factor_cols}")
    
    return excess_returns, factors