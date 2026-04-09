from __future__ import annotations

from .classifier import classify_session, should_notify
from .models import NotificationEvent, SessionSnapshot


def build_notification(snapshot: SessionSnapshot, session_type: str, notify_cfg: dict) -> NotificationEvent:
    if session_type == "group":
        title = f"微信群新消息：{snapshot.chat_name}"
    else:
        title = f"微信好友新消息：{snapshot.chat_name}"

    lines: list[str] = []
    show_sender = bool(notify_cfg.get("show_sender", True))
    show_msg_type = bool(notify_cfg.get("show_msg_type", True))
    show_summary = bool(notify_cfg.get("show_summary", True))

    prefix_parts: list[str] = []
    if session_type == "group" and show_sender and snapshot.sender:
        prefix_parts.append(snapshot.sender)
    if show_msg_type and snapshot.msg_type:
        prefix_parts.append(snapshot.msg_type)
    if prefix_parts:
        lines.append(" · ".join(prefix_parts))
    if show_summary and snapshot.last_message:
        lines.append(snapshot.last_message)
    if not lines:
        lines.append("有新消息")

    body = "\n".join(lines)
    max_len = int(notify_cfg.get("max_body_length", 160))
    if max_len > 0 and len(body) > max_len:
        body = body[: max_len - 3] + "..."

    return NotificationEvent(
        username=snapshot.username,
        session_type=session_type,
        title=title,
        body=body,
        timestamp=snapshot.timestamp,
    )


class Poller:
    def __init__(self, source, notifier, state_store, config: dict, logger):
        self.source = source
        self.notifier = notifier
        self.state_store = state_store
        self.config = config
        self.logger = logger

    def run_once(self) -> dict:
        sessions = self.source.fetch_sessions()
        current = {item.username: item.timestamp for item in sessions}
        previous = self.state_store.load()

        if not previous:
            self.state_store.save(current)
            self.logger.info("首次运行，已建立基线，共记录 %s 个会话", len(current))
            return {
                "first_run": True,
                "baseline_count": len(current),
                "notifications_sent": 0,
                "filtered": 0,
                "detected": 0,
            }

        detected = 0
        filtered = 0
        sent = 0
        new_state = dict(previous)

        for session in sorted(sessions, key=lambda item: item.timestamp):
            prev_ts = int(previous.get(session.username, 0))
            if session.timestamp <= prev_ts:
                continue
            detected += 1
            session_type = classify_session(session)
            if not should_notify(session_type, self.config["filters"]):
                filtered += 1
                self.logger.info("会话被过滤: %s (%s)", session.chat_name, session_type)
                new_state[session.username] = session.timestamp
                self.state_store.save(new_state)
                continue

            event = build_notification(session, session_type, self.config["notify"])
            self.notifier.send(event, self.config["retry"], self.logger)
            new_state[session.username] = session.timestamp
            self.state_store.save(new_state)
            sent += 1

        for username, ts in current.items():
            new_state.setdefault(username, ts)

        self.state_store.save(new_state)
        return {
            "first_run": False,
            "baseline_count": 0,
            "notifications_sent": sent,
            "filtered": filtered,
            "detected": detected,
        }
