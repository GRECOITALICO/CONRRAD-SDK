#!/usr/bin/env python3
"""CVS-001 registry compat — breaking ontology changes require ontology_version bump."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from canonical_governance_lib import (  # noqa: E402
    check_registry_compat,
    load_registry,
    load_registry_from_git,
)


def main() -> int:
    head = load_registry()
    base_ref = os.environ.get("ONTOLOGY_BASE_REF", "origin/main")
    base = load_registry_from_git(base_ref)
    if base is None:
        print(f"Registry compat skipped (no base registry at {base_ref})")
        return 0

    errors = check_registry_compat(base, head)
    if errors:
        print("Registry compat FAILED:")
        for err in errors:
            print(err if err.startswith("  ") or err.startswith("Requires") else f"  {err}")
        return 1

    head_version = head.get("ontology_version")
    base_version = base.get("ontology_version")
    if head_version != base_version:
        print(f"Registry compat OK (ontology_version {base_version} -> {head_version})")
    else:
        print("Registry compat OK (no breaking ontology changes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
