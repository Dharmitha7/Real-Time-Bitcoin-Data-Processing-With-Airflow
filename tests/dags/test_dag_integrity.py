import pytest
from airflow.models import DagBag

EXPECTED_TASK_IDS = {
    "fetch_price",
    "evaluate_and_alert",
    "append_raw_csv",
    "archive_raw_snapshot",
    "upload_archive_to_s3",
    "upload_raw_to_s3",
    "run_quality_checks",
    "compute_rolling_stats",
    "upload_processed_to_s3",
}


@pytest.fixture(scope="module")
def dagbag():
    # Airflow 3's DagBag has no include_examples flag; passing an explicit
    # dag_folder already scopes it to just this repo's dags/, not the
    # example DAGs bundled inside the airflow package itself.
    return DagBag(dag_folder="dags")


def test_no_import_errors(dagbag):
    assert dagbag.import_errors == {}


def test_dag_loaded(dagbag):
    assert "bitcoin_data_pipeline" in dagbag.dags


def test_dag_has_tags(dagbag):
    dag = dagbag.dags["bitcoin_data_pipeline"]
    assert dag.tags


def test_all_tasks_have_retries_and_timeout(dagbag):
    dag = dagbag.dags["bitcoin_data_pipeline"]
    for task in dag.tasks:
        assert task.retries and task.retries > 0
        assert task.execution_timeout is not None


def test_expected_tasks_are_wired_in(dagbag):
    # In particular, this catches archive_raw_snapshot ever again being defined
    # but not actually connected into the task graph.
    dag = dagbag.dags["bitcoin_data_pipeline"]
    assert EXPECTED_TASK_IDS.issubset(set(dag.task_ids))
