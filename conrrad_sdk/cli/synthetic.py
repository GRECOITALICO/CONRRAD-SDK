"""conrrad synthetic — Platform Validation via Synthetic Ecosystem"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    env = os.environ.get("CONRRAD_REPO_ROOT")
    if env:
        return Path(env)
    # conrrad-sdk/conrrad_sdk/cli/synthetic.py -> repo may be parent of sdk
    here = Path(__file__).resolve()
    for parent in [here.parents[3], here.parents[2], here.parents[4]]:
        if (parent / "scripts" / "synthetic_ecosystem" / "platform_validation.py").is_file():
            return parent
    return here.parents[3]


def main() -> int:
    if len(sys.argv) < 1 or sys.argv[0] in ("-h", "--help"):
        print("Usage: conrrad synthetic run [all] [--skip-topology]")
        return 0

    sub = sys.argv[0] if sys.argv[0] != "synthetic" else (sys.argv[1] if len(sys.argv) > 1 else "")
    if sub in ("-h", "--help", ""):
        print("Usage: conrrad synthetic run [all] [--skip-topology]")
        return 0
    if sub != "run":
        print(f"Unknown synthetic subcommand: {sub}", file=sys.stderr)
        return 1

    root = _repo_root()
    script = root / "scripts" / "synthetic_ecosystem" / "run_all.sh"
    if not script.is_file():
        print(f"missing {script}", file=sys.stderr)
        return 1

    args = ["bash", str(script)]
    if "--skip-topology" in sys.argv:
        args.append("--skip-topology")

    return subprocess.call(args, cwd=str(root))


if __name__ == "__main__":
    raise SystemExit(main())
