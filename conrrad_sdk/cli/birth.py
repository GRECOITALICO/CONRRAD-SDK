from __future__ import annotations

import argparse
import sys
from pathlib import Path

from conrrad_sdk.birth.engine import BirthEngine, BirthError


def _find_repo_root(start: Path) -> Path | None:
    current = start.resolve()
    for _ in range(8):
        if (current / ".conrrad-evidence" / "founder_model_v1.json").is_file():
            return current
        if current.parent == current:
            break
        current = current.parent
    return None


def _print_help() -> None:
    print("Usage: conrrad birth <citizen> [--domain <domain>] [--repo-root <path>] [--output <dir>]")
    print("")
    print("Bootstrap a lineage Citizen from a certified Founder Model bundle (VS-05).")
    print("Consume-only: does not mutate Founder Model, timeline, or roadmap persistence.")


def main() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] == "birth":
        argv = argv[1:]

    parser = argparse.ArgumentParser(prog="conrrad birth", add_help=False)
    parser.add_argument("citizen", nargs="?", help="Citizen id (e.g. scout)")
    parser.add_argument("--domain", default="platform", help="Citizen domain for birth-context subset")
    parser.add_argument("--repo-root", type=Path, help="CONRRAD repo root (auto-detected)")
    parser.add_argument("--output", type=Path, help="Output directory (default: cwd)")
    parser.add_argument("-h", "--help", action="store_true")
    args, _ = parser.parse_known_args(argv)

    if args.help or not args.citizen:
        _print_help()
        return 0

    repo_root = args.repo_root or _find_repo_root(Path.cwd())
    if repo_root is None:
        print("❌ Cannot locate CONRRAD repo root (.conrrad-evidence/founder_model_v1.json)")
        return 2

    try:
        engine = BirthEngine(repo_root)
        result = engine.bootstrap(
            args.citizen,
            citizen_domain=args.domain,
            output_dir=args.output,
        )
    except BirthError as exc:
        print(f"❌ Birth blocked: {exc}")
        return 1
    except Exception as exc:
        print(f"❌ Birth failed: {exc}")
        return 1

    print(f"✅ Citizen born: {result.citizen_dir}")
    print(f"   birth_manifest.json → {result.birth_manifest_path}")
    print(f"   birth-context.json  → {result.birth_context_path}")
    print(f"   founder artifact_id   → {result.founder_artifact_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
