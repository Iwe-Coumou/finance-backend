import pandas as pd

def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    daily = (
        prices["close_adjusted"]
        .groupby(level='ticker')
        .pct_change()
        .dropna()
        .rename("value")
        .reset_index()
        .assign(frequency="daily")
    )
    monthly = (
        prices["close_adjusted"]
        .groupby(level="ticker")
        .resample("ME", level="date")
        .last()
        .pct_change()
        .dropna()
        .rename("value")
        .reset_index()
        .assign(frequency="monthly")
    )
    return pd.concat([daily, monthly], ignore_index=True)