from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

CONFIG_DIR = Path.home() / ".conrrad"
TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
PROJECT_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")


def _print_help() -> None:
    print("Usage: conrrad new <project>")
    print("Templates:")
    print("  hello   — Quick Start (local, no Docker)")
    print("  harvey  — Reference Application (full runtime)")
    print("")
    print("Example: conrrad new hello && cd hello && conrrad run")


def _register_project(name: str, project_dir: Path, template_id: str | None = None) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    registry_path = CONFIG_DIR / "projects.json"
    registry: dict = {}
    if registry_path.is_file():
        try:
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            registry = {}
    projects = registry.setdefault("projects", [])
    projects = [p for p in projects if p.get("name") != name]
    projects.append(
        {
            "name": name,
            "path": str(project_dir.resolve()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "template": template_id or name,
        }
    )
    registry["projects"] = projects
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def create_project(name: str, cwd: Path | None = None) -> Path:
    if not PROJECT_NAME_RE.match(name):
        raise ValueError(f"Invalid project name: {name!r}")

    template_dir = TEMPLATES_DIR / name
    if not template_dir.is_dir():
        raise FileNotFoundError(f"Unknown project template: {name}")

    base = cwd or Path.cwd()
    project_dir = base / name
    if project_dir.exists():
        raise FileExistsError(f"Project directory already exists: {project_dir}")

    shutil.copytree(template_dir, project_dir)

    template_id = name
    manifest_path = project_dir / "manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            template_id = manifest.get("template", name)
        except json.JSONDecodeError:
            pass

    if template_id != "hello":
        (project_dir / "workspace").mkdir(exist_ok=True)

    _register_project(name, project_dir, template_id=template_id)
    return project_dir


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "new":
        argv = argv[1:]

    if not argv or argv[0] in ("-h", "--help"):
        _print_help()
        return 0

    name = argv[0]
    try:
        project_dir = create_project(name)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 2
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        return 2
    except FileExistsError as exc:
        print(f"❌ {exc}")
        return 1

    print(f"✅ Project created: {project_dir}")
    print(f"   conrrad.yaml  → {project_dir / 'conrrad.yaml'}")
    print(f"   manifest.json → {project_dir / 'manifest.json'}")
    if name == "hello":
        print("👉 Next: cd hello && conrrad run")
    else:
        print(f"👉 Next: cd {name} && conrrad run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
