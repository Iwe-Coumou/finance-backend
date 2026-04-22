from src.integrations.fmp import FMPClient
from src.logger import get_logger

_logger = get_logger(__name__)

def get_rate(symbol: str, client: FMPClient) -> float:
    _logger.debug(f"Fetching FOREX rate for {symbol}")
    data = client.get("quote-short", params={"symbol": symbol}).json()
    if not data:
        raise ValueError(f"No FOREX data for {symbol}")
    rate = data[0]['price']
    _logger.debug(f"Rate for {symbol}: {rate}")
    return rate