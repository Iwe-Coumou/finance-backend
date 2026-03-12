from sqlalchemy import desc
from src.logger import get_logger
from fredapi import Fred
from src.config import get_env_var
from datetime import date
from src.data.database.db import MacroIndicator, get_engine
from sqlalchemy.orm import Session

logger = get_logger(__name__)


SERIES = {
    "T10Y2Y": "Yield curve slope (10y minus 2y treasury",
    "BAMLC0A0CM": "IG corporate bond credit spread",
    "CPIAUCSL": " CPI - consumer price index (inflation)",
    "UNRATE": "US unemployment rate",
    "VIXCLS": "CBOE VIX volatility index",
    "T10YIE": "10-year breakeven inflation rate",
    "DPCREDIT": "Discount window primary credit rate",
}


def fetch_and_store_macros(start: date = date(2000, 1, 1)) -> None:
    fred = Fred(api_key=get_env_var("FRED_API_KEY", logger=logger))
    engine = get_engine()

    for series_id, description in SERIES.items():
        logger.info(f"Fetching {series_id} - {description}")
        try:
            data = fred.get_series(series_id, observation_start=start)
            data = data.dropna()

            inserted = 0
            with Session(engine) as session:
                for date_idx, value in data.items():
                    existing = (
                        session.query(MacroIndicator)
                        .filter_by(
                            series_id=series_id,
                            date=date_idx.date(),
                        )
                        .first()
                    )

                    if existing is None:
                        session.add(
                            MacroIndicator(
                                series_id=series_id,
                                date=date_idx.date(),
                                value=float(value),
                                description=description,
                            )
                        )
                        inserted += 1

                session.commit()
            logger.info(f"Done. {inserted} new rows inserted.")

        except Exception as e:
            logger.error("Failed to fetch {series_id}: {e}")


if __name__ == "__main__":
    fetch_and_store_macros()


def main():
    pass


if __name__ == "__main__":
    main()
