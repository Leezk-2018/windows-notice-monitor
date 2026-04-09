from __future__ import annotations

from .models import SessionSnapshot


OFFICIAL_LOCAL_TYPE_FLAGS = {
    8,
    24,
    104,
    136,
    280,
    288,
    816,
}


def classify_session(snapshot: SessionSnapshot) -> str:
    if snapshot.is_group or "@chatroom" in snapshot.username:
        return "group"

    if snapshot.username.startswith("gh_") or snapshot.is_subscription:
        return "official"

    if snapshot.verify_flag > 0:
        return "official"

    if snapshot.local_type in OFFICIAL_LOCAL_TYPE_FLAGS:
        return "official"

    if snapshot.username:
        return "friend"

    return "unknown"


def should_notify(session_type: str, filters: dict) -> bool:
    if session_type == "group":
        return bool(filters.get("include_groups", True))
    if session_type == "friend":
        return bool(filters.get("include_friends", True))
    if session_type == "official":
        return not bool(filters.get("exclude_official_accounts", True))
    return bool(filters.get("include_unknown", False))
