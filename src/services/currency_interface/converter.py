from src.data.repositories import get_holdings_df, get_prices, get_assets
from src.integrations.fmp import get_rate, FMPClient
from src.logging.logger import get_logger
import pandas as pd
from datetime import date, datetime

_logger = get_logger(__spec__.name if __spec__ else __name__)
_client = FMPClient()

FOREX_SYMBOLS = [
    "USDCAD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCHF", "NZDUSD", "USDCNY", "USDMXN", "USDINR"
]

def _get_symbols(currencies: list[str]) -> dict[str, tuple[str, str]]:
    result = {}
    unsupported = []
    for currency in set(currencies) - {"USD", "EUR"}:
        matched = False
        for symbol in FOREX_SYMBOLS:
            base, quote = symbol[:3], symbol[3:]
            if currency == base:
                result[currency] = (symbol, "base")
                matched = True
                break
            elif currency == quote:
                result[currency] = (symbol, "quote")
                matched = True
                break
        if not matched:
            unsupported.append(currency)
    if unsupported:
        _logger.warning(f"No forex symbol found for currencies: {unsupported}")
    _logger.debug(f"Resolved forex symbols: {result}")
    return result

def _conversion_map(symbols: dict[str, tuple[str, str]]) -> dict[str, float]:
    eurusd = get_rate("EURUSD", _client)
    _logger.debug(f"EURUSD rate: {eurusd:.6f}")
    rates = {"USD": 1/eurusd, "EUR": 1.0}
    for currency, (symbol, direction) in symbols.items():
        rate = get_rate(symbol, _client)
        usd_rate = rate if direction == "base" else 1/rate
        rates[currency] = usd_rate / eurusd
        _logger.debug(f"{currency} -> EUR rate: {rates[currency]:.6f} (via {symbol})")
    return rates


def _convert_to_eur(series: pd.Series, currencies: pd.Series, conversion_map: dict[str, float]) -> pd.Series:
    return series * currencies.map(conversion_map)

def get_holdings_eur(
    portfolio_id: int | None = None,
    ticker: str | None = None,
    snapshot_date: datetime | None = None,
    all_snapshots: bool = False,
) -> pd.DataFrame:
    _logger.info(f"Converting holdings to EUR | portfolio_id={portfolio_id} ticker={ticker}")
    holdings = get_holdings_df(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date, all_snapshots=all_snapshots)
    currencies = get_assets(tickers=holdings["ticker"].unique().tolist(), cols='currency')
    ticker_currencies = holdings["ticker"].map(currencies["currency"])

    c_map = _conversion_map(_get_symbols(currencies["currency"].tolist()))
    holdings["cost_basis"] = _convert_to_eur(holdings["cost_basis"], ticker_currencies, c_map)
    _logger.info(f"Converted {len(holdings)} holdings to EUR")
    return holdings

def get_holding_eur(
    portfolio_id: int,
    ticker: str,
    snapshot_date: datetime | None = None,
    all_snapshots: bool = False,
) -> pd.DataFrame:
    _logger.info(f"Converting holding to EUR | portfolio_id={portfolio_id} ticker={ticker}")
    holding = get_holdings_df(portfolio_id=portfolio_id, ticker=ticker, snapshot_date=snapshot_date, all_snapshots=all_snapshots)
    if holding.empty:
        _logger.warning(f"Holding not found | portfolio_id={portfolio_id} ticker={ticker}")
        return holding
    currencies = get_assets(tickers=[ticker], cols='currency')
    ticker_currencies = holding["ticker"].map(currencies["currency"])

    c_map = _conversion_map(_get_symbols(currencies["currency"].tolist()))
    holding["cost_basis"] = _convert_to_eur(holding["cost_basis"], ticker_currencies, c_map)
    _logger.info(f"Converted holding to EUR | portfolio_id={portfolio_id} ticker={ticker}")
    return holding


def get_prices_eur(
    tickers: list[str] | None = None,
    start: date | None = None,
    end: date | None = None
) -> pd.DataFrame:
    _logger.info(f"Converting prices to EUR | tickers={tickers} range={start} to {end}")
    prices = get_prices(tickers=tickers, start=start, end=end)
    currencies = get_assets(tickers=prices["ticker"].unique().tolist(), cols="currency")

    price_cols = ["close_adjusted", "close_raw", "open", "high", "low"]
    ticker_currencies = prices["ticker"].map(currencies["currency"])

    c_map = _conversion_map(_get_symbols(currencies["currency"].tolist()))
    for col in price_cols:
        prices[col] = _convert_to_eur(prices[col], ticker_currencies, c_map)

    _logger.info(f"Converted {len(prices)} price rows to EUR for {prices['ticker'].unique().tolist()}")
    return prices


if __name__ == "__main__":
    tickers = ["AAPL", "INFY.NS"]
    start = date(2024, 1, 1)
    end = date(2024, 1, 10)

    prices_before = get_prices(tickers=tickers, start=start, end=end)
    print("=== Before conversion ===")
    print(prices_before[["ticker", "date", "close_adjusted"]].to_string())

    prices_after = get_prices_eur(tickers=tickers, start=start, end=end)
    print("\n=== After conversion (EUR) ===")
    print(prices_after[["ticker", "date", "close_adjusted"]].to_string())
