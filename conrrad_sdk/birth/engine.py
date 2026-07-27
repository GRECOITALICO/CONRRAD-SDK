"""VS-05 Birth Engine — consume-only bootstrap from a certified Founder bundle."""
from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from conrrad_sdk.birth.context import build_birth_context

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
DEFAULT_FM_DIR = ".conrrad-evidence/founder_model/instance"
DEFAULT_VS_INDEX = ".conrrad-evidence/vertical_slice_v1.json"
DEFAULT_FO_INDEX = ".conrrad-evidence/founderos_v1.json"
BIRTH_MANIFEST_SCHEMA = "citizen-birth-manifest/v1"
LINEAGE_TEMPLATE = "lineage"


@dataclass
class BirthResult:
    citizen_id: str
    citizen_dir: Path
    birth_manifest_path: Path
    birth_context_path: Path
    founder_artifact_id: str


class BirthError(Exception):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _step_status(index_path: Path, step_id: str, *, section: str) -> str:
    data = _load_json(index_path)
    if section == "vs":
        steps = (data.get("vertical_slice") or {}).get("steps") or []
    else:
        steps = (data.get("founderos") or {}).get("steps") or []
    for step in steps:
        if step.get("id") == step_id:
            return step.get("status", "VERIFY")
    return "VERIFY"


def _import_fm_tools(repo_root: Path):
    fm_scripts = repo_root / "scripts" / "founder_model"
    if str(fm_scripts) not in sys.path:
        sys.path.insert(0, str(fm_scripts))
    from fm_sign import public_key_path, verify_signature_record  # noqa: WPS433
    from fm_serialize import load_instance, verify_identity  # noqa: WPS433

    return load_instance, verify_identity, verify_signature_record, public_key_path


def _import_roadmap(repo_root: Path):
    services = repo_root / "services"
    if str(services) not in sys.path:
        sys.path.insert(0, str(services))
    from founderos.roadmap_engine import build_roadmap_view  # noqa: WPS433

    return build_roadmap_view


