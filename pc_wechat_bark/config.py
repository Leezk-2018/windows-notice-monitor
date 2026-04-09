from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CONFIG: dict[str, Any] = {
    "wechat": {
        "config_path": "",
    },
    "poll": {
        "interval_seconds": 15,
        "first_run_mode": "baseline_only",
    },
    "filters": {
        "include_groups": True,
        "include_friends": True,
        "exclude_official_accounts": True,
        "include_unknown": False,
    },
    "bark": {
        "server": "https://api.day.app",
        "device_key": "YOUR_DEVICE_KEY",
        "group": "wechat",
        "sound": "",
        "icon": "",
        "url": "",
    },
    "notify": {
        "show_sender": True,
        "show_msg_type": True,
        "show_summary": True,
        "max_body_length": 160,
    },
    "retry": {
        "max_attempts": 3,
        "backoff_seconds": [1, 3, 10],
    },
    "logging": {
        "level": "INFO",
        "file": "",
    },
    "state": {
        "path": "~/.pc-wechat-bark/state.json",
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _normalize_paths(config: dict[str, Any], config_path: Path) -> dict[str, Any]:
    state_path = Path(os.path.expanduser(str(config["state"]["path"])))
    config["state"]["path"] = str(state_path)

    wechat_path = str(config["wechat"].get("config_path", "") or "").strip()
    if wechat_path:
        config["wechat"]["config_path"] = str(Path(os.path.expanduser(wechat_path)))

    log_file = str(config["logging"].get("file", "") or "").strip()
    if log_file:
        config["logging"]["file"] = str(Path(os.path.expanduser(log_file)))

    config["meta"] = {"config_path": str(config_path)}
    return config


def load_config(path: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    target = Path(path or "config.toml")
    if not target.exists():
        raise FileNotFoundError(f"配置文件不存在: {target}")

    with target.open("rb") as f:
        user_config = tomllib.load(f)
    merged = _deep_merge(DEFAULT_CONFIG, user_config)
    return _normalize_paths(merged, target.resolve())


def render_default_config() -> str:
    return """[wechat]
config_path = ""

[poll]
interval_seconds = 15
first_run_mode = "baseline_only"

[filters]
include_groups = true
include_friends = true
exclude_official_accounts = true
include_unknown = false

[bark]
server = "https://api.day.app"
device_key = "YOUR_DEVICE_KEY"
group = "wechat"
sound = ""
icon = ""
url = ""

[notify]
show_sender = true
show_msg_type = true
show_summary = true
max_body_length = 160

[retry]
max_attempts = 3
backoff_seconds = [1, 3, 10]

[logging]
level = "INFO"
file = ""

[state]
path = "~/.pc-wechat-bark/state.json"
"""


def write_default_config(path: str | os.PathLike[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(f"配置文件已存在: {target}")
    target.write_text(render_default_config(), encoding="utf-8")
    return target
