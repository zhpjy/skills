# Architecture impact levels

## Contents

- L0 Mechanical/local
- L1 In-boundary behavior
- L2 Cross-boundary interaction
- L3 Boundary evolution
- L4 System evolution
- Escalation and de-escalation tests
- Ceremony budget


The level controls architecture ceremony, not feature importance.

## L0 — Mechanical/local

Examples:
- formatting, copy, comments, CSS-only styling
- local rename with no public or semantic effect
- mechanical dependency upgrade that preserves contracts/behavior

Default action:
- implement directly
- no architecture artifact
- no ADR

Escalate only if inspection reveals a real boundary/contract/ownership consequence.

## L1 — In-boundary behavior

Examples:
- new behavior inside one established module/owner
- internal algorithm/data-structure change
- private refactor that preserves public contracts and ownership

Default action:
- inspect owning boundary and tests
- preserve existing contracts/invariants
- optional short Change Packet if it helps implementation
- no ADR

## L2 — Cross-boundary interaction

Examples:
- add a consumer to an existing contract
- extend an existing public operation/event without moving ownership
- add a new explicit integration between existing owners
- read data across a boundary through an approved contract

Default action:
- identify affected owners/contracts/invariants
- produce a compact Change Packet
- version/freeze contract if parallel work depends on it
- ADR only when the decision is durable, costly, or non-obvious

Do not classify a change as L3 merely because two modules are touched.

## L3 — Boundary evolution

Examples:
- move authoritative state or responsibility between modules
- change public API semantics or compatibility guarantees
- reverse dependency direction
- change transaction/consistency boundary
- split/merge a bounded context or major module
- change persistence ownership

Default action:
- model current and target states
- compare real alternatives
- record durable decision/rationale
- define compatibility and migration path
- audit implementation against new boundaries

## L4 — System evolution

Examples:
- service decomposition/merge across a substantial subsystem
- major data/platform/runtime migration
- rewrite with coexistence/cutover strategy
- broad event-driven/event-sourcing/CQRS adoption
- new platform or multi-region/topology architecture

Default action:
- define transition architecture, not only target architecture
- stage migration with measurable gates
- define rollback/reversal and data compatibility
- define observability and operational failure handling
- use the minimum ADR set needed for durable decisions

## Escalation tests

Escalate when the change materially affects one or more of:
- authoritative business-state ownership
- public/backward-compatible contract semantics
- dependency direction or cycle risk
- persistence ownership or data migration
- transaction/consistency guarantees
- security/compliance boundary
- deployment/failure isolation
- irreversible or expensive-to-reverse data/model decisions
- major operational topology/cost

## De-escalation tests

Stay at the lower level when:
- proposed abstractions are optional rather than required
- existing ownership can absorb the behavior cleanly
- only implementation organization changes
- public contracts remain stable
- no durable architectural fact changes
- the decision is cheap and reversible

## Ceremony budget

Use a default maximum, not a mandatory minimum:

| Level | Default architecture artifact |
|---|---|
| L0 | none |
| L1 | 3-8 bullets if useful |
| L2 | one compact Change Packet |
| L3 | Change Packet + durable decision/ADR |
| L4 | transition plan + minimal ADR set |

If the artifact is larger than the decision pressure justifies, simplify it.
