from datetime import datetime

from src.models import RawNotification
from src.parser.wechat_notification_parser import WeChatNotificationParser


def test_parse_wechat_notification():
    parser = WeChatNotificationParser(["微信", "WeChat"])
    notification = RawNotification(
        app_name="微信",
        title="张三",
        body="晚上一起吃饭吗？",
        timestamp=datetime(2026, 4, 7, 20, 31),
    )

    event = parser.parse(notification)

    assert event is not None
    assert event.sender == "张三"
    assert event.preview == "晚上一起吃饭吗？"
    assert event.chat_type == "unknown"
