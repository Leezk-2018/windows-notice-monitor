from __future__ import annotations

import logging
from typing import Any

import requests

from src.models import WeChatNotificationEvent


LOG = logging.getLogger(__name__)
_PLACEHOLDER_KEYS = {"", "your_bark_key", "changeme", "replace_me"}


class BarkNotifier:
    def __init__(self, server: str, key: str, group: str | None = None) -> None:
        self._server = server.rstrip("/")
        self._key = key.strip()
        self._group = group

    def send(self, event: WeChatNotificationEvent) -> None:
        if self._key in _PLACEHOLDER_KEYS:
            LOG.debug("Skip Bark send because key is not configured")
            return

        url = f"{self._server}/{self._key}"
        payload: dict[str, Any] = {
            "title": event.sender,
            "subtitle": "微信新消息",
            "body": event.preview,
        }
        if self._group:
            payload["group"] = self._group

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        LOG.info("Sent Bark notification for %s", event.sender)
