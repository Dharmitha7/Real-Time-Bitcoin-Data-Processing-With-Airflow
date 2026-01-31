# Production-Grade Bitcoin Data Pipeline with Apache Airflow
### Near real-time API ingestion, anomaly detection, alerting, and AWS S3 archival orchestrated with Dockerized Apache Airflow
---

## Overview

This project implements a production-grade data pipeline that ingests near real-time Bitcoin price data from an external market API, computes rolling statistics for monitoring and anomaly detection, and persists both raw and processed outputs to cloud storage.

The pipeline is orchestrated using Apache Airflow and containerized with Docker to support reproducible execution, reliable scheduling, and operational visibility. To enable traceability and auditability, immutable raw data snapshots are archived alongside continuously appended logs.

Automated Slack alerts notify operators of significant short-term price movements, simulating real-world observability and incident response workflows. This project demonstrates the design and operation of a data pipeline that emphasizes API-based ingestion, workflow orchestration, cloud storage integration, and production-aware system design.

## Problem Statement

Building reliable data pipelines for external market data involves several operational and system-level challenges. Third-party APIs can be unstable, rate-limited, or change response formats over time, requiring controlled ingestion and error handling. Time-series financial data must be preserved in its raw form to enable traceability, auditing, and historical replay.

In addition, sudden price movements should be detected automatically and surfaced to operators through alerting mechanisms, rather than relying on manual inspection. Data pipelines must also be reproducible across environments and resilient to failures, with clear task boundaries and operational visibility.

This project addresses these challenges by designing a production-style pipeline that emphasizes reliable scheduling, immutable raw data archival, automated monitoring, and cloud-based persistence.

## Architecture

**Dataflow:** CoinGecko API → Airflow DAG → Raw CSV + Snapshot Archive → Rolling Stats → Slack Alerts → S3 (raw + processed)
> _Architecture diagram / Airflow DAG graph will be added._
- **Orchestration:** Airflow schedules and runs ingestion + processing as separate tasks for reliability and traceability.
- **Storage:** Raw and processed artifacts are written locally and synced to S3 for durable retention.

## Objectives

- Ingest Bitcoin pricing data on an hourly schedule to simulate near real-time market ingestion from an external API.
- Persist continuously appended raw logs and immutable timestamped snapshots to support traceability and historical replay.
- Compute rolling mean and standard deviation metrics for monitoring and basic anomaly detection.
- Trigger automated Slack alerts when abnormal 1-hour or 24-hour price movements are detected.
- Upload raw and processed datasets to AWS S3 for durable cloud storage and downstream consumption.
- Execute the full pipeline end-to-end using a Dockerized Apache Airflow environment backed by a PostgreSQL metadata database.


## Pipeline Workflow (Airflow DAG: `bitcoin_data_pipeline`)

The pipeline is implemented as an Airflow DAG with clear task boundaries to support retries, monitoring, and modular extensibility.

| Step | Task ID                        | Description                                                                                             |
| ---- | ------------------------------ | ------------------------------------------------------------------------------------------------------- |
| 1    | `fetch_and_save_bitcoin_price` | Fetch price from CoinGecko, detect anomalies, send Slack alerts, archive raw snapshot, upload raw to S3 |
| 2    | `compute_moving_average`       | Compute moving average & std dev, save processed file, upload to S3                                     |
| 3    | `upload_processed_csv_to_s3`   | Optional redundant upload of processed file (manually callable)                                         |


## Data Outputs

The pipeline produces versioned artifacts locally (via Docker volume mounts) and optionally syncs them to AWS S3:

- **Raw append log:** `data/bitcoin_raw.csv` — continuously appended API pulls (timestamped).
- **Snapshot archive:** `data/archive/<timestamp>.csv` — immutable raw snapshots for auditability and replay.
- **Processed features:** `data/bitcoin_processed.csv` — rolling mean and standard deviation for monitoring/anomaly detection.
- **Cloud storage:** Raw and processed artifacts uploaded to **AWS S3** (when credentials are configured).

## Tech Stack

- **Orchestration:** Apache Airflow
- **Containerization:** Docker, Docker Compose
- **Data Source:** CoinGecko API
- **Storage:** Local CSV + AWS S3
- **Alerts:** Slack Webhooks
- **Language:** Python
- **Metadata DB:** PostgreSQL (Airflow backend)


