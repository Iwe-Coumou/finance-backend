from src.logging.logger import get_logger
from src.data.config import YF_TO_OPENFIGI_EXCHANGE
from src.integrations.openfigi import OpenFIGIClient
import pandas as pd

_logger = get_logger(__name__)

def pick_best_figi(results: list[dict], preferred_exchange: str | None = None) -> dict | None:
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


def get_figi_batch(asset_data: pd.DataFrame, client: OpenFIGIClient) -> dict[str, dict]:
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

    _logger.debug(f"Sending FIGI batch of {len(payload)} items")
    results = client.map(payload)

    output = {}
    for ticker, result in zip(tickers_in_payload, results):
        if "data" in result and result["data"]:
            preferred_exchange = asset_data.loc[ticker, "exchange"]
            output[ticker] = pick_best_figi(result["data"], preferred_exchange=preferred_exchange)
        else:
            _logger.debug(f"[{ticker}] No FIGI results found | raw response: {result}")
    return output