from datetime import datetime

from src.listener.windows_notifications import MockNotificationListener, WindowsNotificationListener
from src.models import RawNotification


def test_mock_notification_listener_returns_raw_notification():
    listener = MockNotificationListener()

    notifications = list(listener.get_notifications())

    assert len(notifications) == 1
    notification = notifications[0]
    assert isinstance(notification, RawNotification)
    assert notification.app_name == "微信"
    assert notification.title == "张三"


def test_windows_notification_listener_gracefully_handles_poller_failure():
    listener = WindowsNotificationListener(poller=lambda: (_ for _ in ()).throw(RuntimeError("boom")))

    notifications = list(listener.get_notifications())

    assert notifications == []


def test_windows_notification_listener_filters_seen_notification_ids():
    first = RawNotification(
        app_name="微信",
        title="张三",
        body="你好",
        timestamp=datetime(2026, 4, 7, 22, 0),
        raw_payload={"id": "1"},
    )
    second = RawNotification(
        app_name="微信",
        title="李四",
        body="在吗",
        timestamp=datetime(2026, 4, 7, 22, 1),
        raw_payload={"id": "2"},
    )
    batches = iter([[first, second], [first, second]])
    listener = WindowsNotificationListener(poller=lambda: next(batches))

    first_batch = list(listener.get_notifications())
    second_batch = list(listener.get_notifications())

    assert [item.raw_payload["id"] for item in first_batch] == ["1", "2"]
    assert second_batch == []


def test_windows_notification_listener_maps_dict_to_raw_notification():
    listener = WindowsNotificationListener(poller=lambda: [])

    notification = listener._to_raw_notification(
        {
            "id": "42",
            "app_name": "微信",
            "title": "群聊",
            "body": "张三: 你好",
            "timestamp": "2026-04-07T22:00:00+08:00",
            "raw_text": "群聊\n张三: 你好",
        }
    )

    assert notification.app_name == "微信"
    assert notification.title == "群聊"
    assert notification.body == "张三: 你好"
    assert notification.raw_payload["id"] == "42"
