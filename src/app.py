from __future__ import annotations

import argparse
import logging
import time
from typing import Any

from src.config import load_config
from src.dedupe.memory_dedupe import MemoryDeduper
from src.listener.windows_notifications import MockNotificationListener, WindowsNotificationListener
from src.notifiers.bark_notifier import BarkNotifier
from src.notifiers.wxpusher_notifier import WxPusherNotifier
from src.parser.wechat_notification_parser import WeChatNotificationParser
from src.store.state_store import StateStore


LOG = logging.getLogger(__name__)


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


def build_notifiers(config: dict[str, Any]) -> list[Any]:
    push_config = config.get("push", {})
    bark_config = push_config.get("bark", {})
    wxpusher_config = push_config.get("wxpusher", {})
    notifiers: list[Any] = []

    if bark_config.get("enabled"):
        notifiers.append(
            BarkNotifier(
                server=bark_config.get("server", "https://api.day.app"),
                key=bark_config.get("key", ""),
                group=bark_config.get("group"),
            )
        )

    if wxpusher_config.get("enabled"):
        notifiers.append(
            WxPusherNotifier(
                app_token=wxpusher_config.get("app_token", ""),
                uids=wxpusher_config.get("uids", []),
            )
        )

    return notifiers


def build_listener(config: dict[str, Any]):
    runtime = config.get("runtime", {})
    if runtime.get("use_mock_listener", False):
        return MockNotificationListener()
    return WindowsNotificationListener()


def run_once(config: dict[str, Any]) -> int:
    listener = build_listener(config)
    parser = WeChatNotificationParser(config.get("source", {}).get("app_names", ["微信", "WeChat"]))
    deduper = MemoryDeduper(ttl_seconds=int(config.get("dedupe", {}).get("ttl_seconds", 10)))
    notifiers = build_notifiers(config)
    store = StateStore()

    sent_count = 0
    for notification in listener.get_notifications():
        event = parser.parse(notification)
        if not event:
            continue
        if deduper.is_duplicate(event):
            LOG.info("Skip duplicate notification from %s", event.sender)
            continue

        store.append_event(event)
        for notifier in notifiers:
            notifier.send(event)
        sent_count += 1
        LOG.info("Processed notification from %s", event.sender)

    return sent_count


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--config", default="config.yaml")
    cli.add_argument("--loop", action="store_true")
    cli.add_argument("--once", action="store_true")
    args = cli.parse_args()

    config = load_config(args.config)
    setup_logging(config.get("runtime", {}).get("log_level", "INFO"))

    if args.loop and args.once:
        raise SystemExit("--loop and --once cannot be used together")

    if not args.loop:
        count = run_once(config)
        LOG.info("Run finished, processed %s notifications", count)
        return

    interval = int(config.get("runtime", {}).get("poll_interval_seconds", 2))
    while True:
        try:
            run_once(config)
        except Exception:
            LOG.exception("Notification loop failed")
        time.sleep(interval)


if __name__ == "__main__":
    main()
