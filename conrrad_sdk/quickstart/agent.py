"""Minimal Agent for first-run developer experience (public vocabulary only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class RunResult:
    """Outcome of a local task run."""

    answer: str
    audit_trail: list[dict[str, Any]] = field(default_factory=list)
    cost: str = "Local execution"

    def __str__(self) -> str:
        return self.answer


@dataclass
class Agent:
    """
    Public Quick Start Agent.

    Runs tasks locally with an audit trail. No infrastructure services required.
    For production deploy, use ``conrrad deploy`` (platform vocabulary).
    """

    name: str = "hello"

    def __post_init__(self) -> None:
        self._session_id = uuid.uuid4().hex[:12]

    def run(self, task: str) -> RunResult:
        if not task or not task.strip():
            raise ValueError("task must be a non-empty string")

        ts = datetime.now(timezone.utc).isoformat()
        audit: list[dict[str, Any]] = [
            {"step": "agent_started", "agent": self.name, "session": self._session_id, "at": ts},
            {"step": "task_received", "task": task.strip(), "at": ts},
        ]

        # Local-first path: deterministic demo response without external services.
        answer = (
            f"Completed locally: {task.strip()} "
            f"(session {self._session_id}; connect an LLM provider to enable full inference)."
        )
        audit.append({"step": "task_completed", "status": "success", "at": ts})

        return RunResult(answer=answer, audit_trail=audit, cost="Local execution")
