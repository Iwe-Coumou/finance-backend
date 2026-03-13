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

BASE_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"

# Explicit filenames per region — French's naming is inconsistent so don't try to construct these
DATASETS: dict[str, dict[str, dict[str, str | None]]] = {
    "us": {
        "daily":   {"ff5": "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip",
                    "mom": "F-F_Momentum_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "F-F_Research_Data_5_Factors_2x3_CSV.zip",
                    "mom": "F-F_Momentum_Factor_CSV.zip"},
    },
    "global": {
        "daily":   {"ff5": "Global_5_Factors_daily_CSV.zip",
                    "mom": "Global_MOM_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "Global_5_Factors_CSV.zip",
                    "mom": "Global_MOM_Factor_CSV.zip"},
    },
    "global_ex_us": {
        "daily":   {"ff5": "Global_ex_US_5_Factors_daily_CSV.zip",
                    "mom": "Global_ex_US_MOM_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "Global_ex_US_5_Factors_CSV.zip",
                    "mom": "Global_ex_US_MOM_Factor_CSV.zip"},
    },
    "europe": {
        "daily":   {"ff5": "Europe_5_Factors_daily_CSV.zip",
                    "mom": "Europe_MOM_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "Europe_5_Factors_CSV.zip",
                    "mom": "Europe_MOM_Factor_CSV.zip"},
    },
    "japan": {
        "daily":   {"ff5": "Japan_5_Factors_daily_CSV.zip",
                    "mom": "Japan_MOM_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "Japan_5_Factors_CSV.zip",
                    "mom": "Japan_MOM_Factor_CSV.zip"},
    },
    "apac": {
        "daily":   {"ff5": "Asia_Pacific_ex_Japan_5_Factors_daily_CSV.zip",
                    "mom": "Asia_Pacific_ex_Japan_MOM_Factor_daily_CSV.zip"},
        "monthly": {"ff5": "Asia_Pacific_ex_Japan_5_Factors_CSV.zip",
                    "mom": "Asia_Pacific_ex_Japan_MOM_Factor_CSV.zip"},
    },
    "em": {
        "daily":   None, # not available
        "monthly": {"ff5": "Emerging_5_Factors_CSV.zip",
                    "mom": None},
    },
}

def _build_urls(region: str, frequency: str) -> dict[str, str]:
    if region not in DATASETS:
        raise ValueError(f"Unknown region '{region}'. Valid options: {list(DATASETS)}")
    files = DATASETS[region][frequency]
    if files is None:
        raise ValueError(f"No {frequency} data available for region '{region}'")
    urls = {"ff5": f"{BASE_URL}/{files['ff5']}"}
    if files.get("mom"):
        urls["mom"] = f"{BASE_URL}/{files['mom']}"
    return urls        


FACTOR_COLUMN_MAP = {
    "Mkt-RF": "mkt",
    "SMB": "smb",
    "HML": "hml",
    "RMW": "rmw",
    "CMA": "cma",
    "Mom": "mom",
    "WML": 'mom',
    "RF": 'rf',
}


def download_french_csv(url: str) -> pd.DataFrame:
    logger.debug(f"Fetching {url}")
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
        if ("Mkt-RF" in stripped or "Mom" in stripped or "WML" in stripped) and stripped.startswith(","):
            header_line = i
            logger.debug(f"Header found at line {i}: {stripped[:60]}")
            break

    if header_line is None:
        raise ValueError(f"Could not find header line in {url}")

    logger.debug(f"Header at line {header_line}, scanning for data bounds")

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

    logger.debug(f"Loaded Dataframe: {df.shape} from {csv_filename}")
    return df


def parse_index(df: pd.DataFrame, frequency: str) -> pd.DataFrame:
    if frequency == "daily":
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
    else:
        df.index = pd.to_datetime(df.index, format="%Y%m") + pd.offsets.MonthEnd(0)
    df.index.name = "date"
    return df


def fetch_factors(
    start: date = date(2000, 1, 1), frequency: str = "daily", region: str='us'
) -> pd.DataFrame:
    if region not in DATASETS:
        raise ValueError(f"Unknown region: '{region}'. Valid options: {list(DATASETS)}")
    
    urls = _build_urls(region=region, frequency=frequency)

    logger.info(f"Downloading FF5 [{region}] {frequency}...")
    ff5 = download_french_csv(urls["ff5"])
    
    if 'mom' in urls:
        logger.info(f"Downloading momentum [{region}] {frequency}...")
        mom = download_french_csv(urls["mom"])
        ff5 = ff5.drop(columns=["Mom", "WML"], errors="ignore")
        combined = ff5.join(mom, how="inner")
    else:
        logger.info(f"Momentum not available for region '{region}', skipping.")
        combined = ff5

    
    combined = combined.rename(columns=FACTOR_COLUMN_MAP)
    logger.debug(f"Columns after rename: {combined.columns.tolist()}")

    combined = combined.loc[:, ~combined.columns.duplicated(keep='first')]

    keep = list(dict.fromkeys(c for c in FACTOR_COLUMN_MAP.values() if c in combined.columns))
    combined = combined[keep]

    combined = combined.apply(pd.to_numeric, errors="coerce") / 100
    combined = parse_index(combined, frequency)

    combined = combined[combined.index >= pd.Timestamp(start)]
    combined = combined.dropna()

    return combined


def get_last_stored_factor_data(frequency: str, region: str) -> date | None:
    engine = get_engine()
    with Session(engine) as session:
        result = session.execute(
            select(FactorReturn.date)
            .where(FactorReturn.frequency == frequency)
            .where(FactorReturn.region == region)
            .order_by(FactorReturn.date.desc())
            .limit(1)
        ).scalar()
        return result


def store_factors(df: pd.DataFrame, frequency: str = "daily", region: str='us') -> int:
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
                        region=region,
                    )
                )
                inserted += 1
        session.commit()

    return inserted


def fetch_and_store_factors(
    start: date = date(2000, 1, 1),
    frequency: str = "daily",
    regions: list[str] | None = None,
) -> None:
    regions = regions or list(DATASETS.keys())

    for region in regions:
        logger.info(f"[{region}] Starting {frequency} factor fetch...")

        if DATASETS[region][frequency] is None:
            logger.info(f"[{region}] No {frequency} data available, skipping.")
            continue

        last_date = get_last_stored_factor_data(frequency, region)
        region_start = last_date + timedelta(days=1) if last_date is not None else start

        logger.info(f"[{region}] Fetching from {region_start}...")
        df = fetch_factors(start=region_start, frequency=frequency, region=region)

        if df.empty:
            logger.debug(f"[{region}] No new {frequency} factor data.")
            continue

        logger.info(f"[{region}] Got {len(df)} rows. Storing...")
        inserted = store_factors(df, frequency=frequency, region=region)
        logger.info(f"[{region}] Done. {inserted} new rows inserted.")


if __name__ == "__main__":
    fetch_and_store_factors(frequency="daily")
    fetch_and_store_factors(frequency="monthly")
