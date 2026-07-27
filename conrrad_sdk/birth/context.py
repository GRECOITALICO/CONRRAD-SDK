"""Founder Model birth-context subset export (consume-only)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

SCHEMA = "founder-model-birth-context/v1"


def _canonical_bytes(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _fingerprint(data: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def build_birth_context(instance: dict[str, Any], *, citizen_domain: str) -> dict[str, Any]:
    """Export a read-only subset of the certified Founder Model for lineage birth."""
    objectives = instance.get("objectives") or {}
    constraints = instance.get("constraints") or {}
    knowledge = instance.get("knowledge") or {}
    relationships = instance.get("relationships") or {}
    identity = instance.get("identity") or {}
    operational = instance.get("operational_context") or {}

    subset = {
        "objectives": objectives.get("declared") or [],
        "constraints": constraints.get("items") or [],
        "constraints_present": constraints.get("present", False),
        "knowledge": knowledge.get("ideas") or [],
        "relationships": relationships.get("people") or [],
        "decision_style": {},
        "uncertainty": {},
        "projects": [],
    }

    project = operational.get("project") or {}
    if project.get("vertical_slice_index"):
        subset["projects"].append("conrrad")

    body = {
        "schema": SCHEMA,
        "founder_id": instance.get("founder_id") or identity.get("founder_id"),
        "citizen_domain": citizen_domain,
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "subset": subset,
    }
    body["content_fingerprint"] = _fingerprint(subset)
    return body
