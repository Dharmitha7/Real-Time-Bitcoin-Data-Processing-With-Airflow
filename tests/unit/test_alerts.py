import json

import responses

from bitcoin_pipeline import alerts

WEBHOOK_URL = "https://hooks.slack.com/services/TEST/TEST/TEST"


@responses.activate
def test_send_slack_alert_success():
    responses.add(responses.POST, WEBHOOK_URL, json={"ok": True}, status=200)

    assert alerts.send_slack_alert("hello", webhook_url=WEBHOOK_URL) is True


@responses.activate
def test_send_slack_alert_non_200_returns_false():
    responses.add(responses.POST, WEBHOOK_URL, body="invalid_payload", status=400)

    assert alerts.send_slack_alert("hello", webhook_url=WEBHOOK_URL) is False


def test_send_slack_alert_missing_webhook_is_noop(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)

    assert alerts.send_slack_alert("hello", webhook_url=None) is False


@responses.activate
def test_evaluate_and_alert_triggers_above_threshold(monkeypatch, sample_record):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", WEBHOOK_URL)
    responses.add(responses.POST, WEBHOOK_URL, status=200)
    record = dict(sample_record, change_1h=10.0, change_24h=1.0)

    triggered = alerts.evaluate_and_alert(record, threshold=5.0)

    assert len(triggered) == 1
    assert "1h anomaly" in triggered[0]
    sent_body = json.loads(responses.calls[0].request.body)
    assert sent_body["text"].startswith("[PRICE ANOMALY]")


def test_evaluate_and_alert_no_trigger_below_threshold(sample_record):
    record = dict(sample_record, change_1h=1.0, change_24h=1.0)

    triggered = alerts.evaluate_and_alert(record, threshold=5.0)

    assert triggered == []


@responses.activate
def test_dag_failure_slack_callback_sends_ops_alert(monkeypatch):
    monkeypatch.setenv("SLACK_WEBHOOK_URL", WEBHOOK_URL)
    responses.add(responses.POST, WEBHOOK_URL, status=200)

    class FakeTaskInstance:
        task_id = "upload_raw_to_s3"
        dag_id = "bitcoin_data_pipeline"

    alerts.dag_failure_slack_callback(
        {"task_instance": FakeTaskInstance(), "run_id": "manual__2026-01-01T00:00:00+00:00"}
    )

    sent_body = json.loads(responses.calls[0].request.body)
    assert sent_body["text"].startswith("[OPS ALERT]")
    assert "upload_raw_to_s3" in sent_body["text"]
    assert "bitcoin_data_pipeline" in sent_body["text"]
