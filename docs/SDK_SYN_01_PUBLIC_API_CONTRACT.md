# SDK-SYN-01 — Public API Contract

| Field | Value |
|-------|--------|
| **Contract ID** | `SDK_SYN_01_PUBLIC_API_CONTRACT` |
| **Version** | `1.0.1` |
| **Status** | **ACTIVE (PASS)** — gates live; failures → SDK-SYN-00X |
| **Policy** | [CONRRAD Progressive Validation Policy](../../../docs/PROGRESSIVE_VALIDATION_POLICY.md) — L1 Synthetic |
| **Migration program** | [KERNELL_TO_CONRRAD_MIGRATION.md](./KERNELL_TO_CONRRAD_MIGRATION.md) |
| **Oracle** | `scripts/sdk_syn_oracle.py` (Deliverable 2) |
| **Failure series** | `SDK-SYN-001` (synthetic oracle breach) |
| **Certification context** | Lessons from VS-07B F008–F010 (API drift, shim loading, legacy namespace leakage) |

This document is the **single source of truth** for what external consumers and synthetic oracles may rely on. All SDK-SYN tests, CI gates, and future vertical integrations **must** trace to a clause here. Anything not listed under §2 is **not** public.

---

## 0. Contract principle

**Implementation details are never part of the public contract.**

Public contracts describe **observable behavior** — imports, symbols, CLI entry points, HTTP shapes, exit codes, and version strings. They do **not** describe repository structure, module layout, bootstrap mechanisms, loaders, shims, or internal dependencies.

---

## 1. Purpose

Guarantee that any change to the SDK breaks the synthetic pipeline **before** it reaches a consumer.

Sprint 1 protects the **integration contract** that platform validation exercises: package install, canonical imports, Pay gateway client, citizen registration, CLI install entry, and version surface. Broader agent-framework APIs (`Agent`, `Memory`, escrow engine, etc.) remain documented in `conrrad_sdk.__all__` but are **out of SDK-SYN-01 oracle scope** until a later sprint extends this contract.

---

## 2. Public API (protected)

### 2.1 Package identity

| Requirement | Contract |
|-------------|----------|
| Canonical import root | `conrrad_sdk` |
| Distribution name (PyPI target) | `conrrad-sdk` |
| Python | `>=3.9` |
| Version string | `conrrad_sdk.__version__` — semver-like string, present after import |

**Sprint 1 oracle scope (F008–F010 lineage):** Pay integration is the protected path. The symbols in §2.3–§2.4 **must** work after install. Full eager loading of every symbol in `conrrad_sdk.__all__` is **declared public** but **outside Sprint 1 oracle scope** until a later contract revision.

**Consumer rule:** Applications and validation scripts import **`conrrad_sdk`** and subpackages listed below. They do **not** depend on repository layout or monorepo paths.

### 2.2 Install surface

| Requirement | Contract |
|-------------|----------|
| Editable install | From `conrrad-sdk` repository root: `pip install -e .` |
| Post-install | `import conrrad_sdk` and `import conrrad_sdk.pay` succeed **without** manual `sys.path` manipulation |
| Dependencies | Declared in project metadata; minimum for Pay path per install metadata |

**Consumer rule:** A clean virtualenv plus `pip install -e .` is the only supported bootstrap for synthetic validation. Monorepo `PYTHONPATH` injection is a **developer convenience**, not part of the public contract.

### 2.3 Submodule `conrrad_sdk.pay`

| Symbol | Type | Notes |
|--------|------|-------|
| `conrrad_sdk.pay` | package | Importable as `import conrrad_sdk.pay` |
| `ConrradPayGateway` | class | HTTP client for gateway / Observatory |
| `ExecutionEnvelope` | class | Pay execution envelope type |

**Import examples (required to work):**

```python
import conrrad_sdk
import conrrad_sdk.pay
from conrrad_sdk.pay import ConrradPayGateway
from conrrad_sdk.pay.gateway_client import ConrradPayGateway  # same class
```

### 2.4 `ConrradPayGateway` — citizen registration

**Constructor**

```python
ConrradPayGateway(base_url: str | None = None, timeout: float = 15.0)
```

- Default base URL resolution order: `CONRRAD_GATEWAY_URL` → `CONRRAD_PAY_GATEWAY_URL` → `http://127.0.0.1:23817`

**Method (public, stable name)**

```python
def register_citizen(
    self,
    *,
    developer_id: str,
    install_fingerprint: str,
    wallet_pubkey: str | None = None,
    sdk_version: str | None = None,
    hostname: str | None = None,
    capabilities: list | None = None,
) -> dict[str, Any]:
```

| Rule | Contract |
|------|----------|
| HTTP | `POST /api/pay/citizen/register` |
| Keyword-only args | `developer_id` and `install_fingerprint` are **required** |
| Removed API | `ensure_citizen()` — **not** public; must not reappear under any alias |

**Success response (minimum keys oracle validates)**

| Key | Type | Required |
|-----|------|----------|
| `citizenId` | string | yes |
| `installToken` | string | yes (new registration) |
| `walletId` | string | optional |
| `registeredAt` | string | optional |
| `reRegistered` | bool | optional |

Synthetic oracle may use a **mock HTTP gateway**; the contract is the **client call shape and response parsing**, not live infrastructure availability.

### 2.5 CLI — `install`

| Requirement | Contract |
|-------------|----------|
| Entry | `python -m conrrad_sdk.cli install` |
| Behavior | Calls `ConrradPayGateway.register_citizen()` with `developer_id`, `install_fingerprint`, `sdk_version`, `hostname` |
| Fingerprint | `INSTALL_FINGERPRINT` env overrides; else SHA-256 of `node:machine:sdk_version` |
| Credentials file | `~/.conrrad/citizen.json` (override: `CONRRAD_CITIZEN_CREDS`) on success |
| Exit code | `0` on success; non-zero on registration failure |

