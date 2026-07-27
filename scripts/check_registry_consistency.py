#!/usr/bin/env python3
"""CVS-001 registry consistency — validate canonical_registry.json internal SSOT."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_governance_lib import check_registry_consistency, load_registry  # noqa: E402


def main() -> int:
    registry = load_registry()
    errors = check_registry_consistency(registry)
    if errors:
        print("Registry consistency FAILED:")
        for err in errors:
            print(f"  {err}")
        return 1
    print(
        "Registry consistency OK "
        f"(registry_version={registry['registry_version']}, "
        f"ontology_version={registry['ontology_version']}, "
        f"sdk_min_version={registry['sdk_min_version']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
