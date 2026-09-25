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


def test_evaluate_and_alert_no_trigger_below_threshold(sample_record):
    record = dict(sample_record, change_1h=1.0, change_24h=1.0)

    triggered = alerts.evaluate_and_alert(record, threshold=5.0)

    assert triggered == []
