FROM apache/airflow:3.3.2
USER airflow

COPY pyproject.toml /opt/airflow/pyproject.toml
COPY bitcoin_pipeline /opt/airflow/bitcoin_pipeline
RUN pip install --no-cache-dir /opt/airflow "apache-airflow-providers-amazon>=9.0,<10.0"
