# Output templates

## Contents

- Compact Architecture Change Packet
- ADR
- Implementation unit
- Migration packet
- Architecture audit
- Architecture extraction report


Use the smallest template that helps the decision.

For this repository, write all human-readable content produced from these templates in Simplified Chinese. Keep levels, IDs, field names, code symbols, database identifiers, and paths unchanged.

## Compact Architecture Change Packet

```markdown
# Architecture Change: <name>

Level: L1 | L2 | L3 | L4

## Current
- Owner/boundary: ...
- Relevant contract/invariant: ...

## Decision
Preserve | Extend | Evolve | Introduce | Migrate

<one short explanation of the smallest justified architecture delta>

## Constraints
- Must preserve: ...
- Allowed dependency/contract changes: ...
- Explicit non-goals: ...

## Implementation
- Affected units: ...
- Required tests/checks: ...

## Risks / assumptions
- ...

## Persistent architecture update
None | <specific architecture delta>
```

Omit empty sections. For L1, 3-8 bullets may be enough.

## ADR

```markdown
# ADR: <decision>

Status: accepted | proposed | superseded

## Context / pressure
...

## Decision
...

## Alternatives actually considered
- ...

## Consequences
- Benefits: ...
- Costs/failure modes: ...

## Migration / compatibility
...

## Reconsider when
...
```

Do not create an ADR merely because architecture was discussed.

## Implementation unit

```yaml
name: payment-refund-domain
owner: payment
may_change:
  - payment/domain/**
  - payment/application/**
may_not_change:
  - order/**
contracts:
  - RefundProvider
invariants:
  - PAYMENT-001
completion:
  - behavior tests
  - contract tests
  - architecture checks
```

## Migration packet

```markdown
# Architecture Migration: <name>

## Current state
...

## Target state
...

## Transition stages
1. ...
2. ...

## Compatibility/data movement
...

## Acceptance gates
- ...

## Rollback/reversal
...

## Observability
- ...

## Cleanup conditions
- ...
```

## Architecture audit

```markdown
# Architecture Audit

Result: PASS | PASS WITH WARNINGS | FAIL

## Verified
- ...

## Drift
- Classification: implementation defect | architecture evolution | benign detail | unresolved risk
  Evidence: ...
  Required action: ...

## Persistent state updates
- None | ...

## Rule candidates
- Repeated issue only; do not promote one-off findings automatically.
```

## Architecture extraction report

```markdown
# Architecture Extraction: <scope>

## Scope / evidence
- Scope: focused | baseline | full-system
- Scanned: ...
- Declared sources: ...
- Important unknowns: ...

## Recovered architecture
### Boundary: <name>
- Responsibility: ...
- Status: DECLARED | OBSERVED | INFERRED | CONFLICTED
- Confidence: high | medium | low
- Evidence: <files/symbols/tests/schemas>
- Owns: ...
- Contracts: ...
- Invariants: ...
- Dependencies: ...

## Ownership map
- <business fact> -> <authoritative owner> [status, confidence, evidence]

## Cross-boundary contracts
- <provider> -> <consumer>: <contract> [status, evidence]

## Invariants
- <invariant> [status, owner, evidence]

## Reconciliation / drift
- Declared: ...
- Observed: ...
- Classification: accepted architecture | implementation defect | architecture evolution | historical residue | unresolved conflict
- Action: ...

## Safe to persist
- <verified durable facts only>

## Unresolved
- <conflicts/unknowns that must not be silently persisted>
```

Do not force every boundary into identical detail. Use evidence citations to concrete repository files/symbols when available.
