"""Shared helpers for CVS-001 canonical governance linters."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs" / "canonical_registry.json"

REQUIRED_VERSION_FIELDS = ("registry_version", "ontology_version", "sdk_min_version")
OPTIONAL_ID_METADATA = ("public", "since", "deprecated")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def load_registry(path: Path | None = None) -> dict:
    registry_path = path or DEFAULT_REGISTRY
    with registry_path.open(encoding="utf-8") as handle:
        registry = json.load(handle)
    missing = [field for field in REQUIRED_VERSION_FIELDS if field not in registry]
    if missing:
        raise ValueError(f"registry missing version fields: {', '.join(missing)}")
    return registry


def iter_lint_files(registry: dict, root: Path | None = None) -> Iterator[Path]:
    base = root or ROOT
    extensions = set(registry.get("text_extensions", [".py", ".md", ".json"]))
    for rel in registry.get("lint_paths", []):
        target = base / rel
        if target.is_file():
            if target.suffix in extensions or not target.suffix:
                yield target
            continue
        if not target.is_dir():
            continue
        for path in target.rglob("*"):
            if path.is_file() and path.suffix in extensions:
                yield path


def compile_forbidden_patterns(registry: dict) -> list[tuple[str, re.Pattern[str]]]:
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for entry in registry.get("forbidden_terms", []):
        pattern = entry["pattern"]
        if entry.get("word_boundary"):
            compiled.append((pattern, re.compile(rf"\b{re.escape(pattern)}\b")))
        else:
            compiled.append((pattern, re.compile(re.escape(pattern))))
    return compiled


def check_vocabulary(registry: dict, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    patterns = compile_forbidden_patterns(registry)
    for path in iter_lint_files(registry, root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root or ROOT)
        for label, regex in patterns:
            for match in regex.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{rel}:{line}: forbidden legacy term {label!r}")
    return errors


def _parse_all_exports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        names: list[str] = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                names.append(elt.value)
                        return names
    return []


def _public_classes_in_dir(directory: Path) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for path in sorted(directory.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                found.append((node.name, str(path.relative_to(ROOT))))
    return found


def check_registry_consistency(registry: dict) -> list[str]:
    """Validate internal consistency of canonical_registry.json (executable SSOT)."""
    errors: list[str] = []
    symbols: dict = registry.get("symbols", {})
    canonical_ids: dict = registry.get("canonical_ids", {})
    valid_owners = set(registry.get("valid_owners", []))

    if not symbols:
        errors.append("registry symbols map is empty")
    if not canonical_ids:
        errors.append("registry canonical_ids map is empty")

    # --- canonical_id definitions ---
    seen_ids: dict[str, int] = {}
    official_name_to_ids: dict[str, list[str]] = {}
    for cid, meta in canonical_ids.items():
        seen_ids[cid] = seen_ids.get(cid, 0) + 1
        if not isinstance(meta, dict):
            errors.append(f"canonical_id {cid!r} must be an object")
            continue
        owner = meta.get("owner")
        official_name = meta.get("official_name")
        if not owner:
            errors.append(f"canonical_id {cid!r} missing owner")
        elif valid_owners and owner not in valid_owners:
            errors.append(f"canonical_id {cid!r} has unknown owner {owner!r}")
        if not official_name:
            errors.append(f"canonical_id {cid!r} missing official_name")
        else:
            official_name_to_ids.setdefault(official_name, []).append(cid)
        errors.extend(_validate_optional_metadata(cid, meta, label="canonical_id"))

    for symbol, meta in symbols.items():
        if isinstance(meta, dict):
            errors.extend(_validate_optional_metadata(symbol, meta, label="symbol"))

    for official_name, ids in official_name_to_ids.items():
        if len(ids) > 1:
            errors.append(
                f"duplicate official_name {official_name!r} on canonical_ids: {', '.join(ids)}"
            )

    # --- public symbols: exactly one canonical_id each; owner must align ---
    symbol_to_cid: dict[str, str] = {}
    cid_owner_from_symbols: dict[str, set[str]] = {}
    for symbol, meta in symbols.items():
        if not isinstance(meta, dict):
            errors.append(f"symbol {symbol!r} must be an object")
            continue
        cid = meta.get("canonical_id")
        owner = meta.get("owner")
        if not cid:
            errors.append(f"symbol {symbol!r} missing canonical_id")
            continue
        if cid not in canonical_ids:
            errors.append(f"symbol {symbol!r} references undefined canonical_id {cid!r}")
            continue
        if symbol in symbol_to_cid and symbol_to_cid[symbol] != cid:
            errors.append(
                f"symbol {symbol!r} maps to multiple canonical_ids: "
                f"{symbol_to_cid[symbol]!r} and {cid!r}"
            )
        symbol_to_cid[symbol] = cid
        if not owner:
            errors.append(f"symbol {symbol!r} missing owner")
        elif valid_owners and owner not in valid_owners:
            errors.append(f"symbol {symbol!r} has unknown owner {owner!r}")
        else:
            cid_owner_from_symbols.setdefault(cid, set()).add(owner)
        id_owner = canonical_ids[cid].get("owner")
        if owner and id_owner and owner != id_owner:
            errors.append(
                f"symbol {symbol!r} owner {owner!r} != canonical_id {cid!r} owner {id_owner!r}"
            )

    for cid, owners in cid_owner_from_symbols.items():
        if len(owners) > 1:
            errors.append(
                f"canonical_id {cid!r} reached by symbols with conflicting owners: "
                f"{', '.join(sorted(owners))}"
            )

    return errors


def _validate_optional_metadata(key: str, meta: dict, *, label: str) -> list[str]:
    """Validate optional release metadata when present (public, since, deprecated)."""
    errors: list[str] = []
    if "public" in meta and not isinstance(meta["public"], bool):
        errors.append(f"{label} {key!r}: public must be boolean")
    for field in ("since", "deprecated"):
        if field not in meta:
            continue
        value = meta[field]
        if value is None:
            continue
        if not isinstance(value, str) or not SEMVER_RE.match(value):
            errors.append(f"{label} {key!r}: {field} must be semver string or null")
    if meta.get("deprecated") and not meta.get("since"):
        errors.append(f"{label} {key!r}: deprecated set but since is missing")
    return errors


def find_registry_breaking_changes(base: dict, head: dict) -> list[str]:
    """Return human-readable breaking ontology deltas (base → head)."""
    changes: list[str] = []
    base_ids = base.get("canonical_ids", {})
    head_ids = head.get("canonical_ids", {})
    base_symbols = base.get("symbols", {})
    head_symbols = head.get("symbols", {})

    for cid in sorted(set(base_ids) - set(head_ids)):
        changes.append(f"canonical_id removed: {cid}")

    for cid in sorted(set(base_ids) & set(head_ids)):
        b_meta = base_ids[cid]
        h_meta = head_ids[cid]
        if b_meta.get("owner") != h_meta.get("owner"):
            changes.append(
                f"canonical_id {cid} owner changed: "
                f"{b_meta.get('owner')!r} -> {h_meta.get('owner')!r}"
            )
        if b_meta.get("official_name") != h_meta.get("official_name"):
            changes.append(
                f"canonical_id {cid} official_name changed: "
                f"{b_meta.get('official_name')!r} -> {h_meta.get('official_name')!r}"
            )

    # Renames appear as remove + add with same official_name
    removed = set(base_ids) - set(head_ids)
    added = set(head_ids) - set(base_ids)
    if removed and added:
        for old_cid in removed:
            old_name = base_ids[old_cid].get("official_name")
            for new_cid in added:
                if head_ids[new_cid].get("official_name") == old_name:
                    changes.append(f"canonical_id renamed: {old_cid} -> {new_cid}")

    for symbol in sorted(set(base_symbols) - set(head_symbols)):
        changes.append(f"symbol removed: {symbol!r}")

    for symbol in sorted(set(base_symbols) & set(head_symbols)):
        b_cid = base_symbols[symbol].get("canonical_id")
        h_cid = head_symbols[symbol].get("canonical_id")
        if b_cid != h_cid:
            changes.append(
                f"symbol {symbol!r} canonical_id changed: {b_cid!r} -> {h_cid!r}"
            )
        b_owner = base_symbols[symbol].get("owner")
        h_owner = head_symbols[symbol].get("owner")
        if b_owner != h_owner:
            changes.append(
                f"symbol {symbol!r} owner changed: {b_owner!r} -> {h_owner!r}"
            )

    return changes


def check_registry_compat(base: dict, head: dict) -> list[str]:
    """Fail if breaking ontology changes lack an ontology_version bump."""
    breaking = find_registry_breaking_changes(base, head)
    if not breaking:
        return []
    base_version = int(base.get("ontology_version", 0))
    head_version = int(head.get("ontology_version", 0))
    if head_version > base_version:
        return []
    lines = ["BREAKING ONTOLOGY CHANGE — requires ontology_version bump:"]
    lines.extend(f"  - {item}" for item in breaking)
    lines.append(f"Requires: ontology_version > {base_version} (head has {head_version})")
    return lines


def load_registry_from_git(ref: str, root: Path | None = None) -> dict | None:
    """Load canonical_registry.json from a git ref, or None if unavailable."""
    import subprocess

    base = root or ROOT
    rel = DEFAULT_REGISTRY.relative_to(base)
    try:
        raw = subprocess.check_output(
            ["git", "show", f"{ref}:{rel.as_posix()}"],
            cwd=base,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    registry = json.loads(raw)
    missing = [field for field in REQUIRED_VERSION_FIELDS if field not in registry]
    if missing:
        raise ValueError(f"registry at {ref} missing version fields: {', '.join(missing)}")
    return registry


def _validate_registry_integrity(registry: dict) -> list[str]:
    return check_registry_consistency(registry)


def check_ontology(registry: dict, root: Path | None = None) -> list[str]:
    errors = _validate_registry_integrity(registry)
    base = root or ROOT
    symbols = registry.get("symbols", {})
    ontology = registry.get("ontology", {})
    ignore_classes = set(ontology.get("ignore_class_names", []))
    ignore_prefixes = tuple(ontology.get("ignore_identifier_prefixes", ["_"]))

    for rel in ontology.get("api_export_modules", []):
        path = base / rel
        if not path.is_file():
            errors.append(f"missing api export module: {rel}")
            continue
        for name in _parse_all_exports(path):
            if name.startswith(ignore_prefixes):
                continue
            if name not in symbols:
                errors.append(
                    f"{rel}: exported symbol {name!r} not in canonical_registry.json "
                    f"(no architectural owner)"
                )

    for rel in ontology.get("public_class_dirs", []):
        directory = base / rel
        if not directory.is_dir():
            errors.append(f"missing public class dir: {rel}")
            continue
        for class_name, file_rel in _public_classes_in_dir(directory):
            if class_name in ignore_classes or class_name.startswith(ignore_prefixes):
                continue
            if class_name not in symbols:
                errors.append(
                    f"{file_rel}: public class {class_name!r} not in canonical_registry.json "
                    f"(e.g. orphan concept like SmartBudget)"
                )

    return errors
