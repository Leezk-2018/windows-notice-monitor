import unittest

from pc_wechat_bark.classifier import classify_session, should_notify
from pc_wechat_bark.models import SessionSnapshot


class ClassifierTests(unittest.TestCase):
    def test_group_classification(self):
        session = SessionSnapshot(
            username="123@chatroom",
            chat_name="群",
            sender="张三",
            msg_type="文本",
            last_message="hi",
            timestamp=1,
            unread=1,
            is_group=True,
        )
        self.assertEqual(classify_session(session), "group")

    def test_official_classification(self):
        session = SessionSnapshot(
            username="gh_abc",
            chat_name="公众号",
            sender="",
            msg_type="文本",
            last_message="hi",
            timestamp=1,
            unread=1,
            is_group=False,
            is_subscription=True,
        )
        self.assertEqual(classify_session(session), "official")

    def test_friend_classification(self):
        session = SessionSnapshot(
            username="wxid_a",
            chat_name="好友",
            sender="",
            msg_type="文本",
            last_message="hi",
            timestamp=1,
            unread=1,
            is_group=False,
        )
        self.assertEqual(classify_session(session), "friend")

    def test_should_notify(self):
        filters = {
            "include_groups": True,
            "include_friends": True,
            "exclude_official_accounts": True,
            "include_unknown": False,
        }
        self.assertTrue(should_notify("group", filters))
        self.assertTrue(should_notify("friend", filters))
        self.assertFalse(should_notify("official", filters))
        self.assertFalse(should_notify("unknown", filters))


if __name__ == "__main__":
    unittest.main()
