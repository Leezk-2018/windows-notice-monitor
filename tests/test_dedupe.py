from datetime import datetime

from src.dedupe.memory_dedupe import MemoryDeduper
from src.models import WeChatNotificationEvent


def test_memory_deduper_blocks_duplicate_within_ttl():
    deduper = MemoryDeduper(ttl_seconds=10)
    event = WeChatNotificationEvent(
        source="wechat_windows_notification",
        app_name="微信",
        sender="张三",
        preview="你好",
        chat_type="unknown",
        raw_text="张三\n你好",
        timestamp=datetime(2026, 4, 7, 20, 31),
    )

    assert deduper.is_duplicate(event) is False
    assert deduper.is_duplicate(event) is True
