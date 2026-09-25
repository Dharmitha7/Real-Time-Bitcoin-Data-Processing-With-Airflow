"""CSV I/O, rolling statistics, S3 upload, and archival for the Bitcoin price pipeline."""

import logging
import os
from datetime import datetime, timezone

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

RAW_DATA_PATH = os.getenv("BITCOIN_RAW_PATH", "/opt/airflow/data/bitcoin_raw.csv")
PROCESSED_DATA_PATH = os.getenv("BITCOIN_PROCESSED_PATH", "/opt/airflow/data/bitcoin_processed.csv")
ARCHIVE_PATH = os.getenv("BITCOIN_ARCHIVE_PATH", "/opt/airflow/data/archive")


def default_bucket() -> str:
    """The S3 bucket to upload to. Looked up lazily so import/parsing never requires it."""
    return os.environ["BITCOIN_S3_BUCKET"]


def append_raw_record(record: dict, raw_path: str = RAW_DATA_PATH) -> str:
    """Append a price record to the raw CSV, creating it if it doesn't exist yet."""
    df = pd.DataFrame([record])
    if os.path.exists(raw_path):
        df_existing = pd.read_csv(raw_path)
        df = pd.concat([df_existing, df], ignore_index=True)

    df.to_csv(raw_path, index=False)
    logger.info(f"Saved price to {raw_path}")
    return raw_path


def compute_rolling_stats(
    raw_path: str = RAW_DATA_PATH,
    processed_path: str = PROCESSED_DATA_PATH,
    window: int = 24,
) -> str:
    """Compute rolling mean/std over price_usd and write the processed CSV."""
    df = pd.read_csv(raw_path)
    if "price_usd" not in df.columns:
        raise ValueError("Missing 'price_usd' column in data.")

    df["price_ma"] = df["price_usd"].rolling(window=window).mean()
    df["price_std"] = df["price_usd"].rolling(window=window).std()

    df.to_csv(processed_path, index=False)
    logger.info(f"Processed data saved to {processed_path}")
    return processed_path


def upload_to_s3(local_path: str, bucket_name: str, key_path: str) -> None:
    """Upload exactly `local_path` to s3://bucket_name/key_path."""
    try:
        logger.info(f"Uploading {local_path} to s3://{bucket_name}/{key_path}...")
        s3 = boto3.client("s3")
        s3.upload_file(local_path, bucket_name, key_path)
        logger.info(f"Uploaded to s3://{bucket_name}/{key_path}")
    except (BotoCoreError, ClientError, FileNotFoundError) as e:
        logger.error(f"Upload failed: {e}")
        raise


def archive_raw_snapshot(raw_path: str = RAW_DATA_PATH, archive_dir: str = ARCHIVE_PATH) -> str:
    """Copy the raw CSV to a timestamped snapshot file and return its path."""
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"No raw CSV to archive at {raw_path}")

    os.makedirs(archive_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_file = os.path.join(archive_dir, f"bitcoin_raw_snapshot_{timestamp}.csv")
    df = pd.read_csv(raw_path)
    df.to_csv(archive_file, index=False)
    logger.info(f"Archived raw snapshot to {archive_file}")
    return archive_file


def build_s3_key(prefix: str, dt: datetime, filename: str) -> str:
    """Build a dt=/hour= partitioned S3 key, e.g. raw/dt=2026-09-25/hour=14/bitcoin_raw.parquet."""
    return f"{prefix}/dt={dt:%Y-%m-%d}/hour={dt:%H}/{filename}"


def write_parquet(csv_path: str, parquet_path: str) -> str:
    """Convert a CSV file to Parquet at parquet_path and return that path."""
    df = pd.read_csv(csv_path)
    df.to_parquet(parquet_path, index=False)
    logger.info(f"Wrote Parquet copy of {csv_path} to {parquet_path}")
    return parquet_path
