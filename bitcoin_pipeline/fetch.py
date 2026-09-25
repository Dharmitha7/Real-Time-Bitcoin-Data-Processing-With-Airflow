"""CoinGecko price fetching: HTTP client, retry policy, and response validation."""

import logging
import os
from datetime import datetime, timezone

import requests
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

COINGECKO_URL = (
    "https://api.coingecko.com/api/v3/simple/price"
    "?ids=bitcoin&vs_currencies=usd&include_24hr_change=true&include_1hr_change=true"
)


class BitcoinPrice(BaseModel):
    usd: float = Field(gt=0)
    usd_1h_change: float | None = None
    usd_24h_change: float | None = None


class CoinGeckoResponse(BaseModel):
    bitcoin: BitcoinPrice


@retry(
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=30),
    reraise=True,
)
def _get_coingecko_price(api_key: str | None) -> dict:
    headers = {"x-cg-demo-api-key": api_key} if api_key else {}
    response = requests.get(COINGECKO_URL, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_bitcoin_price(api_key: str | None = None) -> dict:
    """Fetch the current Bitcoin price from CoinGecko, retrying on transient errors."""
    api_key = api_key if api_key is not None else os.getenv("COINGECKO_API_KEY")
    raw_data = _get_coingecko_price(api_key)

    try:
        parsed = CoinGeckoResponse.model_validate(raw_data)
    except ValidationError:
        logger.error(f"Unexpected CoinGecko response shape: {raw_data}")
        raise

    logger.info("Fetched Bitcoin price successfully.")
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price_usd": parsed.bitcoin.usd,
        "change_1h": parsed.bitcoin.usd_1h_change,
        "change_24h": parsed.bitcoin.usd_24h_change,
    }
