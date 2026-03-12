import pandas as pd
import requests
import zipfile
import io
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.data.database.db import FactorReturn, get_engine
from src.logger import get_logger

logger = get_logger(__name__)

DATASETS = {
    "daily": {
        "ff5": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
        "mom": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip",
    },
    "monthly": {
        "ff5": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip",
        "mom": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip",
    },
}

FACTOR_COLUMN_MAP = {
    "Mkt-RF": "mkt",
    "SMB": "smb",
    "HML": "hml",
    "RMW": "rmw",
    "CMA": "cma",
    "Mom": "mom",
}


def download_french_csv(url: str) -> pd.DataFrame:
    logger.info(f"Fetching {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        csv_filename = [f for f in z.namelist() if f.lower().endswith(".csv")][0]
        logger.debug(f"Found CSV in zip: {csv_filename}")
        with z.open(csv_filename) as f:
            raw = f.read().decode("utf-8", errors="ignore")

        lines = raw.split("\n")

        header_line = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if ("Mkt-RF" in stripped or "Mom" in stripped) and stripped.startswith(","):
                header_line = i
                logger.debug(f"Header found at line {i}: {stripped[:60]}")
                break

        if header_line is None:
            raise ValueError(f"Could not find header line in {url}")

        logger.info(f"Header at line {header_line}, scanning for data bounds")

        data_start = header_line + 1
        end_line = len(lines)
        found_data = None
        for i in range(data_start, end_line):
            stripped = lines[i].strip()
            if stripped and stripped[0].isdigit():
                found_data = True
            elif found_data and not stripped:
                end_line = i
                break
            elif found_data and stripped and not stripped[0].isdigit():
                end_line = i
                break

        logger.debug(f"Data range: lines {data_start}-{end_line}")

        data_str = "\n".join(lines[header_line:end_line])
        df = pd.read_csv(io.StringIO(data_str), index_col=0)
        df.index = df.index.astype(str).str.strip()
        df.columns = df.columns.str.strip()

        logger.info(f"Loaded Dataframe: {df.shape} from {csv_filename}")
        return df


def parse_index(df: pd.DataFrame, frequency: str) -> pd.DataFrame:
    if frequency == "daily":
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
    else:
        df.index = pd.to_datetime(df.index, format="%Y%m") + pd.offsets.MonthEnd(0)
    df.index.name = "date"
    return df


def fetch_factors(
    start: date = date(2000, 1, 1), frequency: str = "daily"
) -> pd.DataFrame:
    urls = DATASETS[frequency]

    logger.info(f"Downloading FF5 {frequency}...")
    ff5 = download_french_csv(urls["ff5"])
    logger.info(f"Downloading momentum {frequency}...")
    mom = download_french_csv(urls["mom"])

    combined = ff5.join(mom, how="inner")
    combined = combined.rename(columns=FACTOR_COLUMN_MAP)
    combined = combined.drop(columns=["RF"], errors="ignore")

    keep = [c for c in FACTOR_COLUMN_MAP.values() if c in combined.columns]
    combined = combined[keep]

    combined = combined.apply(pd.to_numeric, errors="coerce") / 100
    combined = parse_index(combined, frequency)

    combined = combined[combined.index >= pd.Timestamp(start)]
    combined = combined.dropna()

    return combined


def get_last_stored_factor_data(frequency: str) -> date | None:
    engine = get_engine()
    with Session(engine) as session:
        result = session.execute(
            select(FactorReturn.date)
            .where(FactorReturn.frequency == frequency)
            .order_by(FactorReturn.date.desc())
            .limit(1)
        ).scalar()
        return result


def store_factors(df: pd.DataFrame, frequency: str = "daily") -> int:
    engine = get_engine()
    inserted = 0

    with Session(engine) as session:
        for date_idx, row in df.iterrows():
            for factor_name, value in row.items():
                if pd.isna(value):
                    continue
                session.add(
                    FactorReturn(
                        factor=factor_name,
                        date=date_idx.date(),
                        value=float(value),
                        frequency=frequency,
                    )
                )
                inserted += 1
        session.commit()

    return inserted


def fetch_and_store_factors(
    start: date = date(2000, 1, 1), frequency: str = "daily"
) -> None:
    last_date = get_last_stored_factor_data(frequency)
    incremental = last_date is not None
    if incremental:
        start = last_date + timedelta(days=1)

    logger.info(f"Fetching {frequency} factor returns from {start}...")
    df = fetch_factors(start=start, frequency=frequency)

    if df.empty:
        logger.debug(f"No new {frequency} factor data.")
        return

    logger.info(f"Got {len(df)} rows. Storing...")
    inserted = store_factors(df, frequency=frequency)
    logger.info(f"Done. {inserted} new rows inserted.")


if __name__ == "__main__":
    fetch_and_store_factors(frequency="daily")
    fetch_and_store_factors(frequency="monthly")
