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
    "on_failure_callback": alerts.dag_failure_slack_callback,
}

# Network-dependent tasks (the CoinGecko fetch and the three S3 uploads) get
# more retries with exponential backoff and a tighter timeout than the
# default, since they're the tasks most likely to hit transient failures.
_NETWORK_TASK_ARGS = {
    "retries": 3,
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(minutes=5),
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
    @task(task_id="fetch_price", **_NETWORK_TASK_ARGS)
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

    @task(task_id="upload_archive_to_s3", **_NETWORK_TASK_ARGS)
    def upload_archive_to_s3_task(archive_path: str) -> None:
        if _s3_uploads_skipped():
            return
        parquet_path = storage.write_parquet(archive_path, archive_path.replace(".csv", ".parquet"))
        filename = parquet_path.rsplit("/", 1)[-1]
        key = storage.build_s3_key("archive", pendulum.now("UTC"), filename)
        storage.upload_to_s3(parquet_path, storage.default_bucket(), key)

    @task(task_id="upload_raw_to_s3", **_NETWORK_TASK_ARGS)
    def upload_raw_to_s3_task(raw_path: str) -> None:
        if _s3_uploads_skipped():
            return
        parquet_path = storage.write_parquet(raw_path, raw_path.replace(".csv", ".parquet"))
        key = storage.build_s3_key("raw", pendulum.now("UTC"), "bitcoin_raw.parquet")
        storage.upload_to_s3(parquet_path, storage.default_bucket(), key)

    @task(task_id="run_quality_checks")
    def run_quality_checks_task(raw_path: str) -> str:
        quality.run_quality_checks(raw_path)
        return raw_path

    @task(task_id="compute_rolling_stats")
    def compute_rolling_stats_task(raw_path: str) -> str:
        return storage.compute_rolling_stats(raw_path)

    @task(task_id="upload_processed_to_s3", **_NETWORK_TASK_ARGS)
    def upload_processed_to_s3_task(processed_path: str) -> None:
        if _s3_uploads_skipped():
            return
        parquet_path = storage.write_parquet(
            processed_path, processed_path.replace(".csv", ".parquet")
        )
        key = storage.build_s3_key("processed", pendulum.now("UTC"), "bitcoin_processed.parquet")
        storage.upload_to_s3(parquet_path, storage.default_bucket(), key)

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
