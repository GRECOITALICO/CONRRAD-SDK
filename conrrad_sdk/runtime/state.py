"""Runtime state fingerprints — consume-only integrity checks (P-ARCH-01)."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class IntegrityFingerprint:
    founder_artifact_id: str
    founder_canonical_sha256: str
    citizen_birth_fingerprint: str | None
    roadmap_schema: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def capture_integrity(repo_root: Path, citizen_dir: Path | None) -> IntegrityFingerprint:
    instance_path = repo_root / ".conrrad-evidence/founder_model/instance/INSTANCE.json"
    instance = _load_json(instance_path)
    sha = instance.get("canonical_sha256", "")
    artifact_id = f"fm://sha256/{sha.strip().lower()}" if sha else ""

    birth_fp = None
    if citizen_dir and (citizen_dir / "birth_manifest.json").is_file():
        ref = _load_json(citizen_dir / "birth_manifest.json").get("founder_context_ref") or {}
        birth_fp = ref.get("birth_context_fingerprint")

    return IntegrityFingerprint(
        founder_artifact_id=artifact_id,
        founder_canonical_sha256=sha,
        citizen_birth_fingerprint=birth_fp,
        roadmap_schema="founderos.roadmap.v1",
    )


def verify_integrity(before: IntegrityFingerprint, after: IntegrityFingerprint) -> tuple[bool, str]:
    if before.founder_artifact_id != after.founder_artifact_id:
        return False, "founder artifact_id changed"
    if before.founder_canonical_sha256 != after.founder_canonical_sha256:
        return False, "founder canonical_sha256 changed"
    if before.citizen_birth_fingerprint != after.citizen_birth_fingerprint:
        return False, "citizen birth fingerprint changed"
    return True, "ok"


@dataclass
class RuntimeState:
    schema: str
    citizen_id: str
    repo_root: str
    started_at: str
    restart_count: int
    last_heartbeat: str | None
    integrity: dict[str, Any]
    pid: int | None = None

    @staticmethod
    def new(citizen_id: str, repo_root: Path, integrity: IntegrityFingerprint) -> RuntimeState:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return RuntimeState(
            schema="conrrad.runtime.state/v1",
            citizen_id=citizen_id,
            repo_root=str(repo_root.resolve()),
            started_at=now,
            restart_count=0,
            last_heartbeat=None,
            integrity=integrity.to_dict(),
            pid=None,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def load(path: Path) -> RuntimeState:
        data = _load_json(path)
        return RuntimeState(**data)
