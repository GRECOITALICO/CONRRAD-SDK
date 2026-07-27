#!/usr/bin/env python3
"""CVS-001 vocabulary lint — forbidden legacy terms in public SDK paths."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_governance_lib import check_vocabulary, load_registry  # noqa: E402


def main() -> int:
    registry = load_registry()
    errors = check_vocabulary(registry)
    if errors:
        print("Vocabulary lint FAILED — forbidden legacy terms in public paths:")
        for err in errors:
            print(f"  {err}")
        return 1
    print("Vocabulary lint OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