Other CLI subcommands (`init`, `doctor`, `synthetic`, …) exist but are **outside SDK-SYN-01 Sprint 1** unless added in a contract revision.

### 2.6 Packaging metadata

| Requirement | Contract |
|-------------|----------|
| Importable packages after install | `conrrad_sdk`, `conrrad_sdk.pay`, and packages required for those imports |
| Consumer-facing distribution name | `conrrad-sdk` (target) |
| Public entry | `conrrad_sdk` only — see §3 |

---

## 3. Non-public (explicitly excluded)

The following are **implementation details**. Synthetic consumers, platform validation, and external integrators **must not** depend on them. Oracle failure if a consumer script uses them.

| Category | Examples | Why excluded |
|----------|----------|--------------|
| Historical import roots | Any `import` path other than `conrrad_sdk` and its documented subpackages | Not the public identity |
| File-path loading | `importlib.util.spec_from_file_location` on SDK files | Bypasses package graph |
| Manual path injection | `sys.path.insert(0, …)` in consumer code | Monorepo-only; not install contract |
| Internal modules | `conrrad_sdk._*`, loaders, sunset telemetry | Private by convention |
| Repository paths | File paths inside the SDK tree | Not a stable API |
| Removed symbols | `ensure_citizen()` | Removed in F009; permanent sunset |

**Implementer note:** The SDK may use internal implementation modules. Their names, layout, and dependency graph are **not** part of this contract and may change without a public API revision, provided the oracle in §5 remains green.

---

## 4. Bootstrap rules (normative)

### 4.1 Correct consumer bootstrap

```text
1. python -m venv .venv && source .venv/bin/activate
2. pip install -e .          # from conrrad-sdk root
3. from conrrad_sdk.pay import ConrradPayGateway
4. gateway = ConrradPayGateway(base_url=...)
5. gateway.register_citizen(developer_id=..., install_fingerprint=...)
```

### 4.2 Forbidden consumer patterns

```text
✗ spec_from_file_location("gateway_client", path/to/conrrad_sdk/pay/gateway_client.py)
✗ import from legacy namespace aliases (see migration program)
✗ ensure_citizen(...)
✗ Assuming conrrad-sdk submodule path without pip install
```

These patterns produced F008–F010. The SDK oracle exists to detect regressions.

---

## 5. SDK-SYN-01 oracle mapping

Each oracle step maps to a contract clause:

| Step | Clause | Sprint 1 |
|------|--------|----------|
| Create clean venv | §2.2 | required |
| `pip install -e .` | §2.2 | required |
| `import conrrad_sdk` | §2.1 | **required** |
| `import conrrad_sdk.pay` | §2.3 | **required** |
| `ConrradPayGateway(...)` | §2.4 | **required** |
| `register_citizen(developer_id=..., install_fingerprint=...)` | §2.4 | **required** (mock gateway allowed) |
| Validate `citizenId` in response | §2.4 | **required** |
| `conrrad_sdk.__version__` | §2.1 | **required** |
| Exit 0 | §2.2 | **required** |

On any failure: emit `SDK-SYN-001`, exit non-zero.

---

## 6. Versioning and change control

| Change type | Process |
|-------------|---------|
| Additive public symbol in §2 | Minor contract bump + oracle update + CI green |
| Breaking change to §2 | Major contract bump + migration note + auditor concurrence |
| Remove public symbol | Major bump; must not silently restore removed APIs (e.g. `ensure_citizen`) |
| Implementation-only refactor | Allowed if oracle PASS and §3 boundaries preserved |

Contract revisions increment `Version` in the header. Sprint 1 frozen at `1.0.1`.

---

## 7. Relationship to other contracts

| Document | Relationship |
|----------|----------------|
| `KERNELL_TO_CONRRAD_MIGRATION.md` | Historical namespace retirement program |
| `CONRRAD_SDK_INSTALL_CONTRACT.md` | Habitat genesis ceremony — complementary; CLI-SYN-01 |
| `CONRRAD_DOCTRINE_CONTRACT.md` | Constitutional semantics — upstream |
| VS-07B `certification/VS-07B/` | Historical evidence; immutable |
| PVP | SDK-SYN-01 is L1 for SDK component |

---

## 8. Sprint status

| Gate | Status |
|------|--------|
| `sdk_syn_oracle.py` | PASS (live) |
| `check_legacy_imports.py` | PASS (live) |
| CI `sdk-syn-oracle` + `legacy-gate` | PASS (live) |

**SDK-SYN-01: ACTIVE (PASS)** — contract frozen at v1.0.1. New failures open **SDK-SYN-00X** incidents; contract is not rewritten.

Deliverables complete:

- [x] Public API enumerated (§2)
- [x] Non-public surface enumerated (§3)
- [x] Contract principle (§0)
- [x] Oracle + CI + legacy inventory (MIG-001…003)

Next track: **CLI-SYN-01** (Day-0 CLI).

---

## Appendix A — Known technical debt (informational)

This appendix is **not** part of the public compatibility contract. It records implementation gaps scheduled for removal. The oracle protects §2 behavior; fixing debt below must not break §2.

| Item | Status | Target |
|------|--------|--------|
| Distribution metadata may still use legacy package naming in build files | Open | Rename to `conrrad-sdk` uniformly |
| Full eager import of all `conrrad_sdk.__all__` symbols may require native components | Open | Unified packaging or optional native extra |
| Historical namespace directories and wrappers remain in tree | Open | [KERNELL_TO_CONRRAD_MIGRATION.md](./KERNELL_TO_CONRRAD_MIGRATION.md) |

---

*Protect the contract first. Behavior coverage grows after the oracle is green.*
