from src.logger import get_logger
from fredapi import Fred
from src.config import get_env_var

logger = get_logger(__name__)
FRED_API_KEY = get_env_var("FRED_API_KEY", logger=logger)


def main():
    pass


if __name__ == "__main__":
    main()
