from __future__ import annotations

import hashlib
import time
from collections.abc import MutableMapping

from src.models import WeChatNotificationEvent


class MemoryDeduper:
    def __init__(self, ttl_seconds: int = 10) -> None:
        self._ttl_seconds = ttl_seconds
        self._seen: MutableMapping[str, float] = {}

    def is_duplicate(self, event: WeChatNotificationEvent) -> bool:
        self._purge_expired()
        fingerprint = self._build_fingerprint(event)
        now = time.time()
        expires_at = self._seen.get(fingerprint)
        if expires_at and expires_at > now:
            return True

        self._seen[fingerprint] = now + self._ttl_seconds
        return False

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [key for key, expires_at in self._seen.items() if expires_at <= now]
        for key in expired:
            self._seen.pop(key, None)

    @staticmethod
    def _build_fingerprint(event: WeChatNotificationEvent) -> str:
        base = "|".join(
            [
                (event.sender or "").strip(),
                (event.preview or "").strip(),
                event.timestamp.strftime("%Y-%m-%d %H:%M"),
            ]
        )
        return hashlib.sha256(base.encode("utf-8")).hexdigest()
