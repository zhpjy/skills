# Compact Architecture IR

## Contents

- Core concepts
- Optional concepts
- Evolution semantics
- Recommended layout
- Source-of-truth policy
- Extraction provenance boundary


Persistent architecture state is optional. Use it when durable facts need to survive across features, agents, and time.

## Core concepts

Prefer five core concepts. Add optional concepts only when they solve repeated real needs.

### 1. Boundary
A responsibility boundary such as a module, service, bounded context, subsystem, or package-level architecture unit.

```yaml
name: payment
purpose: Own payment authorization, capture, refund, and payment state.
owns: [Payment, Refund]
public_api:
  commands: [AuthorizePayment, RefundPayment]
  queries: [GetPayment]
  events: [PaymentCaptured, PaymentRefunded]
dependencies: [ledger]
forbidden_dependencies: [order.persistence]
```

Do not list every class/file. Record durable boundary facts.

### 2. Ownership
Ownership answers: which boundary is authoritative for a mutable business fact?

Defaults:
- one mutable business fact has one authoritative owner
- projections/caches may duplicate data but must not become ambiguous authorities
- cross-boundary mutation of another owner's persistence is prohibited unless an explicit exception is recorded

### 3. Contract
A contract defines permitted cross-boundary interaction.

```yaml
name: RefundProvider
provider: payment
consumers: [support]
operations:
  request_refund:
    input: [payment_id, amount]
    output: refund_id
    errors: [NOT_REFUNDABLE, INVALID_AMOUNT]
    guarantees: [idempotent]
```

Record failure/idempotency semantics only when correctness depends on them.

### 4. Invariant
An invariant is a durable statement that must not become false.

```yaml
invariants:
  - id: PAYMENT-001
    statement: A captured payment cannot be captured twice.
    owner: payment
    verification: [unit-test, integration-test]
```

Prefer business/architectural facts over implementation detail.

### 5. Decision
Use an ADR only for durable, costly, non-obvious choices whose rationale will matter later.

Capture:
- context/pressure
- options actually considered
- decision
- tradeoffs/consequences
- migration/compatibility if relevant
- reconsider_when

## Optional concepts

Add only when useful:

- **Dependency**: when allowed/forbidden directions need explicit governance.
- **Scenario**: when cross-boundary behavior/invariants are easier to verify through executable narratives.
- **Evolution**: when concrete future change pressure should influence today's design.
- **Rule**: when repeated governance knowledge deserves a heuristic/guideline/error check.

## Evolution semantics

If using `evolution.yaml`, distinguish:
- `expected`: committed/repeated change pressure that may justify design support now
- `stable`: areas intentionally optimized for low churn
- `uncertain`: plausible ideas that **must not** justify new abstractions by themselves

## Recommended layout

```text
architecture/
  constitution.yaml
  system.yaml
  glossary.yaml
  invariants.yaml
  evolution.yaml          # optional
  modules/                # boundaries, only as needed
  contracts/              # only public/cross-boundary contracts worth persisting
  scenarios/              # optional
  decisions/              # ADRs only when durable
```

## Source-of-truth policy

Do not call `architecture/` the source of truth for facts that can only be validated in code/runtime. Instead:
- architecture state is the declared intent/contract
- code/tests/runtime are implementation evidence
- drift must be reconciled explicitly

Prefer generated diagrams/views from this state; do not require manual diagram maintenance.

## Extraction provenance boundary

When Architecture IR is bootstrapped from existing code, keep the extraction evidence ledger separate from persistent IR.

Temporary extraction artifacts may contain:
- `DECLARED` statements
- `OBSERVED` facts
- `INFERRED` hypotheses with confidence
- `CONFLICTED` evidence
- raw dependency/inventory output

Persist a fact into Architecture IR only after it is evidence-supported, materially unconflicted or explicitly modeled as an accepted exception/transition, and durable enough to justify maintenance.

Do not add confidence scores or raw file inventories to every long-lived IR item merely because they existed during extraction. Preserve provenance in an ADR or concise note only when future maintainers need it to understand a non-obvious decision.
