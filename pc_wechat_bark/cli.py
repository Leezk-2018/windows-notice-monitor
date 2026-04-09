from __future__ import annotations

import logging
import sys

import click

from . import __version__
from .bark import BarkClient
from .config import load_config, write_default_config
from .poller import Poller
from .service import Service
from .source import WeChatSource
from .state import StateStore


def _setup_logger(config: dict) -> logging.Logger:
    logger = logging.getLogger("pc_wechat_bark")
    logger.setLevel(getattr(logging, str(config["logging"].get("level", "INFO")).upper(), logging.INFO))
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    log_file = str(config["logging"].get("file", "") or "").strip()
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def _build_runtime(config_path: str):
    config = load_config(config_path)
    logger = _setup_logger(config)
    source = WeChatSource(config["wechat"].get("config_path", ""))
    notifier = BarkClient(config["bark"])
    state = StateStore(config["state"]["path"])
    poller = Poller(source, notifier, state, config, logger)
    return config, logger, source, notifier, state, poller


@click.group()
@click.version_option(version=__version__, prog_name="pc-wechat-bark")
def cli():
    """pc-wechat-bark 命令行入口"""


@cli.command("init-config", short_help="生成默认配置文件")
@click.option("--path", "config_path", default="config.toml", help="输出配置文件路径")
def init_config(config_path: str):
    """生成默认配置文件。"""
    path = write_default_config(config_path)
    click.echo(f"已生成配置文件: {path}")


@cli.command("doctor", short_help="检查配置、Bark 和 wechat_cli 环境")
@click.option("--config", "config_path", default="config.toml", help="配置文件路径")
def doctor(config_path: str):
    """检查配置、Bark 与 wechat_cli 数据源。"""
    try:
        config = load_config(config_path)
    except Exception as e:
        click.echo(f"[FAIL] 配置加载失败: {e}")
        raise SystemExit(1)

    click.echo(f"[OK] 配置加载成功: {config['meta']['config_path']}")
    bark = BarkClient(config["bark"])
    errors = bark.validate()
    if errors:
        for error in errors:
            click.echo(f"[FAIL] {error}")
        raise SystemExit(1)
    click.echo("[OK] Bark 配置完整")

    try:
        source = WeChatSource(config["wechat"].get("config_path", ""))
        sessions = source.fetch_sessions()
    except Exception as e:
        click.echo(f"[FAIL] wechat_cli 数据源不可用: {e}")
        raise SystemExit(1)
    click.echo(f"[OK] wechat_cli 数据源可用，会话数: {len(sessions)}")


@cli.command("check", short_help="执行一次检查并按需推送")
@click.option("--config", "config_path", default="config.toml", help="配置文件路径")
def check(config_path: str):
    """执行一次检查并按需推送。"""
    config, logger, _source, _notifier, _state, poller = _build_runtime(config_path)
    errors = BarkClient(config["bark"]).validate()
    if errors:
        for error in errors:
            click.echo(f"[FAIL] {error}")
        raise SystemExit(1)
    result = poller.run_once()
    logger.info("单次检查完成: %s", result)
    click.echo(result)


@cli.command("run", short_help="常驻运行，持续轮询并推送")
@click.option("--config", "config_path", default="config.toml", help="配置文件路径")
def run(config_path: str):
    """常驻运行，持续轮询并推送。"""
    config, logger, _source, _notifier, _state, poller = _build_runtime(config_path)
    errors = BarkClient(config["bark"]).validate()
    if errors:
        for error in errors:
            click.echo(f"[FAIL] {error}")
        raise SystemExit(1)
    service = Service(poller, config["poll"]["interval_seconds"], logger)
    service.run_forever()


@cli.command("version", short_help="显示当前版本号")
def version():
    """显示版本号"""
    click.echo(__version__)


if __name__ == "__main__":
    cli()
