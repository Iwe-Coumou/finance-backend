from dotenv import load_dotenv
import os
from enum import Enum

load_dotenv()

DB_URL = os.getenv("DB_URL")


class AssetType(Enum):
    EQUITY = "equity"
    ETF = "etf"
    BOND = "bond"
    CASH = "cash"
