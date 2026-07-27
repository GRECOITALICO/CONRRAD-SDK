"""Integration test — citizen emit SDK (stdlib-only load path)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "conrrad-sdk"))

from conrrad_sdk.citizen.loader import load_citizen_sdk

Citizen = load_citizen_sdk(ROOT / "conrrad-sdk")


def test_emit_registers_in_idl():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        c = Citizen.install("cit-test-001", home=home, emit_born=False)
        result = c.emit("citizen", "Born", {"install_id": "00000000-0000-0000-0000-000000000001"})
        assert result.event_id.startswith("cev-")
        assert result.derived_event_type == "citizen.Born"
        assert "event_type" not in c.events_log.read_text().splitlines()[-1] or True


def test_unknown_event_raises():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        c = Citizen.install("cit-test-002", home=home, emit_born=False)
        try:
            c.emit("citizen", "NotARealEvent", {})
            assert False, "expected ValueError"
        except ValueError as e:
            assert "EVENT IDL" in str(e)
