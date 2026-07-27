"""Fluent emit APIs — syntactic sugar over Citizen.emit()."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from conrrad_sdk.citizen.sdk import Citizen


class _AggregateAPI:
    def __init__(self, citizen: Citizen, aggregate: str):
        self._citizen = citizen
        self._aggregate = aggregate

    def emit(self, event: str, payload: dict[str, Any], **kwargs):
        return self._citizen.emit(self._aggregate, event, payload, **kwargs)


class MissionAPI(_AggregateAPI):
    def __init__(self, citizen: Citizen):
        super().__init__(citizen, "mission")

    def started(self, mission_id: str, *, project_id: str | None = None, **extra: Any):
        payload = {"mission_id": mission_id, **extra}
        return self._citizen.emit("mission", "Started", payload, project_id=project_id)

    def complete(self, mission_id: str, *, project_id: str | None = None, summary: str = "", **extra: Any):
        payload = {"mission_id": mission_id, "summary": summary, **extra}
        return self._citizen.emit("mission", "Completed", payload, project_id=project_id)


class MarketplaceAPI(_AggregateAPI):
    def __init__(self, citizen: Citizen):
        super().__init__(citizen, "marketplace")

    def job_finished(
        self,
        job_id: str,
        capability_id: str,
        *,
        success: bool = True,
        runtime_hours: float | None = None,
        **extra: Any,
    ):
        payload = {
            "job_id": job_id,
            "capability_id": capability_id,
            "success": success,
            **extra,
        }
        if runtime_hours is not None:
            payload["runtime_hours"] = runtime_hours
        return self._citizen.emit("marketplace", "JobFinished", payload)


class CitizenLifeAPI(_AggregateAPI):
    def __init__(self, citizen: Citizen):
        super().__init__(citizen, "citizen")

    def born(self, install_id: str, **extra: Any):
        return self._citizen.emit("citizen", "Born", {"install_id": install_id, **extra})

    def enrolled(self, streams_enabled: list[str] | None = None, **extra: Any):
        payload = extra.copy()
        if streams_enabled:
            payload["streams_enabled"] = streams_enabled
        return self._citizen.emit("citizen", "Enrolled", payload)

    def capability_updated(self, skill_id: str, *, action: str = "add_certified", **extra: Any):
        return self._citizen.emit(
            "citizen",
            "CapabilityUpdated",
            {"skill_id": skill_id, "action": action, **extra},
        )


class IntentAPI(_AggregateAPI):
    def __init__(self, citizen: Citizen):
        super().__init__(citizen, "intent")

    def create(
        self,
        intent_id: str,
        capability_urn: str,
        inputs: dict[str, Any] | None = None,
        *,
        intent_type: str = "P-EXINT-1",
        **extra: Any,
    ):
        payload = {
            "intent_id": intent_id,
            "capability_urn": capability_urn,
            "inputs": inputs or {},
            "type": intent_type,
            **extra,
        }
        return self._citizen.emit("intent", "Created", payload)
