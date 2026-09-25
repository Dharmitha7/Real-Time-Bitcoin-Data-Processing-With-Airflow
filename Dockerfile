FROM apache/airflow:3.3.2
USER airflow

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY pyproject.toml /opt/airflow/pyproject.toml
COPY bitcoin_pipeline /opt/airflow/bitcoin_pipeline
RUN pip install --no-cache-dir --no-deps /opt/airflow