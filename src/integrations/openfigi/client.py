from src.integrations.base import HTTPClient
from src.logger import get_logger

_logger = get_logger(__name__)

OPENFIGI_BASE_URL = "https://api.openfigi.com/v3"

class OpenFIGIClient(HTTPClient):
    def __init__(self):
        super().__init__(
            base_url=OPENFIGI_BASE_URL,
            headers={"Content-Type": "application/json"},
        )
        
    def map(self, payload: list[dict]) -> list[dict]:
        _logger.debug(f"Sending FIGI mapping request with {len(payload)} items")
        return self.post("mapping", json=payload).json()