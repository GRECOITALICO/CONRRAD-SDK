"""Runtime filesystem path defaults. Internal — not public API."""
from __future__ import annotations

import os
from pathlib import Path

_CONRRAD_HOME = Path.home() / ".conrrad"


def resolve_env_path(env_var: str, default: Path) -> Path:
    """Resolve optional env override; expanduser on override."""
    override = os.environ.get(env_var)
    return Path(override).expanduser() if override else default


def default_sully_root() -> Path:
    """Root for sully datasets, models, and shadow logs."""
    return resolve_env_path("CONRRAD_SULLY_DATA_DIR", _CONRRAD_HOME / "sully")


def default_sully_dataset_file(name: str = "sully.jsonl") -> Path:
    return default_sully_root() / name


def default_sully_models_dir() -> Path:
    return default_sully_root() / "models"


def default_sully_shadow_log() -> Path:
    return default_sully_root() / "shadow_eval.jsonl"


def default_demo_buffer_dir() -> Path:
    """Demo telemetry buffer directory."""
    return resolve_env_path("CONRRAD_DEMO_DIR", _CONRRAD_HOME / "demo")


def default_telemetry_file() -> Path:
    """Latest telemetry buffer file path."""
    root = resolve_env_path("CONRRAD_TELEMETRY_DIR", _CONRRAD_HOME / "telemetry")
    return root / "telemetry_buffer_latest.jsonl"


def default_payload_spill_dir() -> Path:
    """Directory for large execution payload spill files."""
    return resolve_env_path("CONRRAD_PAYLOAD_DIR", _CONRRAD_HOME / "payloads")


def default_escrow_db() -> Path:
    """Marketplace escrow SQLite database path."""
    return resolve_env_path("CONRRAD_ESCROW_DB", _CONRRAD_HOME / "escrow.sqlite3")


def default_tasks_file() -> Path:
    """Web dashboard persisted tasks file."""
    return resolve_env_path("CONRRAD_TASKS_PATH", _CONRRAD_HOME / "data" / "tasks.json")


def default_executions_file() -> Path:
    """Web dashboard persisted executions file."""
    return resolve_env_path("CONRRAD_EXECUTIONS_PATH", _CONRRAD_HOME / "data" / "executions.json")