class BirthEngine:
    """Verify a certified Founder bundle and bootstrap a lineage Citizen."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root.resolve()
        self.fm_dir = self.repo_root / DEFAULT_FM_DIR

    def verify_gates(self) -> None:
        vs_index = self.repo_root / DEFAULT_VS_INDEX
        fo_index = self.repo_root / DEFAULT_FO_INDEX
        for path in (vs_index, fo_index):
            if not path.is_file():
                raise BirthError(f"index missing: {path}")

        required = [
            (vs_index, "VS-04", "vs"),
            (fo_index, "FO-00", "fo"),
            (fo_index, "FO-01", "fo"),
        ]
        for index_path, step_id, section in required:
            status = _step_status(index_path, step_id, section=section)
            if status != "PASS":
                raise BirthError(f"gate {step_id} is {status}, required PASS")

    def verify_founder_bundle(self) -> dict[str, Any]:
        instance_path = self.fm_dir / "INSTANCE.json"
        identity_path = self.fm_dir / "identity.json"
        manifest_path = self.fm_dir / "manifest.json"
        signature_path = self.fm_dir / "signature.json"

        for path in (instance_path, identity_path, manifest_path, signature_path):
            if not path.is_file():
                raise BirthError(f"founder bundle incomplete: missing {path.name}")

        load_instance, verify_identity, verify_signature_record, public_key_path = _import_fm_tools(
            self.repo_root
        )

        if not public_key_path(self.repo_root).is_file():
            raise BirthError("trust root public key missing")

        instance = load_instance(instance_path)
        if not verify_identity(instance):
            raise BirthError("founder INSTANCE hash invalid (corrupt)")

        identity = _load_json(identity_path)
        signature = _load_json(signature_path)
        artifact_id = instance.get("canonical_sha256")
        if artifact_id:
            expected_uri = f"fm://sha256/{artifact_id.strip().lower()}"
        else:
            raise BirthError("canonical_sha256 missing on INSTANCE")

        for label, record in (("identity", identity), ("signature", signature)):
            if record.get("artifact_id") != expected_uri:
                raise BirthError(f"artifact_id mismatch in {label}")
            if record.get("canonical_sha256") != artifact_id:
                raise BirthError(f"canonical_sha256 mismatch in {label}")

        ok, msg = verify_signature_record(
            self.repo_root, instance_path, manifest_path, signature_path
        )
        if not ok:
            raise BirthError(f"signature verification failed: {msg}")

        constraints = instance.get("constraints")
        if constraints is None:
            raise BirthError("constraints block missing from founder INSTANCE")

        return {
            "instance": instance,
            "identity": identity,
            "signature": signature,
            "artifact_id": expected_uri,
        }

    def verify_roadmap_sync(self, bundle: dict[str, Any]) -> dict[str, Any]:
        build_roadmap_view = _import_roadmap(self.repo_root)
        roadmap = build_roadmap_view(self.repo_root)
        link = roadmap.get("founder_model_link") or {}
        instance = bundle["instance"]
        identity = bundle["identity"]

        checks = [
            link.get("instance_id") == instance.get("instance_id"),
            link.get("canonical_sha256") == instance.get("canonical_sha256"),
            link.get("artifact_id") == bundle["artifact_id"],
            link.get("parent_artifact_id") == identity.get("parent_artifact_id"),
            roadmap.get("schema") == "founderos.roadmap.v1",
            roadmap.get("read_only") is True,
        ]
        if not all(checks):
            raise BirthError("roadmap not synchronized with founder bundle")

        return roadmap

    def bootstrap(
        self,
        citizen_id: str,
        *,
        citizen_domain: str = "platform",
        output_dir: Path | None = None,
    ) -> BirthResult:
        self.verify_gates()
        bundle = self.verify_founder_bundle()
        roadmap = self.verify_roadmap_sync(bundle)

        birth_context = build_birth_context(bundle["instance"], citizen_domain=citizen_domain)
        if not birth_context.get("founder_id"):
            raise BirthError("founder_id missing from birth context")

        template_dir = TEMPLATES_DIR / LINEAGE_TEMPLATE
        if not template_dir.is_dir():
            raise BirthError(f"lineage template missing: {template_dir}")

        base = output_dir or Path.cwd()
        citizen_dir = base / citizen_id
        if citizen_dir.exists():
            raise BirthError(f"citizen directory already exists: {citizen_dir}")

        shutil.copytree(template_dir, citizen_dir)
        manifest_path = citizen_dir / "manifest.json"
        manifest = _load_json(manifest_path)
        manifest["id"] = citizen_id
        manifest["name"] = f"{citizen_id.title()} Lineage Citizen"
        manifest["lineage"] = {
            "parent_citizen": "founderos",
            "reference_citizen": "harvey",
            "founder_id": birth_context["founder_id"],
            "citizen_domain": citizen_domain,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        birth_context_path = citizen_dir / "birth-context.json"
        birth_context_path.write_text(json.dumps(birth_context, indent=2) + "\n", encoding="utf-8")

        born_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        birth_manifest = {
            "schema": BIRTH_MANIFEST_SCHEMA,
            "citizen_id": citizen_id,
            "citizen_domain": citizen_domain,
            "born_at": born_at,
            "lineage": {
                "parent_citizen": "founderos",
                "reference_citizen": "harvey",
                "founder_id": birth_context["founder_id"],
            },
            "founder_context_ref": {
                "artifact_id": bundle["artifact_id"],
                "instance_id": bundle["instance"].get("instance_id"),
                "canonical_sha256": bundle["instance"].get("canonical_sha256"),
                "birth_context_fingerprint": birth_context["content_fingerprint"],
            },
            "roadmap_ref": {
                "schema": roadmap.get("schema"),
                "generated_at": roadmap.get("generated_at"),
                "founder_model_link": roadmap.get("founder_model_link"),
            },
            "gates_verified": {
                "VS-04": "PASS",
                "FO-00": "PASS",
                "FO-01": "PASS",
            },
        }
        birth_manifest_path = citizen_dir / "birth_manifest.json"
        birth_manifest_path.write_text(json.dumps(birth_manifest, indent=2) + "\n", encoding="utf-8")

        return BirthResult(
            citizen_id=citizen_id,
            citizen_dir=citizen_dir,
            birth_manifest_path=birth_manifest_path,
            birth_context_path=birth_context_path,
            founder_artifact_id=bundle["artifact_id"],
        )
