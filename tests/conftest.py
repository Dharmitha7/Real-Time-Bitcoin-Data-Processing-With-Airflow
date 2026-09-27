import boto3
import pytest
from moto import mock_aws

TEST_BUCKET = "test-bitcoin-bucket"


@pytest.fixture
def s3_bucket(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    with mock_aws():
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=TEST_BUCKET)
        yield TEST_BUCKET


@pytest.fixture
def sample_record():
    return {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "price_usd": 50000.0,
        "change_1h": 1.0,
        "change_24h": 2.0,
    }
