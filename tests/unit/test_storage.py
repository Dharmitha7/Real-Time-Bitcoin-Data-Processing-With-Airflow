import os
from datetime import datetime, timezone

import boto3
import pandas as pd
import pytest

from bitcoin_pipeline import storage


def test_append_raw_record_creates_file(tmp_path, sample_record):
    raw_path = str(tmp_path / "raw.csv")

    result = storage.append_raw_record(sample_record, raw_path=raw_path)

    assert result == raw_path
    df = pd.read_csv(raw_path)
    assert len(df) == 1
    assert df.iloc[0]["price_usd"] == 50000.0


def test_append_raw_record_appends_to_existing(tmp_path, sample_record):
    raw_path = str(tmp_path / "raw.csv")

    storage.append_raw_record(sample_record, raw_path=raw_path)
    storage.append_raw_record(sample_record, raw_path=raw_path)

    assert len(pd.read_csv(raw_path)) == 2


def test_compute_rolling_stats(tmp_path):
    raw_path = str(tmp_path / "raw.csv")
    processed_path = str(tmp_path / "processed.csv")
    pd.DataFrame({"price_usd": [100.0, 200.0, 300.0]}).to_csv(raw_path, index=False)

    result = storage.compute_rolling_stats(
        raw_path=raw_path, processed_path=processed_path, window=2
    )

    assert result == processed_path
    out = pd.read_csv(processed_path)
    assert "price_ma" in out.columns
    assert "price_std" in out.columns
    assert out.iloc[1]["price_ma"] == 150.0


def test_compute_rolling_stats_missing_column_raises(tmp_path):
    raw_path = str(tmp_path / "raw.csv")
    pd.DataFrame({"other": [1, 2]}).to_csv(raw_path, index=False)

    with pytest.raises(ValueError):
        storage.compute_rolling_stats(raw_path=raw_path, processed_path=str(tmp_path / "out.csv"))


def test_upload_to_s3_uploads_the_given_local_path(tmp_path, s3_bucket):
    # Regression test: upload_to_s3 used to ignore its arguments and always
    # upload the module-level PROCESSED_DATA_PATH regardless of local_path.
    file_a = tmp_path / "a.csv"
    file_a.write_text("file a contents")
    file_b = tmp_path / "b.csv"
    file_b.write_text("file b contents, different from a")

    storage.upload_to_s3(str(file_b), s3_bucket, "uploaded.csv")

    s3 = boto3.client("s3", region_name="us-east-1")
    body = s3.get_object(Bucket=s3_bucket, Key="uploaded.csv")["Body"].read().decode()
    assert body == "file b contents, different from a"


def test_upload_to_s3_raises_on_missing_file(s3_bucket):
    with pytest.raises(FileNotFoundError):
        storage.upload_to_s3("/nonexistent/path.csv", s3_bucket, "key.csv")


def test_archive_raw_snapshot_creates_timestamped_copy(tmp_path):
    raw_path = tmp_path / "raw.csv"
    raw_path.write_text("price_usd\n100\n")
    archive_dir = tmp_path / "archive"

    archive_file = storage.archive_raw_snapshot(
        raw_path=str(raw_path), archive_dir=str(archive_dir)
    )

    assert os.path.exists(archive_file)
    assert str(archive_dir) in archive_file
    assert "bitcoin_raw_snapshot_" in archive_file


def test_archive_raw_snapshot_raises_if_raw_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        storage.archive_raw_snapshot(
            raw_path=str(tmp_path / "missing.csv"), archive_dir=str(tmp_path / "archive")
        )


def test_default_bucket_reads_env(monkeypatch):
    monkeypatch.setenv("BITCOIN_S3_BUCKET", "my-bucket")

    assert storage.default_bucket() == "my-bucket"


def test_default_bucket_raises_if_unset(monkeypatch):
    monkeypatch.delenv("BITCOIN_S3_BUCKET", raising=False)

    with pytest.raises(KeyError):
        storage.default_bucket()


def test_build_s3_key_partitions_by_date_and_hour():
    dt = datetime(2026, 9, 25, 14, 30, tzinfo=timezone.utc)

    key = storage.build_s3_key("raw", dt, "bitcoin_raw.parquet")

    assert key == "raw/dt=2026-09-25/hour=14/bitcoin_raw.parquet"
