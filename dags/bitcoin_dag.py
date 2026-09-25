"""
Airflow DAG to automate real-time Bitcoin data ingestion, anomaly detection with Slack alerts,
data-quality checks, rolling statistics computation, archival, and S3 uploads using the
bitcoin_pipeline package.
"""

import os
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

from bitcoin_pipeline import alerts, fetch, quality, storage


def _s3_uploads_skipped() -> bool:
    # Lets the CI smoke test (Phase 6) exercise the full task graph without
    # needing real AWS credentials as a GitHub secret.
    return os.getenv("BITCOIN_PIPELINE_SKIP_S3") == "true"


default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=10),
}


@dag(
    dag_id="bitcoin_data_pipeline",
    description="ETL DAG: ingest, validate, compute stats, archive, alert, and upload Bitcoin data",
    default_args=default_args,
    schedule="@hourly",
    start_date=pendulum.datetime(2025, 5, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["bitcoin", "etl", "stats", "s3", "slack", "archival"],
)
def bitcoin_data_pipeline():
    @task(task_id="fetch_price")
    def fetch_price_task() -> dict:
        return fetch.fetch_bitcoin_price()

    @task(task_id="evaluate_and_alert")
    def evaluate_and_alert_task(record: dict) -> None:
        alerts.evaluate_and_alert(record)

    @task(task_id="append_raw_csv")
    def append_raw_csv_task(record: dict) -> str:
        return storage.append_raw_record(record)

    @task(task_id="archive_raw_snapshot")
    def archive_raw_snapshot_task(raw_path: str) -> str:
        return storage.archive_raw_snapshot(raw_path)

    @task(task_id="upload_archive_to_s3")
    def upload_archive_to_s3_task(archive_path: str) -> None:
        if _s3_uploads_skipped():
            return
        filename = archive_path.rsplit("/", 1)[-1]
        storage.upload_to_s3(archive_path, storage.default_bucket(), f"archive/{filename}")

    @task(task_id="upload_raw_to_s3")
    def upload_raw_to_s3_task(raw_path: str) -> None:
        if _s3_uploads_skipped():
            return
        storage.upload_to_s3(raw_path, storage.default_bucket(), "raw/bitcoin_raw.csv")

    @task(task_id="run_quality_checks")
    def run_quality_checks_task(raw_path: str) -> str:
        quality.run_quality_checks(raw_path)
        return raw_path

    @task(task_id="compute_rolling_stats")
    def compute_rolling_stats_task(raw_path: str) -> str:
        return storage.compute_rolling_stats(raw_path)

    @task(task_id="upload_processed_to_s3")
    def upload_processed_to_s3_task(processed_path: str) -> None:
        if _s3_uploads_skipped():
            return
        storage.upload_to_s3(
            processed_path, storage.default_bucket(), "processed/bitcoin_processed.csv"
        )

    price_record = fetch_price_task()
    raw_path = append_raw_csv_task(price_record)

    evaluate_and_alert_task(price_record)

    archive_path = archive_raw_snapshot_task(raw_path)
    upload_archive_to_s3_task(archive_path)

    upload_raw_to_s3_task(raw_path)

    checked_path = run_quality_checks_task(raw_path)
    processed_path = compute_rolling_stats_task(checked_path)
    upload_processed_to_s3_task(processed_path)


bitcoin_data_pipeline()
