"""Slack alerting: anomaly notifications for the Bitcoin price pipeline."""

import logging
import os

import requests

logger = logging.getLogger(__name__)


def send_slack_alert(message: str, webhook_url: str | None = None) -> bool:
    """Post a message to Slack. Returns whether it was sent successfully."""
    webhook_url = webhook_url if webhook_url is not None else os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("Slack webhook URL not set. Skipping alert.")
        return False
    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Slack alert failed: {response.text}")
            return False
        logger.info("Slack alert sent.")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Slack notification error: {e}")
        return False


def evaluate_and_alert(record: dict, threshold: float = 5.0) -> list[str]:
    """Check a price record for 1h/24h swings beyond threshold and alert on Slack if so."""
    change_1h = float(record.get("change_1h") or 0)
    change_24h = float(record.get("change_24h") or 0)

    triggered = []
    if abs(change_1h) > threshold:
        triggered.append(f" 1h anomaly: {change_1h:.2f}%")
    if abs(change_24h) > threshold:
        triggered.append(f" 24h anomaly: {change_24h:.2f}%")

    for message in triggered:
        logger.warning(message)

    if triggered:
        send_slack_alert("[PRICE ANOMALY]\n" + "\n".join(triggered))

    return triggered


def dag_failure_slack_callback(context: dict) -> None:
    """Airflow on_failure_callback: alert that the pipeline itself broke.

    Uses a distinct [OPS ALERT] prefix so it's never confused with a
    [PRICE ANOMALY] message - one means "the data looks unusual", the other
    means "the pipeline stopped working".
    """
    ti = context["task_instance"]
    message = (
        f"[OPS ALERT] Task '{ti.task_id}' in DAG '{ti.dag_id}' failed "
        f"(run {context.get('run_id')})."
    )
    send_slack_alert(message)
