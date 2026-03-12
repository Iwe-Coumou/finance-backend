from dotenv import load_dotenv
import os
from enum import Enum
from src.logger import get_logger


def get_env_var(var: str, logger=None) -> str:
    if logger is None:
        logger = get_logger(__name__)

    load_dotenv()
    logger.debug(f"Getting environment variable: {var}...")
    result = os.getenv(var)
    if result is None:
        logger.error(f"Environment variable '{var}' not set")
        raise ValueError(f"environment variable '{var}' not set")
    logger.debug(f"Environment variable '{var}' retrieved successfully")
    return result


class AssetType(Enum):
    EQUITY = "equity"
    ETF = "etf"
    BOND = "bond"
    CASH = "cash"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    INDEX = "index"
    FUTURE = "future"
    FOREX = "forex"
    WARRANT = "warrant"
    RIGHT = "right"
    UNKNOWN = "unknown"


QUOTE_TYPE_MAP = {
    "EQUITY": AssetType.EQUITY,
    "ETF": AssetType.ETF,
    "MUTUALFUND": AssetType.MUTUAL_FUND,
    "CRYPTO": AssetType.CRYPTO,
    "INDEX": AssetType.INDEX,
    "FUTURE": AssetType.FUTURE,
    "CURRENCY": AssetType.FOREX,
    "WARRANT": AssetType.WARRANT,
    "RIGHT": AssetType.RIGHT,
}
