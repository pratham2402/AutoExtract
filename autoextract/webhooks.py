"""Webhook notifications for extraction events."""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from autoextract.config import WebhookConfig

logger = logging.getLogger(__name__)


def _build_payload(event: str, data: dict) -> dict:
    return {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }


def _send_webhook(config: WebhookConfig, payload: dict) -> bool:
    for attempt in range(1, config.retries + 1):
        try:
            response = requests.post(
                config.url,
                json=payload,
                timeout=config.timeout,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.debug("Webhook sent to %s (status %d)", config.url, response.status_code)
            return True
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Webhook attempt %d/%d to %s failed: %s",
                attempt,
                config.retries,
                config.url,
                exc,
            )
            if attempt < config.retries:
                time.sleep(2 ** attempt)
    logger.error("Webhook to %s failed after %d retries", config.url, config.retries)
    return False


def notify(
    webhooks: list[WebhookConfig],
    event: str,
    archive_name: str,
    archive_path: str,
    output_path: Optional[str] = None,
    error: Optional[str] = None,
    duration_ms: Optional[float] = None,
) -> None:
    active = [w for w in webhooks if event in w.events]
    if not active:
        return

    data = {
        "archive_name": archive_name,
        "archive_path": archive_path,
    }
    if output_path:
        data["output_path"] = output_path
    if error:
        data["error"] = error
    if duration_ms is not None:
        data["duration_ms"] = duration_ms

    payload = _build_payload(event, data)

    for webhook in active:
        _send_webhook(webhook, payload)
