"""Citizen domain event emitter — append-only, envelope v1.3."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from conrrad_sdk.events.idl import assert_citizen_event_registered, canonical_event_type, idl_payload_version


@dataclass
class EmitResult:
    event_id: str
    aggregate: str
    event: str
    derived_event_type: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "aggregate": self.aggregate,
            "event": self.event,
            "event_type": self.derived_event_type,
        }


@dataclass
class CitizenEventEmitter:
    """
    Emit-only interface to citizen-events.jsonl.

    Does NOT read or write Genome, State, Memory, or Observability.
    """

    citizen_id: str
    citizen_home: Path
    actor: str = "conrrad-sdk"
    _idl_domain: str = field(default="citizen", init=False, repr=False)

    @property
    def registry_path(self) -> Path:
        return self.citizen_home / "citizen-registry.json"

    @property
    def events_path(self) -> Path:
        reg = json.loads(self.registry_path.read_text(encoding="utf-8"))
        return self.citizen_home / reg["history"]["event_log"]

    def _next_event_id(self) -> str:
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        n = 1
        path = self.events_path
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip() and f"cev-{day}-" in line:
                    n += 1
        return f"cev-{day}-{n:04d}"

    def emit(
        self,
        aggregate: str,
        event: str,
        payload: dict[str, Any],
        *,
        project_id: str | None = None,
        actor: str | None = None,
        causation_id: str | None = None,
        correlation_id: str | None = None,
        dry_run: bool = False,
    ) -> EmitResult:
        entry = assert_citizen_event_registered(aggregate, event)
        now = datetime.now(timezone.utc).isoformat()
        record = {
            "id": self._next_event_id(),
            "event_class": "domain",
            "aggregate": aggregate,
            "event": event,
            "schema_version": idl_payload_version(entry),
            "occurred_at": now,
            "recorded_at": now,
            "actor": actor or self.actor,
            "citizen_id": self.citizen_id,
            "project_id": project_id,
            "payload": payload,
            "evidence_ref": [],
        }
        if causation_id:
            record["causation_id"] = causation_id
        if correlation_id:
            record["correlation_id"] = correlation_id

        derived = canonical_event_type(aggregate, event)
        if dry_run:
            return EmitResult(record["id"], aggregate, event, derived)

        if not self.registry_path.is_file():
            raise FileNotFoundError(
                f"citizen registry not found: {self.registry_path} — call Citizen.install() first"
            )
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
        return EmitResult(record["id"], aggregate, event, derived)
