from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional


class MemoryStore:
    """Append-only turn memory persisted under project workspace (VS-03)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.is_file():
            self._write({"sessions": {}})

    def _read(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"sessions": {}}

    def _write(self, data: dict[str, Any]) -> None:
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def last_turn(self, session_id: str) -> Optional[dict[str, Any]]:
        sessions = self._read().get("sessions", {})
        turns = sessions.get(session_id, [])
        return turns[-1] if turns else None

    def append(self, session_id: str, turn: dict[str, Any]) -> None:
        data = self._read()
        sessions = data.setdefault("sessions", {})
        sessions.setdefault(session_id, []).append(turn)
        self._write(data)

    def turn_count(self, session_id: str) -> int:
        return len(self._read().get("sessions", {}).get(session_id, []))
