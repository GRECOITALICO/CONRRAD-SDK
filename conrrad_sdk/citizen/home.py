"""Citizen home layout — registry bootstrap without touching read models."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def resolve_citizen_home(citizen_id: str) -> Path:
    if explicit := os.environ.get("CONRRAD_CITIZEN_HOME"):
        return Path(explicit)
    if root := os.environ.get("CONRRAD_ROOT"):
        return Path(root) / "citizens" / citizen_id
    return Path.home() / ".conrrad" / "citizens" / citizen_id


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def bootstrap_registry(citizen_id: str, home: Path | None = None) -> Path:
    """Create citizen-registry.json — required before any emit."""
    base = home or resolve_citizen_home(citizen_id)
    base.mkdir(parents=True, exist_ok=True)
    reg_path = base / "citizen-registry.json"
    if reg_path.is_file():
        return reg_path
    reg = {
        "schema": "citizen-registry/v1",
        "updated_at": utc_now_iso(),
        "citizen_id": citizen_id,
        "history": {"event_log": "citizen-events.jsonl"},
        "artifacts": {
            "genome": "genome.json",
            "state": "state.json",
            "observability": "observability.json",
            "memory": "memory.json",
        },
    }
    reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
    events = base / reg["history"]["event_log"]
    if not events.is_file():
        events.write_text("# Citizen domain events — APPEND ONLY\n", encoding="utf-8")
    return reg_path
