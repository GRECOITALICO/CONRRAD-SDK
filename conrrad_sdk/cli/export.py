from __future__ import annotations

import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from conrrad_sdk.cli.run import _resolve_project_dir
from conrrad_sdk.export.package import verify_package, write_package


def _print_help() -> None:
    print("Usage: conrrad export <project> [--output <path>] [--verify]")
    print("Creates deterministic Production Package: <project>.export.tar.gz")


def _sdk_version() -> str:
    try:
        return version("conrrad")
    except PackageNotFoundError:
        return "dev"


def main() -> int:
    argv = sys.argv[2:] if len(sys.argv) >= 2 and sys.argv[1] == "export" else sys.argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        _print_help()
        return 0

    project_name = argv[0]
    output_path: Path | None = None
    do_verify = False
    i = 1
    while i < len(argv):
        if argv[i] == "--output" and i + 1 < len(argv):
            output_path = Path(argv[i + 1])
            i += 2
            continue
        if argv[i] == "--verify":
            do_verify = True
            i += 1
            continue
        print(f"Unknown argument: {argv[i]}")
        return 2

    try:
        project_dir = _resolve_project_dir(project_name)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 2

    out = output_path or (Path.cwd() / f"{project_dir.name}.export.tar.gz")
    manifest = write_package(project_dir, out, sdk_version=_sdk_version())

    if do_verify:
        try:
            verify_package(out)
        except ValueError as exc:
            print(f"❌ Package verification failed: {exc}")
            return 1

    print(f"✅ Production Package: {out}")
    print(f"   project_id: {manifest.get('project_id')}")
    print(f"   files: {len(manifest.get('files', []))}")
    print(f"   package_sha256: {manifest.get('package_sha256')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
