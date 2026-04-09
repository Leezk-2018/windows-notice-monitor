import unittest
from pathlib import Path
import shutil
import uuid

from pc_wechat_bark.poller import Poller, build_notification
from pc_wechat_bark.models import SessionSnapshot
from pc_wechat_bark.state import StateStore


class FakeSource:
    def __init__(self, sessions):
        self.sessions = sessions

    def fetch_sessions(self):
        return list(self.sessions)


class FakeNotifier:
    def __init__(self, fail=False):
        self.fail = fail
        self.events = []

    def send(self, event, retry, logger):
        if self.fail:
            raise RuntimeError("send failed")
        self.events.append((event, retry))


class FakeLogger:
    def info(self, *args, **kwargs):
        return None

    def warning(self, *args, **kwargs):
        return None


def make_config(state_path):
    return {
        "filters": {
            "include_groups": True,
            "include_friends": True,
            "exclude_official_accounts": True,
            "include_unknown": False,
        },
        "notify": {
            "show_sender": True,
            "show_msg_type": True,
            "show_summary": True,
            "max_body_length": 20,
        },
        "retry": {
            "max_attempts": 3,
            "backoff_seconds": [1, 3, 10],
        },
        "state": {"path": str(state_path)},
    }


def make_workspace_dir() -> Path:
    root = Path(__file__).resolve().parent / ".tmp"
    path = root / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


class PollerTests(unittest.TestCase):
    def test_first_run_baseline_only(self):
        tmp = make_workspace_dir()
        try:
            path = tmp / "state.json"
            sessions = [
                SessionSnapshot("wxid_a", "好友", "", "文本", "hello", 10, 1, False),
            ]
            poller = Poller(FakeSource(sessions), FakeNotifier(), StateStore(str(path)), make_config(path), FakeLogger())
            result = poller.run_once()
            self.assertTrue(result["first_run"])
            self.assertEqual(result["notifications_sent"], 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_send_new_friend_message(self):
        tmp = make_workspace_dir()
        try:
            path = tmp / "state.json"
            store = StateStore(str(path))
            store.save({"wxid_a": 10})
            sessions = [
                SessionSnapshot("wxid_a", "好友", "", "文本", "hello world", 20, 1, False),
            ]
            notifier = FakeNotifier()
            poller = Poller(FakeSource(sessions), notifier, store, make_config(path), FakeLogger())
            result = poller.run_once()
            self.assertFalse(result["first_run"])
            self.assertEqual(result["notifications_sent"], 1)
            self.assertEqual(len(notifier.events), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_official_filtered(self):
        tmp = make_workspace_dir()
        try:
            path = tmp / "state.json"
            store = StateStore(str(path))
            store.save({"gh_abc": 10})
            sessions = [
                SessionSnapshot("gh_abc", "公众号", "", "文本", "hello world", 20, 1, False, verify_flag=8, is_subscription=True),
            ]
            notifier = FakeNotifier()
            poller = Poller(FakeSource(sessions), notifier, store, make_config(path), FakeLogger())
            result = poller.run_once()
            self.assertEqual(result["filtered"], 1)
            self.assertEqual(len(notifier.events), 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_failed_send_does_not_advance_state(self):
        tmp = make_workspace_dir()
        try:
            path = tmp / "state.json"
            store = StateStore(str(path))
            store.save({"wxid_a": 10})
            sessions = [
                SessionSnapshot("wxid_a", "好友", "", "文本", "hello world", 20, 1, False),
            ]
            poller = Poller(FakeSource(sessions), FakeNotifier(fail=True), store, make_config(path), FakeLogger())
            with self.assertRaises(RuntimeError):
                poller.run_once()
            self.assertEqual(store.load()["wxid_a"], 10)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_build_notification_truncates(self):
        session = SessionSnapshot("123@chatroom", "群聊", "张三", "文本", "abcdefghijklmnopqrstuvwxyz", 20, 1, True)
        event = build_notification(session, "group", {"show_sender": True, "show_msg_type": True, "show_summary": True, "max_body_length": 20})
        self.assertTrue(event.body.endswith("..."))


if __name__ == "__main__":
    unittest.main()
