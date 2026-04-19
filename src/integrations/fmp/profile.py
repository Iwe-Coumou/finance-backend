from src.integrations.fmp import FMPClient
from src.logger import get_logger

_logger = get_logger(__name__)

def get_profile(ticker: str, client: FMPClient) -> dict:
    _logger.debug(f"Fetching FMP profile for {ticker}")
    data = client.get("profile", params={"symbol": ticker}).json()
    if not data:
        raise ValueError(f"No profile data for {ticker}")
    return data[0]