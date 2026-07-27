from __future__ import annotations

import json
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

CONFIG_DIR = Path.home() / ".conrrad"


def _pkg_version(name: str, fallback: str = "dev") -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return fallback


def main() -> int:
    payload = {
        "status": "ok",
        "config_dir": str(CONFIG_DIR),
        "config_exists": CONFIG_DIR.is_dir(),
        "sdk_version": _pkg_version("conrrad", _pkg_version("kap-escrow")),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
