from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.models import WeChatNotificationEvent


class StateStore:
    def __init__(self, path: str | Path = "runtime_state.json") -> None:
        self._path = Path(path)

    def append_event(self, event: WeChatNotificationEvent) -> None:
        state = self._read_state()
        events = state.setdefault("events", [])
        payload: dict[str, Any] = asdict(event)
        payload["timestamp"] = event.timestamp.isoformat()
        events.append(payload)
        state["events"] = events[-200:]
        self._write_state(state)

    def _read_state(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _write_state(self, state: dict[str, Any]) -> None:
        self._path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
