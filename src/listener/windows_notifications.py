from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Protocol

from src.models import RawNotification


LOG = logging.getLogger(__name__)
_POWERSHELL_QUERY = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$listener = [Windows.UI.Notifications.Management.UserNotificationListener, Windows.UI.Notifications, ContentType=WindowsRuntime]::Current
$access = [System.WindowsRuntimeSystemExtensions]::AsTask($listener.RequestAccessAsync()).GetAwaiter().GetResult()
if ($access -ne [Windows.UI.Notifications.Management.UserNotificationListenerAccessStatus]::Allowed) {
    @{ status = 'access_denied'; message = $access.ToString(); notifications = @() } | ConvertTo-Json -Compress
    exit 0
}
$kind = [Windows.UI.Notifications.NotificationKinds]::Toast
$notifications = [System.WindowsRuntimeSystemExtensions]::AsTask($listener.GetNotificationsAsync($kind)).GetAwaiter().GetResult()
$items = foreach ($notification in $notifications) {
    $appName = ''
    if ($notification.AppInfo -and $notification.AppInfo.DisplayInfo) {
        $appName = [string]$notification.AppInfo.DisplayInfo.DisplayName
    }

    $texts = @()
    $binding = $notification.Notification.Visual.GetBinding([Windows.UI.Notifications.KnownNotificationBindings]::ToastGeneric)
    if ($binding) {
        foreach ($text in $binding.GetTextElements()) {
            if ($text.Text) {
                $texts += [string]$text.Text
            }
        }
    }

    [pscustomobject]@{
        id = [string]$notification.Id
        app_name = $appName
        title = if ($texts.Count -ge 1) { $texts[0] } else { '' }
        body = if ($texts.Count -ge 2) { ($texts[1..($texts.Count - 1)] -join "`n") } else { '' }
        timestamp = $notification.CreationTime.DateTime.ToString('o')
        raw_text = ($texts -join "`n")
    }
}
@{ status = 'ok'; notifications = @($items) } | ConvertTo-Json -Compress -Depth 4
""".strip()


class NotificationListener(Protocol):
    def get_notifications(self) -> Iterable[RawNotification]: ...


class MockNotificationListener:
    def get_notifications(self) -> Iterable[RawNotification]:
        return [
            RawNotification(
                app_name="微信",
                title="张三",
                body="晚上一起吃饭吗？",
                timestamp=datetime.now(),
                raw_payload={"mock": True},
            )
        ]


class WindowsNotificationListener:
    def __init__(self, poller: Callable[[], list[RawNotification]] | None = None) -> None:
        self._warned = False
        self._seen_ids: set[str] = set()
        self._poller = poller or self._load_notifications

    def get_notifications(self) -> Iterable[RawNotification]:
        try:
            notifications = self._poller()
        except Exception as exc:
            self._warn_once(f"Windows notification listener unavailable: {exc}")
            LOG.debug("Windows notification listener failure", exc_info=True)
            return []

        fresh_notifications: list[RawNotification] = []
        for notification in notifications:
            notification_id = str(notification.raw_payload.get("id", "")).strip()
            if notification_id:
                if notification_id in self._seen_ids:
                    continue
                self._seen_ids.add(notification_id)
            fresh_notifications.append(notification)
        return fresh_notifications

    def _load_notifications(self) -> list[RawNotification]:
        if sys.platform != "win32":
            raise RuntimeError("Windows notification listener only works on Windows")

        payload = self._query_windows_notifications()
        status = payload.get("status", "ok")
        if status != "ok":
            message = payload.get("message", status)
            raise RuntimeError(f"notification access failed: {message}")

        items = payload.get("notifications", [])
        if not isinstance(items, list):
            raise RuntimeError("notification query returned invalid payload")

        notifications: list[RawNotification] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            notifications.append(self._to_raw_notification(item))
        return notifications

    def _query_windows_notifications(self) -> dict[str, Any]:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                _POWERSHELL_QUERY,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip() or result.stdout.strip() or "unknown PowerShell error"
            raise RuntimeError(stderr)

        stdout = result.stdout.strip()
        if not stdout:
            return {"status": "ok", "notifications": []}

        payload = json.loads(stdout)
        if isinstance(payload, list):
            return {"status": "ok", "notifications": payload}
        if not isinstance(payload, dict):
            raise RuntimeError("notification query returned non-object JSON")
        return payload

    def _to_raw_notification(self, item: dict[str, Any]) -> RawNotification:
        timestamp = self._parse_timestamp(item.get("timestamp"))
        title = str(item.get("title") or "").strip()
        body = str(item.get("body") or "").strip()
        raw_text = str(item.get("raw_text") or "").strip()
        if not raw_text:
            raw_text = "\n".join(part for part in (title, body) if part)

        return RawNotification(
            app_name=str(item.get("app_name") or "").strip(),
            title=title,
            body=body,
            timestamp=timestamp,
            raw_payload={
                "id": str(item.get("id") or "").strip(),
                "raw_text": raw_text,
                "source": "powershell_winrt",
            },
        )

    def _parse_timestamp(self, value: Any) -> datetime:
        if not value:
            return datetime.now()
        if isinstance(value, datetime):
            return value

        text = str(value).strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return datetime.now()

    def _warn_once(self, message: str) -> None:
        if not self._warned:
            LOG.warning(message)
            self._warned = True
