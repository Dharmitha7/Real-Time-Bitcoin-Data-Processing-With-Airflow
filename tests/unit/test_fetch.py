import time

import pytest
import responses
from pydantic import ValidationError

from bitcoin_pipeline import fetch

COINGECKO_URL_BASE = "https://api.coingecko.com/api/v3/simple/price"


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    # Skip tenacity's real backoff delay so retry tests run instantly.
    monkeypatch.setattr(time, "sleep", lambda seconds: None)


@responses.activate
def test_fetch_bitcoin_price_success():
    responses.add(
        responses.GET,
        COINGECKO_URL_BASE,
        json={"bitcoin": {"usd": 50000.0, "usd_1h_change": 0.5, "usd_24h_change": -1.2}},
        status=200,
    )

    result = fetch.fetch_bitcoin_price()

    assert result["price_usd"] == 50000.0
    assert result["change_1h"] == 0.5
    assert result["change_24h"] == -1.2
    assert "timestamp" in result


@responses.activate
def test_fetch_bitcoin_price_retries_then_succeeds():
    responses.add(responses.GET, COINGECKO_URL_BASE, status=429)
    responses.add(
        responses.GET,
        COINGECKO_URL_BASE,
        json={"bitcoin": {"usd": 51000.0}},
        status=200,
    )

    result = fetch.fetch_bitcoin_price()

    assert result["price_usd"] == 51000.0
    assert len(responses.calls) == 2


@responses.activate
def test_fetch_bitcoin_price_malformed_payload_raises():
    responses.add(responses.GET, COINGECKO_URL_BASE, json={"unexpected": "shape"}, status=200)

    with pytest.raises(ValidationError):
        fetch.fetch_bitcoin_price()


@responses.activate
def test_fetch_bitcoin_price_exhausts_retries_on_persistent_5xx():
    for _ in range(5):
        responses.add(responses.GET, COINGECKO_URL_BASE, status=500)

    with pytest.raises(Exception):
        fetch.fetch_bitcoin_price()

    assert len(responses.calls) == 5


@responses.activate
def test_fetch_bitcoin_price_sends_api_key_header():
    responses.add(
        responses.GET,
        COINGECKO_URL_BASE,
        json={"bitcoin": {"usd": 50000.0}},
        status=200,
    )

    fetch.fetch_bitcoin_price(api_key="demo-key-123")

    assert responses.calls[0].request.headers["x-cg-demo-api-key"] == "demo-key-123"
