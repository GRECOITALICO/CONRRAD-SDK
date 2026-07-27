"""Entry point for supervised runtime server subprocess."""
from __future__ import annotations

import argparse
from pathlib import Path

from conrrad_sdk.runtime.server import serve


def main() -> int:
    parser = argparse.ArgumentParser(description="CONRRAD Platform Runtime server")
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--citizen", required=True)
    parser.add_argument("--citizen-dir", type=Path, default=None)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8530)
    args = parser.parse_args()

    serve(
        args.repo_root,
        args.citizen,
        args.citizen_dir,
        args.runtime_dir,
        args.host,
        args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
