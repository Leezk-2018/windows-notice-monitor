from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class StateStore:
    def __init__(self, path: str):
        self.path = Path(path)

    def load(self) -> dict[str, int]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        sessions = data.get("sessions", {})
        return {str(k): int(v) for k, v in sessions.items()}

    def save(self, sessions: dict[str, int]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessions": sessions,
            "updated_at": datetime.now(timezone.utc).astimezone().isoformat(),
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
