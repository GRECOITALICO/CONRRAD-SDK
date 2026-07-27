"""CONRRAD Event IDL helpers for SDK emitters — no Runtime dependency."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path


def canonical_event_type(aggregate: str, event: str) -> str:
    return f"{aggregate}.{event}"


def _idl_search_paths() -> list[Path]:
    paths: list[Path] = []
    if env := os.environ.get("CONRRAD_EVENT_IDL"):
        paths.append(Path(env))
    bundled = Path(__file__).resolve().parent / "data" / "EVENT_IDL.json"
    paths.append(bundled)
    # Monorepo dev fallback
    repo = Path(__file__).resolve().parents[3]
    paths.append(repo / "docs" / "events" / "EVENT_IDL.json")
    return paths


@lru_cache(maxsize=1)
def load_idl() -> dict:
    for path in _idl_search_paths():
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    return {"domains": {"citizen": {}}}


def idl_entry(domain: str, aggregate: str, event: str) -> dict | None:
    section = load_idl().get("domains", {}).get(domain, {})
    agg = section.get(aggregate)
    if isinstance(agg, dict) and event in agg:
        entry = agg[event]
        return entry if isinstance(entry, dict) else None
    return None


def idl_payload_version(entry: dict) -> int:
    return int(entry.get("payload_version", entry.get("version", 1)))


def assert_citizen_event_registered(aggregate: str, event: str) -> dict:
    entry = idl_entry("citizen", aggregate, event)
    if not entry:
        raise ValueError(f"unknown citizen event: {aggregate}.{event} — not in EVENT IDL")
    return entry
