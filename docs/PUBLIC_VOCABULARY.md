# CONRRAD Public Vocabulary (frozen)

| Field | Value |
|-------|--------|
| **Status** | **FROZEN** — product-facing SSOT |
| **Rule** | Public Vocabulary Rule (below) |
| **Budget** | 5 core concepts for onboarding |
| **Economics SSOT** | [ECONOMIC_VOCABULARY.md](ECONOMIC_VOCABULARY.md) |
| **Ontology SSOT** | [CANONICAL_MODEL.md](CANONICAL_MODEL.md) |
| **Historical policy** | [LEGACY_ELIMINATION_POLICY.md](LEGACY_ELIMINATION_POLICY.md) · [CVS-001](CVS-001_CANONICAL_VOCABULARY_SWEEP.md) |

---

## Public Vocabulary Rule

No README, example, user doc, landing page, video, CLI message, error string, or tutorial may introduce a term outside the **product vocabulary** unless explicitly marked as *Platform* or *Operator* documentation.

Historical terms do not belong in the public SDK. Historical names live only in [docs/history/PROJECT_EVOLUTION.md](history/PROJECT_EVOLUTION.md).

**Architectural owner rule:** every concept has exactly one canonical owner; every public symbol maps to a canonical ID in [CANONICAL_MODEL.md](CANONICAL_MODEL.md).

---

## Three languages

| Layer | Audience | When |
|-------|----------|------|
| **Product** | Developers | First contact — README, PyPI, Quick Start, examples, CLI |
| **Platform** | Operators / production users | After `deploy` — Citizen, Observatory, CONRRAD Pay, SEAL (brief), policies |
| **Internal** | Engineering / audit | Never in user onboarding — ROA, gates, TD-*, DEC-* |

---

## Vocabulary budget (onboarding)

Maximum **5 new concepts** in the first 10 minutes:

| Term | Meaning |
|------|---------|
| **CONRRAD** | The platform |
| **Agent** | What the developer creates |
| **Task** | What the Agent executes |
| **Audit Trail** | What happened and why |
| **Deploy** | Moving from local dev to production |

Everything else is discovered later.

---

## Product vocabulary (allowed in public copy)

| Term | Usage |
|------|--------|
| CONRRAD | Platform name |
| conrrad-sdk | PyPI package |
| conrrad | CLI command |
| Agent | `from conrrad import Agent` |
| Task | Input to `agent.run(...)` |
| run / `agent.run()` | Execute a task locally |
| deploy / `conrrad deploy` | Production path |
| Audit Trail | Trace of steps during a run |
| Budget | Cost control — **introduce at deploy stage only** |
| Memory | Agent context (optional, post-hello) |

**At deploy (one line):** *"This deployment uses CONRRAD Pay. Usage is metered automatically. Internally, all economic operations are denominated in SEAL."* — one mention of SEAL; no wallets, ledger, or contracts in onboarding.

---

## Platform vocabulary (after deploy only)

| Term | When |
|------|------|
| Citizen | Deployed agent identity |
| Observatory | Ops / telemetry dashboard |
| CONRRAD Pay | Executes economic operations — budgets, metering, billing (landing, invoices) |
| SEAL | Native unit of account — one sentence at deploy |
| Trust Authority | Platform pillar — **architecture & ADR only**; governs all verifiable interaction |
| Deterministic Trust Ledger | Records Trust Authority events — operator / ADR only |
| Harlemm | Host governor (operator docs) |
| Economic Router | Inference cost routing (operator docs) |
| Runtime · Policy Engine | Production ops |

Do not use in Quick Start, `examples/hello.py`, or `conrrad new hello`.

---

## Internal vocabulary (engineering only)

ROA · Gates · TD-* · DEC-* · BI-* · Fase A · Bundle · Validator · Governance Schema · Sully · Swarm · OMEGA · KAP · Seal Engine (causal evidence — distinct from SEAL currency)

Historical names (Kernell, KERN): [docs/history/](history/PROJECT_EVOLUTION.md) only — never in public SDK after CVS-001.

---

## Developer journey (phases)

```text
conrrad new hello  →  code  →  conrrad run  →  test  →  conrrad deploy
                                                              ↓
                                         CONRRAD Pay · Budget (product message)
                                                              ↓
                                         Citizen · Observatory · SEAL (platform)
```

`conrrad init --full` (Docker / Redis / Qdrant) is **infrastructure prep**, not Quick Start.

---

## Economic terms (summary)

| Concept | Layer | Public onboarding? |
|---------|-------|-------------------|
| **Budget / Usage** | Product (deploy+) | ✅ |
| **CONRRAD Pay** | Platform | ✅ after deploy |
| **SEAL** | Platform / operator | ❌ Quick Start; ✅ deploy/enterprise |
| **Deterministic Trust Ledger** | Platform / operator | ❌ — ADR/operator only |

Full model: [ECONOMIC_VOCABULARY.md](ECONOMIC_VOCABULARY.md)

---

## Product vs architecture (naming rule)

Architecture diagrams and ADR use **Trust Authority** (governs) and **Deterministic Trust Ledger** (records). Landing pages, checkout, and billing use **CONRRAD Pay** (executes economic operations). The names need not match (cf. IAM vs AWS Billing).

---

## Platform domains (three pillars)

```text
Execution          → runs Agents and Runtime
Trust Authority    → governs every verifiable interaction
Observability      → telemetry, audit, diagnostics (Observatory)

Within Trust Authority:
  Pay    → executes economic operations
  Ledger → records Trust Authority events (multiple producers, not Pay-only)
  SEAL   → denominates economic events
```

| Component | Responsibility |
|-----------|----------------|
| **Trust Authority** | Governs verifiable interactions |
| **CONRRAD Pay** | Executes economic operations |
| **Deterministic Trust Ledger** | Records Trust Authority events deterministically |
| **SEAL** | Native unit of account |

Full model: [ECONOMIC_VOCABULARY.md](ECONOMIC_VOCABULARY.md)
