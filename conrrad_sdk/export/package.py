from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
import tempfile
from pathlib import Path
from typing import Iterable

MANIFEST_SCHEMA = "conrrad-export-manifest/v1"
EPHEMERAL_NAMES = {".runtime.pid", "runtime.log"}
DETERMINISTIC_EXPORTED_AT = "1970-01-01T00:00:00Z"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _sdk_harvey_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "harvey"


def collect_export_files(project_dir: Path) -> list[Path]:
    """Collect project files for Production Package (exclude ephemeral runtime)."""
    files: list[Path] = []
    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(project_dir)
        if rel.parts and rel.parts[0] == "workspace":
            if path.name in EPHEMERAL_NAMES:
                continue
        files.append(path)
    for name in ("conrrad.yaml", "manifest.json"):
        p = project_dir / name
        if p.is_file() and p not in files:
            files.append(p)
    return sorted(set(files), key=lambda p: str(p.relative_to(project_dir)))


def collect_pipeline_files() -> list[tuple[str, bytes]]:
    """Bundle SDK Harvey pipeline as harvey/ for portable Production Package."""
    harvey_dir = _sdk_harvey_dir()
    if not harvey_dir.is_dir():
        return []
    bundled: list[tuple[str, bytes]] = []
    for path in sorted(harvey_dir.rglob("*.py")):
        rel = f"harvey/{path.relative_to(harvey_dir).as_posix()}"
        bundled.append((rel, path.read_bytes()))
    return bundled


def build_manifest(
    project_dir: Path,
    project_entries: list[dict],
    pipeline_entries: list[dict],
    sdk_version: str,
) -> dict:
    project_id = project_dir.name
    manifest_path = project_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            project_id = json.loads(manifest_path.read_text(encoding="utf-8")).get("id", project_id)
        except json.JSONDecodeError:
            pass

    files = sorted(project_entries + pipeline_entries, key=lambda e: e["path"])
    content_fingerprint = _sha256_bytes(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )

    return {
        "schemaVersion": MANIFEST_SCHEMA,
        "project_id": project_id,
        "exported_at": DETERMINISTIC_EXPORTED_AT,
        "content_fingerprint": content_fingerprint,
        "sdk_version": sdk_version,
        "files": files,
    }


def _add_tar_entry(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mtime = 0
    tar.addfile(info, fileobj=io.BytesIO(data))


def write_package(project_dir: Path, output_path: Path, sdk_version: str = "unknown") -> dict:
    """Build deterministic tar.gz Production Package. Returns manifest with package_sha256."""
    project_files = collect_export_files(project_dir)
    project_entries = [
        {
            "path": str(p.relative_to(project_dir)).replace("\\", "/"),
            "sha256": _sha256_file(p),
        }
        for p in project_files
    ]
    pipeline_blobs = collect_pipeline_files()
    pipeline_entries = [{"path": rel, "sha256": _sha256_bytes(data)} for rel, data in pipeline_blobs]

    manifest = build_manifest(project_dir, project_entries, pipeline_entries, sdk_version)
    manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n"

    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.GNU_FORMAT) as tar:
        _add_tar_entry(tar, "export-manifest.json", manifest_bytes)
        for path in project_files:
            rel = str(path.relative_to(project_dir)).replace("\\", "/")
            _add_tar_entry(tar, rel, path.read_bytes())
        for rel, data in pipeline_blobs:
            _add_tar_entry(tar, rel, data)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(gzip.compress(tar_buffer.getvalue(), compresslevel=9, mtime=0))

    manifest["package_sha256"] = _sha256_file(output_path)
    manifest["package_name"] = output_path.name
    return manifest


def verify_package(package_path: Path, extract_dir: Path | None = None) -> dict:
    """C08: open package, validate manifest and file checksums (no Citizen execution)."""
    work = extract_dir
    cleanup = False
    if work is None:
        work = Path(tempfile.mkdtemp(prefix="conrrad-export-verify-"))
        cleanup = True

    try:
        with tarfile.open(package_path, "r:gz") as tar:
            tar.extractall(work, filter="data")

        manifest_path = work / "export-manifest.json"
        if not manifest_path.is_file():
            raise ValueError("missing export-manifest.json")

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("schemaVersion") != MANIFEST_SCHEMA:
            raise ValueError(f"invalid schemaVersion: {manifest.get('schemaVersion')}")

        for entry in manifest.get("files", []):
            rel = entry["path"]
            expected = entry["sha256"]
            fp = work / rel
            if not fp.is_file():
                raise ValueError(f"missing file in package: {rel}")
            if _sha256_file(fp) != expected:
                raise ValueError(f"checksum mismatch: {rel}")

        return manifest
    finally:
        if cleanup:
            import shutil

            shutil.rmtree(work, ignore_errors=True)
