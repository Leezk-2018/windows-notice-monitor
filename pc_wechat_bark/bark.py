from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from .models import NotificationEvent


@dataclass(slots=True)
class BarkResult:
    ok: bool
    status_code: int | None = None
    error: str = ""


class BarkClient:
    def __init__(self, config: dict, timeout: int = 10):
        self.server = str(config.get("server", "https://api.day.app")).rstrip("/")
        self.device_key = str(config.get("device_key", "")).strip()
        self.group = str(config.get("group", "")).strip()
        self.sound = str(config.get("sound", "")).strip()
        self.icon = str(config.get("icon", "")).strip()
        self.url = str(config.get("url", "")).strip()
        self.timeout = timeout

    def validate(self) -> list[str]:
        errors = []
        if not self.server:
            errors.append("bark.server 不能为空")
        if not self.device_key or self.device_key == "YOUR_DEVICE_KEY":
            errors.append("bark.device_key 未配置")
        return errors

    def send(self, event: NotificationEvent, retry: dict, logger) -> None:
        attempts = max(1, int(retry.get("max_attempts", 3)))
        backoff = list(retry.get("backoff_seconds", [1, 3, 10]))
        last_error = "unknown error"
        for attempt in range(1, attempts + 1):
            result = self._send_once(event)
            if result.ok:
                logger.info("Bark 推送成功: %s", event.title)
                return
            last_error = result.error or f"HTTP {result.status_code}"
            logger.warning("Bark 推送失败(%s/%s): %s", attempt, attempts, last_error)
            if attempt < attempts:
                time.sleep(backoff[min(attempt - 1, len(backoff) - 1)] if backoff else 1)
        raise RuntimeError(f"Bark 推送失败: {last_error}")

    def _send_once(self, event: NotificationEvent) -> BarkResult:
        params = {
            "title": event.title,
            "body": event.body,
        }
        if self.group:
            params["group"] = self.group
        if self.sound:
            params["sound"] = self.sound
        if self.icon:
            params["icon"] = self.icon
        if self.url:
            params["url"] = self.url

        query = urllib.parse.urlencode(params)
        endpoint = f"{self.server}/{self.device_key}/?{query}"
        request = urllib.request.Request(endpoint, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                status = getattr(resp, "status", 200)
                body = resp.read()
                if 200 <= status < 300:
                    try:
                        payload = json.loads(body.decode("utf-8"))
                    except Exception:
                        payload = {}
                    code = payload.get("code", 200)
                    if code in (200, 0, "200", "0", None):
                        return BarkResult(ok=True, status_code=status)
                    return BarkResult(ok=False, status_code=status, error=str(payload))
                return BarkResult(ok=False, status_code=status, error=body.decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as e:
            return BarkResult(ok=False, status_code=e.code, error=str(e))
        except Exception as e:  # pragma: no cover
            return BarkResult(ok=False, error=str(e))
