from src.logger import get_logger
from src.data.config import YF_TO_OPENFIGI_EXCHANGE
from src.data.database.db import get_engine, Asset
from src.data.retrievers.assets import get_assets
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
import requests
import time
import pandas as pd


_logger = get_logger(__name__)

def _pick_best_figi(results: list[dict], preferred_exchange: str | None = None) -> dict | None:
    if not results:
        return None

    equities = [r for r in results if r.get("marketSector") == "Equity"]
    if not equities:
        equities = results

    mapped = YF_TO_OPENFIGI_EXCHANGE.get(preferred_exchange) if preferred_exchange else None

    composites = [
        r for r in equities
        if r.get("figi") == r.get("compositeFIGI")
        and r.get("securityType") in ("Common Stock", "ETP")
    ]

    if composites:
        if mapped:
            match = [r for r in composites if r.get("exchCode") == mapped]
            if match:
                return match[0]
        return composites[0]

    if mapped:
        match = [r for r in equities if r.get("exchCode") == mapped]
        if match:
            return match[0]

    for r in equities:
        if r.get("securityType") in ("Common Stock", "ETP"):
            return r

    return equities[0]


def _get_figi_batch(asset_data: pd.DataFrame) -> dict[str, dict]:
    tickers_in_payload = []
    payload = []

    for ticker, row in asset_data.iterrows():
        isin = row.get("isin")
        exchange = row.get("exchange")

        if pd.notna(isin) and isin:
            query = {"idType": "ID_ISIN", "idValue": isin}
        elif pd.notna(exchange):
            symbol = ticker.split(".")[0] if "." in ticker else ticker
            if exchange == "HKG":
                symbol = symbol.lstrip("0") or symbol
            query = {"idType": "TICKER", "idValue": symbol}
        else:
            _logger.debug(f"[{ticker}] Skipping — no ISIN or exchange available")
            continue

        payload.append(query)
        tickers_in_payload.append(ticker)

    _logger.debug(f"Sending payload: {payload}")
    response = requests.post(
        "https://api.openfigi.com/v3/mapping",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()

    output = {}
    for ticker, result in zip(tickers_in_payload, results):
        if "data" in result and result["data"]:
            preferred_exchange = asset_data.loc[ticker, "exchange"]
            output[ticker] = _pick_best_figi(result["data"], preferred_exchange=preferred_exchange)
        else:
            _logger.debug(f"[{ticker}] No FIGI results found | raw response: {result}")
    return output


def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


def _update_figis(figi_map: dict[str, str], force: bool = False):
    engine = get_engine()
    with Session(engine) as session:
        for ticker, figi in figi_map.items():
            asset = session.execute(
                select(Asset).where(Asset.ticker == ticker)
            ).scalar_one_or_none()

            if not asset:
                _logger.warning(f"[{ticker}] Asset not found")
                continue
            if asset.figi and not force:
                _logger.debug(f"[{ticker}] FIGI already set to '{asset.figi}', skipping")
                continue

            asset.figi = figi
            asset.updated_at = func.now()
            _logger.debug(f"[{ticker}] FIGI set to '{figi}'")

        session.commit()


def enrich(force: bool = False):
    asset_df = get_assets(cols=["exchange", "isin"])
    _logger.info(f"Starting FIGI enrichment for {len(asset_df)} assets...")

    updated = 0
    for batch in _chunks(list(asset_df.index), 10):
        results = _get_figi_batch(asset_data=asset_df.loc[batch])
        figi_map = {
            ticker: figi_data["figi"]
            for ticker, figi_data in results.items()
            if figi_data and figi_data.get("figi")
        }
        _update_figis(figi_map, force=force)
        updated += len(figi_map)
        time.sleep(2)

    _logger.info(f"FIGI enrichment complete. Updated {updated}/{len(asset_df)} assets.")


def main():
    enrich(True)


if __name__ == "__main__":
    main()