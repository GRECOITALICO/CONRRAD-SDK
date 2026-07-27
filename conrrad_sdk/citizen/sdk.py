"""
CONRRAD Citizen SDK — emit-only integration surface.

The SDK produces domain events. CONRRAD Runtime produces views.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from conrrad_sdk.citizen.fluent import CitizenLifeAPI, IntentAPI, MarketplaceAPI, MissionAPI
from conrrad_sdk.citizen.home import bootstrap_registry, resolve_citizen_home
from conrrad_sdk.events.emitter import CitizenEventEmitter, EmitResult


class Citizen:
    """
    Third-party integration entry point.

    Usage:
        citizen = Citizen.install("cit-my-agent")
        citizen.emit("mission", "Completed", {"mission_id": "m-1"})
        # or
        citizen.mission.complete("m-1", summary="done")

    The SDK never reads or writes genome.json, state.json, memory.json,
    or observability.json — that is Runtime's job.
    """

    def __init__(self, citizen_id: str, home: Path | None = None, *, actor: str = "conrrad-sdk"):
        self.citizen_id = citizen_id
        self.home = home or resolve_citizen_home(citizen_id)
        self._emitter = CitizenEventEmitter(citizen_id, self.home, actor=actor)
        self.life = CitizenLifeAPI(self)
        self.mission = MissionAPI(self)
        self.marketplace = MarketplaceAPI(self)
        self.intent = IntentAPI(self)

    @classmethod
    def install(
        cls,
        citizen_id: str | None = None,
        home: Path | None = None,
        *,
        install_id: str | None = None,
        emit_born: bool = True,
    ) -> Citizen:
        """Bootstrap registry and optionally emit citizen.Born."""
        cid = citizen_id or f"cit-{uuid.uuid4().hex[:12]}"
        resolved_home = home or resolve_citizen_home(cid)
        bootstrap_registry(cid, resolved_home)
        citizen = cls(cid, resolved_home)
        if emit_born:
            citizen.life.born(install_id or str(uuid.uuid4()))
        return citizen

    def emit(
        self,
        aggregate: str,
        event: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> EmitResult:
        return self._emitter.emit(aggregate, event, payload, **kwargs)

    @property
    def events_log(self) -> Path:
        return self._emitter.events_path
