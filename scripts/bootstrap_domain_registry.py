#!/usr/bin/env python3
"""Bootstrap domain registry entries and MANIFEST.yaml from conrrad_sdk tree."""
from __future__ import annotations

import pathlib
import textwrap

DOMAINS = [
    "adapters", "benchmarks", "billing", "birth", "citizen", "cli", "cluster",
    "cognitive", "compliance", "core", "crypto", "delegation", "devlayer",
    "escrow", "events", "export", "governance", "harvey", "internal", "learning",
    "llm", "marketplace", "network", "observability", "pay", "quickstart",
    "reputation", "router", "runtime", "security", "shadow", "sully", "swarm",
    "telemetry", "templates", "testnet", "tools", "web_dashboard", "worker",
]

DOMAIN_META = {
    "runtime": ("Runtime", "Executive Core", "Persistent cognitive execution layer.", "ADR-001"),
    "escrow": ("Escrow", "Executive Architecture", "Canonical escrow runtime.", "ADR-003"),
    "governance": ("Governance", "Executive Core", "Policy and authority enforcement.", "ADR-004"),
    "memory": ("Memory", "Runtime Layer", "Persistent state and recall.", "ADR-002"),
    "security": ("Security", "SEAL Layer", "Execution security and sandbox boundaries.", "ADR-005"),
    "core": ("Core", "Executive Core", "Foundation primitives shared across domains.", "ADR-001"),
}

DEFAULT_STEWARD = "Executive Architecture"


def domain_record(name: str) -> str:
    title, steward, desc, adr = DOMAIN_META.get(
        name,
        (name.replace("_", " ").title(), DEFAULT_STEWARD, f"{name} domain.", "ADR-TBD"),
    )
    asset_id = f"SDK.{name.upper().replace('/', '.')}.DOMAIN"
    return textwrap.dedent(
        f"""\
        asset_id: {asset_id}
        name: {title}
        type: Domain
        domain: {name}
        path: conrrad_sdk/{name}/

        owner:
          domain: {title}
          steward: {steward}

        purpose:
          canonical: {desc}

        governed_by:
          - HARLEMM
          - {steward}

        consumed_by:
          - OMEGA
          - Executive Core

        replacement:
          status: none
          successor: null

        lifecycle:
          introduced: "1.0.0"
          status: ACTIVE

        adr:
          - {adr}

        exports:
          public: true

        dependencies: []

        contains_glob:
          - "**/*"
        """
    )


def domain_manifest(name: str) -> str:
    title, steward, desc, _ = DOMAIN_META.get(
        name,
        (name.replace("_", " ").title(), DEFAULT_STEWARD, f"{name} domain.", "ADR-TBD"),
    )
    return textwrap.dedent(
        f"""\
        name: {title}
        owner: {steward}
        domain: {name}
        description: |
          {desc}
        contains_glob:
          - "**/*"
        public_api: []
        forbidden:
          - UI
          - ad-hoc scripts
        """
    )


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    sdk = root / "conrrad_sdk"
    reg = root / "assets" / "registry" / "domains"
    reg.mkdir(parents=True, exist_ok=True)

    active = []
    for name in sorted(DOMAINS):
        if not (sdk / name).is_dir():
            continue
        (reg / f"{name}.yaml").write_text(domain_record(name))
        manifest = sdk / name / "MANIFEST.yaml"
        if not manifest.exists():
            manifest.write_text(domain_manifest(name))
        active.append(name)

    root_modules = sorted(
        p.name
        for p in sdk.iterdir()
        if p.is_file() and p.suffix == ".py" and not p.name.startswith("__")
    )

    index = {
        "registry_version": "1.0",
        "repository": "conrrad-sdk",
        "package": "conrrad_sdk",
        "domains": [
            {
                "name": n,
                "asset_id": f"SDK.{n.upper()}.DOMAIN",
                "registry": f"assets/registry/domains/{n}.yaml",
                "manifest": f"conrrad_sdk/{n}/MANIFEST.yaml",
                "lifecycle": "ACTIVE",
            }
            for n in active
        ],
        "root_modules": root_modules,
    }

    import yaml

    idx_path = root / "assets" / "registry" / "index.yaml"
    idx_path.write_text(yaml.dump(index, sort_keys=False, allow_unicode=True))
    print(f"[OK] Registered {len(active)} domains → {idx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
