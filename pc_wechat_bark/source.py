from __future__ import annotations

import os
import sqlite3
from contextlib import closing

from .models import SessionSnapshot


class WeChatSource:
    def __init__(self, config_path: str = ""):
        from wechat_cli.core.context import AppContext
        from wechat_cli.core.contacts import get_contact_detail, get_contact_names
        from wechat_cli.core.messages import decompress_content, format_msg_type

        self._get_contact_detail = get_contact_detail
        self._get_contact_names = get_contact_names
        self._decompress_content = decompress_content
        self._format_msg_type = format_msg_type
        self.app = AppContext(config_path or None)

    def fetch_sessions(self) -> list[SessionSnapshot]:
        path = self.app.cache.get(os.path.join("session", "session.db"))
        if not path:
            raise RuntimeError("无法解密 session.db")

        names = self._get_contact_names(self.app.cache, self.app.decrypted_dir)
        with closing(sqlite3.connect(path)) as conn:
            rows = conn.execute(
                """
                SELECT username, unread_count, summary, last_timestamp,
                       last_msg_type, last_msg_sender, last_sender_display_name
                FROM SessionTable
                WHERE last_timestamp > 0
                ORDER BY last_timestamp DESC
                """
            ).fetchall()

        snapshots: list[SessionSnapshot] = []
        for username, unread, summary, ts, msg_type, sender, sender_name in rows:
            display = names.get(username, username)
            is_group = "@chatroom" in username

            if isinstance(summary, bytes):
                summary = self._decompress_content(summary, 4) or "(压缩内容)"
            if isinstance(summary, str) and ":\n" in summary:
                summary = summary.split(":\n", 1)[1]

            sender_display = ""
            if is_group and sender:
                sender_display = names.get(sender, sender_name or sender)

            detail = self._get_contact_detail(username, self.app.cache, self.app.decrypted_dir) or {}
            snapshots.append(
                SessionSnapshot(
                    username=username,
                    chat_name=display,
                    sender=sender_display,
                    msg_type=self._format_msg_type(msg_type),
                    last_message=str(summary or ""),
                    timestamp=int(ts or 0),
                    unread=int(unread or 0),
                    is_group=is_group,
                    verify_flag=int(detail.get("verify_flag") or 0),
                    local_type=int(detail.get("local_type") or 0),
                    is_subscription=bool(detail.get("is_subscription")),
                )
            )

        return snapshots
