from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SessionSnapshot:
    username: str
    chat_name: str
    sender: str
    msg_type: str
    last_message: str
    timestamp: int
    unread: int
    is_group: bool
    verify_flag: int = 0
    local_type: int = 0
    is_subscription: bool = False


@dataclass(slots=True)
class NotificationEvent:
    username: str
    session_type: str
    title: str
    body: str
    timestamp: int
