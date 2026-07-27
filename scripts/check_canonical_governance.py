#!/usr/bin/env python3
"""Run CVS-001 vocabulary + ontology linters (canonical governance)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    scripts = [
        ROOT / "check_registry_consistency.py",
        ROOT / "check_public_vocabulary.py",
        ROOT / "check_public_ontology.py",
    ]
    failed = False
    for script in scripts:
        result = subprocess.run([sys.executable, str(script)], check=False)
        if result.returncode != 0:
            failed = True
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
