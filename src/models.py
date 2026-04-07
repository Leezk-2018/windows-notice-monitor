from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class RawNotification:
    app_name: str
    title: str
    body: str
    timestamp: datetime
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WeChatNotificationEvent:
    source: str
    app_name: str
    sender: str
    preview: str
    chat_type: str
    raw_text: str
    timestamp: datetime
