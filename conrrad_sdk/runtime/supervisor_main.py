"""Supervisor CLI entry for subprocess invocation."""
from __future__ import annotations

import argparse
from pathlib import Path

from conrrad_sdk.runtime.supervisor import supervise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--citizen", required=True)
    parser.add_argument("--citizen-dir", type=Path, default=None)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8530)
    args = parser.parse_args()
    return supervise(
        args.repo_root,
        args.citizen,
        args.citizen_dir,
        args.runtime_dir,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    raise SystemExit(main())
