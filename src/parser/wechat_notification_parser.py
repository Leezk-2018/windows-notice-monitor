from __future__ import annotations

from datetime import datetime

from src.models import RawNotification, WeChatNotificationEvent


class WeChatNotificationParser:
    def __init__(self, app_names: list[str]) -> None:
        self._app_names = {name.casefold() for name in app_names}

    def is_wechat_notification(self, notification: RawNotification) -> bool:
        app_name = (notification.app_name or "").strip().casefold()
        return app_name in self._app_names

    def parse(self, notification: RawNotification) -> WeChatNotificationEvent | None:
        if not self.is_wechat_notification(notification):
            return None

        title = (notification.title or "").strip()
        body = (notification.body or "").strip()

        sender = title or "微信"
        preview = body or title or "收到新消息"
        raw_text = "\n".join(part for part in [title, body] if part).strip() or "收到新消息"
        chat_type = self._guess_chat_type(title=title, body=body)

        return WeChatNotificationEvent(
            source="wechat_windows_notification",
            app_name=notification.app_name,
            sender=sender,
            preview=preview,
            chat_type=chat_type,
            raw_text=raw_text,
            timestamp=notification.timestamp if isinstance(notification.timestamp, datetime) else datetime.now(),
        )

    @staticmethod
    def _guess_chat_type(title: str, body: str) -> str:
        text = f"{title}\n{body}"
        group_markers = ["群", "群聊", "@", "[群聊]"]
        if any(marker in text for marker in group_markers):
            return "group"
        return "unknown"
