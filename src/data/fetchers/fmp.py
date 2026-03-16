from src.logger import get_logger
from src.config import get_env_var
from src.data.database.db import get_engine

_logger = get_logger(__name__)
API_KEY = get_env_var("FMP_API_KEY")