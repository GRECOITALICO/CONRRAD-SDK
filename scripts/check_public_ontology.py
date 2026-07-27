#!/usr/bin/env python3
"""CVS-001 ontology lint — public symbols must map to canonical IDs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_governance_lib import check_ontology, load_registry  # noqa: E402


def main() -> int:
    registry = load_registry()
    errors = check_ontology(registry)
    if errors:
        print("Ontology lint FAILED — unregistered or invalid public symbols:")
        for err in errors:
            print(f"  {err}")
        return 1
    print("Ontology lint OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
