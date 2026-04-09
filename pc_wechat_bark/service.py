from __future__ import annotations

import time


class Service:
    def __init__(self, poller, interval_seconds: int, logger):
        self.poller = poller
        self.interval_seconds = max(1, int(interval_seconds))
        self.logger = logger

    def run_forever(self) -> None:
        self.logger.info("服务启动，轮询间隔 %s 秒", self.interval_seconds)
        try:
            while True:
                result = self.poller.run_once()
                self.logger.info("本轮完成: %s", result)
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，服务退出")
