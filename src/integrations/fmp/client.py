from src.integrations.base import HTTPClient
from src.config import get_env_var
from src.logger import get_logger

_logger = get_logger(__name__)

FMP_BASE_URL = "https://financialmodelingprep.com/stable"

class FMPClient(HTTPClient):
    def __init__(self):
        super().__init__(
            base_url=FMP_BASE_URL,
            api_key=get_env_var("FMP_API_KEY", logger=_logger),
            api_key_param="apikey",
        )