"""
Airflow DAG to automate real-time Bitcoin data ingestion, anomaly detection with Slack alerts,
rolling statistics computation, and S3 uploads using bitcoin_utils.py.
"""

import sys
from datetime import timedelta

import pendulum
from airflow.sdk import dag, task

sys.path.append("/opt/airflow")
from bitcoin_utils import compute_moving_average, save_price_to_csv, upload_to_s3

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=10),
}


@dag(
    dag_id="bitcoin_data_pipeline",
    description="ETL DAG: Ingest, compute stats, archive, and upload Bitcoin data with Slack alerts",
    default_args=default_args,
    schedule="@hourly",
    start_date=pendulum.datetime(2025, 5, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["bitcoin", "etl", "stats", "s3", "slack", "archival"],
)
def bitcoin_data_pipeline():
    # Task 1: Fetch and Save Bitcoin Price (includes anomaly detection, Slack alert, S3 upload)
    @task(task_id="fetch_and_save_bitcoin_price")
    def fetch_and_save_bitcoin_price():
        save_price_to_csv()

    # Task 2: Compute rolling statistics and update processed data + S3 upload
    @task(task_id="compute_moving_average")
    def compute_moving_average_task():
        compute_moving_average()

    # Redundant uploader task if needed independently
    @task(task_id="upload_processed_csv_to_s3")
    def upload_processed_csv_to_s3():
        upload_to_s3(
            bucket_name="bitcoin-price-store",
            key_path="processed/bitcoin_processed.csv",
        )

    fetch_and_save_bitcoin_price() >> compute_moving_average_task() >> upload_processed_csv_to_s3()


bitcoin_data_pipeline()
