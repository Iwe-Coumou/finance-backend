from src.data.repositories import get_holdings_df, get_prices, get_assets
from src.integrations.fmp import get_rate, FMPClient
from src.logger import get_logger
import pandas as pd
from datetime import date

_logger = get_logger(__name__)
_client = FMPClient()

FOREX_SYMBOLS = [
    "USDCAD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "NZDUSD", "USDCNY", "USDMXN", "USDINR"
]

def _get_symbols(currencies: list[str]) -> dict[str, tuple[str, str]]:  
    result = {}
    for currency in set(currencies) - {"USD", "EUR"}:
        for symbol in FOREX_SYMBOLS:
            base, quote = symbol[:3], symbol[3:]
            if currency == base:
                result[currency] = (symbol, "base")
                break
            elif currency == quote:
                result[currency] = (symbol, "quote")
                break
            
    return result
   
def _conversion_map(symbols: dict[str, tuple[str, str]]) -> dict[str, float]:
    eurusd = get_rate("EURUSD", _client)
    rates = {"USD": 1/eurusd, "EUR": 1.0}
    for currency, (symbol, direction) in symbols.items():
        rate = get_rate(symbol, _client)
        usd_rate = rate if direction == "base" else 1/rate
        rates[currency] = usd_rate / eurusd
    return rates


def _convert_to_eur(series: pd.Series, currencies: pd.Series, conversion_map: dict[str, float]) -> pd.Series:
    return series * currencies.map(conversion_map)

def get_holdings_eur(
    portfolio_id: int | None = None,
    ticker: str | None = None,
    snapshot_date: date | None = None,
) -> pd.DataFrame:
    holdings = get_holdings_df(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date)
    currencies = get_assets(tickers=holdings["ticker"].unique().tolist(), cols='currency')
    ticker_currencies = holdings["ticker"].map(currencies["currency"])
    
    c_map = _conversion_map(_get_symbols(currencies["currency"].tolist()))
    holdings["cost_basis"] = _convert_to_eur(holdings["cost_basis"], ticker_currencies, c_map)
    return holdings
    

def get_prices_eur(
    tickers: list[str] | None = None,
    start: date | None = None,
    end: date | None = None
) -> pd.DataFrame:
    prices = get_prices(tickers=tickers, start=start, end=end)
    currencies = get_assets(tickers=prices["ticker"].unique().tolist(), cols="currency")
    
    price_cols = ["close_adjusted", "close_raw", "open", "high", "low"]
    ticker_currencies = prices["ticker"].map(currencies["currency"])
    
    c_map = _conversion_map(_get_symbols(currencies["currency"].tolist()))
    for col in price_cols:
        prices[col] = _convert_to_eur(prices[col], ticker_currencies, c_map)
        
    return prices
    
    