##  Quickstart

### 1. Start Airflow Docker Environment

```bash
docker-compose up --build
```

Wait for containers to initialize, especially `airflow-init` and `airflow-webserver`.

### 2. Access Airflow UI

* Go to: [http://localhost:8080](http://localhost:8080)
* Login with:

  ```
  Username: admin
  Password: admin
  ```
* Trigger the DAG: `bitcoin_data_pipeline`

After execution:
- Raw and processed CSV files are written to the `data/` directory
- Snapshot files are archived under `data/archive/`
- Data is uploaded to AWS S3 if credentials are configured
- Slack alerts are sent if anomaly thresholds are met

##  File Structure

```plaintext
.
├── dags/
│   └── bitcoin_dag.py            # Airflow DAG: defines fetch, process, upload
├── bitcoin_utils.py              # All utility logic for fetch, alerts, archive, S3
├── airflow.API.ipynb             # Demonstrates the API interaction logic
├── airflow.API.md                # Markdown explanation of how the API works
├── airflow.example.ipynb         # Notebook running full pipeline sequence
├── airflow.example.md            # Explains pipeline implementation and design
├── data/                         # Volume mount for raw/processed/snapshot CSVs
├── Dockerfile                    # Optional custom build 
├── requirements.txt              # Python dependencies
├── docker-compose.yaml           # Brings up Airflow, Postgres, volumes
````

##  Configuration

### Environment Variables

These are automatically used in your Docker container:

```bash
BITCOIN_RAW_PATH=/opt/airflow/data/bitcoin_raw.csv
BITCOIN_PROCESSED_PATH=/opt/airflow/data/bitcoin_processed.csv
BITCOIN_ARCHIVE_PATH=/opt/airflow/data/archive
```

To use Slack alerts:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

###  Environment Variables with `.env` File

To avoid exposing secrets (like Slack webhooks or AWS credentials) in your code or version control, you can define them in a `.env` file:

#### Sample `.env` file:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/token/here
```

Make sure to place this file **in your project root directory**, and update your `docker-compose.yaml` to include:

```yaml
env_file:
  - .env
```

For example, inside `airflow-webserver`, `airflow-scheduler`, and `airflow-init` services:

```yaml
services:
  airflow-webserver:
    ...
    env_file:
      - .env
```


##  AWS S3 Access

* Ensure your AWS credentials are located in:

  ```
  ~/.aws/credentials
  ```
* These credentials are mounted automatically via:

  ```yaml
  - ${USERPROFILE}/.aws:/home/airflow/.aws
  ```

##  Documentation

| File                                               | Description                                                                 |
|----------------------------------------------------|-----------------------------------------------------------------------------|
| [`bitcoin_utils.py`](./bitcoin_utils.py)           | Modular utility functions: fetch, alert, archive, upload                   |
| [`bitcoin_dag.py`](./dags/bitcoin_dag.py)          | Apache Airflow DAG that orchestrates the full ETL pipeline                 |
| [`airflow.API.ipynb`](./airflow.API.ipynb)         | Tool demonstration notebook — showcases how utility functions behave       |
| [`airflow.API.md`](./airflow.API.md)               | Explains each utility function's internal logic and expected behavior      |
| [`airflow.example.ipynb`](./airflow.example.ipynb) | Full project demo notebook — simulates the entire DAG workflow manually    |
| [`airflow.example.md`](./airflow.example.md)       | Describes the step-by-step pipeline execution and design rationale         |


## Limitations & Next Steps

**Limitations**
- Runs on an hourly schedule (near real-time), not true streaming.
- Uses CSV-based artifacts rather than database or warehouse tables.
- Anomaly detection is based on rolling statistics and threshold rules.

**Next Steps**
- Partition S3 outputs by time (e.g., `date=YYYY-MM-DD/hour=HH/`) for scalable retention.
- Add schema and data quality validation (e.g., Great Expectations).
- Persist processed outputs to a database or warehouse for analytics use.
- Extend monitoring and alerting for task failures and data quality issues.

##  References

* [CoinGecko API Docs](https://www.coingecko.com/en/api)
* [Apache Airflow TaskFlow](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/taskflow.html)
* [AWS S3 Python SDK](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
* [Slack Webhooks](https://api.slack.com/messaging/webhooks)



