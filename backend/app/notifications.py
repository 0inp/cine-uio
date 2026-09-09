"""Getting a failed scrape in front of a human."""

import os

import requests

from app.logging import logger

WEBHOOK_ENV_VAR = "SCRAPE_WEBHOOK_URL"
TIMEOUT_SECONDS = 10


def notify(message: str) -> bool:
    """Post a message to the configured webhook. Returns whether it was sent.

    Never raises: an unreachable webhook must not turn a successful scrape into a
    failed one, nor a failed one into a crash.
    """
    url = os.environ.get(WEBHOOK_ENV_VAR, "").strip()
    if not url:
        logger.info(f"{WEBHOOK_ENV_VAR} not set — not sending: {message}")
        return False

    # Slack reads "text", Discord reads "content", and each ignores the other's key,
    # so one payload works with either without asking which is configured.
    payload = {"text": message, "content": message}
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
    except Exception as e:
        logger.error(f"could not reach the webhook: {e}")
        return False

    if not response.ok:
        logger.error(f"webhook rejected the message: {response.status_code}")
        return False
    return True
