"""Tests for CVS-001 canonical governance linters."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts.canonical_governance_lib import (
    check_ontology,
    check_registry_compat,
    check_registry_consistency,
    check_vocabulary,
    load_registry,
)

ROOT = Path(__file__).resolve().parents[1]


class CanonicalGovernanceTests(unittest.TestCase):
    def test_registry_loads(self) -> None:
        registry = load_registry()
        self.assertEqual(registry["registry_version"], 1)
        self.assertEqual(registry["ontology_version"], 1)
        self.assertEqual(registry["sdk_min_version"], "2.0.0")
        self.assertIn("Agent", registry["symbols"])
        self.assertEqual(registry["symbols"]["Agent"]["canonical_id"], "EXEC.AGENT")

    def test_registry_consistency_passes(self) -> None:
        errors = check_registry_consistency(load_registry())
        self.assertEqual(errors, [])

    def test_registry_catches_duplicate_official_name(self) -> None:
        registry = json.loads(json.dumps(load_registry()))
        registry["canonical_ids"]["EXEC.RUNTIME"]["official_name"] = "Run"
        errors = check_registry_consistency(registry)
        self.assertTrue(any("duplicate official_name" in err for err in errors))

    def test_registry_catches_symbol_owner_mismatch(self) -> None:
        registry = json.loads(json.dumps(load_registry()))
        registry["symbols"]["Run"]["owner"] = "Observatory"
        errors = check_registry_consistency(registry)
        self.assertTrue(any("owner" in err and "Run" in err for err in errors))

    def test_registry_catches_undefined_canonical_id(self) -> None:
        registry = json.loads(json.dumps(load_registry()))
        registry["symbols"]["Run"]["canonical_id"] = "EXEC.MISSING"
        errors = check_registry_consistency(registry)
        self.assertTrue(any("undefined canonical_id" in err for err in errors))

    def test_registry_compat_requires_version_bump_on_owner_change(self) -> None:
        base = load_registry()
        head = json.loads(json.dumps(base))
        head["symbols"]["Run"]["owner"] = "Observatory"
        head["canonical_ids"]["EXEC.RUN"]["owner"] = "Observatory"
        errors = check_registry_compat(base, head)
        self.assertTrue(any("BREAKING ONTOLOGY CHANGE" in err for err in errors))

    def test_registry_compat_passes_with_version_bump(self) -> None:
        base = load_registry()
        head = json.loads(json.dumps(base))
        head["ontology_version"] = int(base["ontology_version"]) + 1
        head["symbols"]["Run"]["owner"] = "Observatory"
        head["canonical_ids"]["EXEC.RUN"]["owner"] = "Observatory"
        errors = check_registry_compat(base, head)
        self.assertEqual(errors, [])

    def test_registry_compat_passes_when_unchanged(self) -> None:
        reg = load_registry()
        self.assertEqual(check_registry_compat(reg, reg), [])
        errors = check_vocabulary(load_registry(), root=ROOT)
        self.assertEqual(errors, [])

    def test_ontology_passes_on_current_public_api(self) -> None:
        errors = check_ontology(load_registry(), root=ROOT)
        self.assertEqual(errors, [])

    def test_vocabulary_catches_kern(self) -> None:
        registry = load_registry()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry["lint_paths"] = ["sample.md"]
            (root / "sample.md").write_text("balance in KERN units\n", encoding="utf-8")
            errors = check_vocabulary(registry, root=root)
            self.assertTrue(any("KERN" in err for err in errors))

    def test_ontology_catches_unregistered_export(self) -> None:
        registry = json.loads(json.dumps(load_registry()))
        registry["ontology"]["api_export_modules"] = ["conrrad/__init__.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pkg = root / "conrrad"
            pkg.mkdir()
            (pkg / "__init__.py").write_text(
                textwrap.dedent(
                    """
                    from demo import SmartBudget
                    __all__ = ["SmartBudget"]
                    """
                ),
                encoding="utf-8",
            )
            errors = check_ontology(registry, root=root)
            self.assertTrue(any("SmartBudget" in err for err in errors))

    def test_governance_scripts_exit_zero(self) -> None:
        for name in (
            "check_registry_consistency.py",
            "check_public_vocabulary.py",
            "check_public_ontology.py",
        ):
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / name)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode,
                0,
                msg=result.stdout + result.stderr,
            )


if __name__ == "__main__":
    unittest.main()
