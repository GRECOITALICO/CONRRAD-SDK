# SECURITY_INVARIANTS.md (v1.1)

## System Philosophy

CONRRAD SDK follows a zero-trust internal model with security-by-invariants:

- Every critical action must preserve authenticity, integrity, non-repudiation, and valid state transitions.
- Any invariant violation must fail closed with explicit rejection.

---

## Domain A — Execution / VSOCK

### E1 — Secret Required (Fail-Close)
- **Definition:** If `FC_VSOCK_SHARED_SECRET_B64` is missing/invalid (`< 32` decoded bytes), execution is rejected.
- **Evidence:** `test_vsock_requires_secret`.

### E2 — Frame Authenticity
- **Definition:** Accepted frame satisfies `HMAC_SHA256(canonical(frame_without_sig), k_ctx) == sig`.
- **Conditions:** Canonical serialization and stable key derivation (`k_exec`, `k_resp`).
- **Evidence:** fuzz tampering tests and HMAC mismatch tests.

### E3 — Replay Safety
- **Definition:** `(nonce)` cannot be accepted twice in replay window; stale timestamps are rejected.
- **Parameter:** recommended window `<= 30s`.
- **Evidence:** replay and stale timestamp tests.

### E4 — Payload Binding
- **Definition:** If `meta.payload_sha256` exists, `sha256(payload)` must match exactly.
- **Impact:** Prevents execution of unsigned/unauthorized payload.
- **Evidence:** payload-hash mismatch test.

### E5 — Context Binding
- **Definition:** Response context must match request context (`tenant_id`, `request_id`).
- **Evidence:** runtime response binding checks and integration tests.

### E6 — Host Pre-Validation
- **Definition:** `validate_code()` runs on host before delegating to VM channel.
- **Evidence:** runtime reject-before-send tests.

### E7 — Fail-Closed Parsing
- **Definition:** Parsing/framing/encoding/size errors must reject immediately.
- **Evidence:** malformed frame fuzz + length-prefix mismatch tests.

---

## Domain B — Cryptographic Ledger

### L1 — Hash-chain Integrity
- **Definition:** `event[i].prev_hash == event[i-1].event_hash`.
- **Evidence:** append-and-verify property tests.

### L2 — Entry Integrity
- **Definition:** `sha256(entry_json) == stored_hash`.
- **Evidence:** tampering tests.

### L3 — Signature Validity
- **Definition:** `kms.verify(tenant_id, entry_json, signature) == true`.
- **Mode:** Required in production; optional in dev/test by explicit config.
- **Evidence:** invalid-signature tests with `verify_signatures=True`.

### L4 — Append-Only
- **Definition:** No mutation of historical events (`UPDATE`/`DELETE` forbidden by policy).
- **Evidence:** full replay verification and audit process.

### L5 — Canonical Serialization
- **Definition:** All signatures/hashes computed over canonical JSON:
  `json.dumps(obj, sort_keys=True, separators=(",", ":"))`.
- **Risk mitigated:** representation ambiguity and signature bypass.

---

## Domain C — Escrow State Machine

### S1 — Valid States Only
- **Definition:** `state ∈ {CREATED, FUNDED, LOCKED, DISPUTED, EXPIRED, RELEASED, REFUNDED}`.
- **Evidence:** escrow property tests.

### S2 — Authorized Transitions
- **Definition:** Transition matrix:
  - `CREATE` by buyer from `NONE`
  - `FUND` by buyer from `CREATED`
  - `LOCK` by buyer from `FUNDED`
  - `RELEASE` by buyer/arbitrator from `LOCKED`
  - `DISPUTE` by buyer/seller from `LOCKED`
  - `REFUND` by arbitrator from `DISPUTED`/`EXPIRED`
- **Evidence:** strict state-machine tests.

### S3 — Signature Mandatory
- **Definition:** Every valid transition requires Ed25519 signature by authorized actor.
- **Evidence:** invalid-signature and property tests.

### S4 — Nonce Uniqueness
- **Definition:** `UNIQUE(contract_id, nonce)`.
- **Impact:** Blocks replay of economic actions.
- **Evidence:** replay/non-unique nonce tests.

### S5 — Expected State Match
- **Definition:** `expected_prev_state == current_state`.
- **Impact:** Prevents race/TOCTOU transitions.

### S6 — Terminal Finality
- **Definition:** `state ∈ {RELEASED, REFUNDED}` implies no further transitions.
- **Evidence:** property tests with terminal-state assertions.

---

## Domain D — Multi-Tenant & Traceability

### T1 — Tenant Attribution
- **Definition:** `tenant_id` is derived from verified credentials (JWT/mTLS/API key), never trusted from free-form input.

### T2 — Audit Completeness
- **Definition:** Every critical action emits an auditable event (execution and escrow transitions).

### T3 — Deterministic Failure
- **Definition:** No permissive fallback or silent ignore on invariant violations.

---

## CI Gating (Policy-as-Code)

### `security-fast` (PR blocking)
- `pytest -m "not slow"`
- Must cover critical checks in Execution, Ledger, and Escrow.

### `security-nightly`
- `pytest -m "slow"`
- Includes fuzz/property-heavy suites.

### `release-gate` (required)
- All domains green:
  - Execution: `E1–E7`
  - Ledger: `L1–L5`
  - Escrow: `S1–S6`
  - Tenant/Traceability: `T1–T3`

---

## Known Remaining Gaps

- Secret rotation policy (VSOCK/KMS) needs formalization.
- Explicit DoS/rate-limit policy should be versioned as invariant spec.
- Cross-tenant adversarial tests should be expanded.
- Host compromise boundaries must stay documented as model limits.

