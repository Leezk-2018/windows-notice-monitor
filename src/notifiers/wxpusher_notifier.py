from __future__ import annotations

import logging

import requests

from src.models import WeChatNotificationEvent


LOG = logging.getLogger(__name__)
_PLACEHOLDER_TOKENS = {"", "your_app_token", "changeme", "replace_me"}
_PLACEHOLDER_UIDS = {"", "your_uid", "changeme", "replace_me"}


class WxPusherNotifier:
    API_URL = "https://wxpusher.zjiecode.com/api/send/message"

    def __init__(self, app_token: str, uids: list[str]) -> None:
        self._app_token = app_token.strip()
        self._uids = [uid for uid in uids if uid and uid not in _PLACEHOLDER_UIDS]

    def send(self, event: WeChatNotificationEvent) -> None:
        if self._app_token in _PLACEHOLDER_TOKENS or not self._uids:
            LOG.debug("Skip WxPusher send because config is incomplete")
            return

        payload = {
            "appToken": self._app_token,
            "content": f"发送人：{event.sender}<br/>内容：{event.preview}<br/>时间：{event.timestamp.isoformat()}",
            "summary": f"微信新消息 - {event.sender}",
            "contentType": 2,
            "uids": self._uids,
        }
        response = requests.post(self.API_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("code") not in (1000, None):
            raise RuntimeError(f"WxPusher send failed: {data}")
        LOG.info("Sent WxPusher notification for %s", event.sender)
