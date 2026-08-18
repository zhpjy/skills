# Architecture Context Pack

A Context Pack is the minimum sufficient architecture context for one task or agent.

## Goal

Reduce context radius without hiding constraints that can make the change incorrect.

## Pack contents

Include only relevant items:

```text
Task intent
Known constraints
Current owner/boundary
Affected domain terms
Changed/consumed contracts
Relevant invariants
Allowed/forbidden dependencies
Persistence/consistency rules
Relevant live ADR rationale
Concrete expected evolution, if decision-relevant
Open assumptions/unknowns
```

## Selection rules

Always include:
- the current owner/boundary for the changed behavior/fact
- every public contract the task changes
- every invariant the task can violate
- any hard global rule that actually applies

Include conditionally:
- adjacent boundaries only when interaction changes
- ADRs only when they explain a live constraint or choice
- quality attributes only when they affect the decision
- evolution entries only when backed by a committed/repeated change pressure
- DDD/pattern guidance only when the modeling question needs it

Exclude by default:
- unrelated modules
- full dependency implementation trees
- stale historical docs
- generic architecture theory
- file inventories that do not constrain the change

## Evidence labels

For architecture extraction, use these provenance labels consistently:
- `DECLARED`: explicitly stated by project architecture/docs/contracts
- `OBSERVED`: directly demonstrated by live code/config/tests/schema/runtime evidence
- `INFERRED`: best architectural explanation of multiple observations
- `CONFLICTED`: credible evidence supports incompatible interpretations

For change planning, add when needed:
- `ASSUMPTION`: required to proceed but not verified
- `DECISION`: chosen architecture direction
- `UNKNOWN`: missing evidence that could change the decision

Do not overload small outputs with labels; use them when ambiguity matters. Never collapse `DECLARED` and `OBSERVED` into one fact when drift is plausible.

## Agent work unit

For coding agents, narrow the pack further:

```yaml
task: implement-refund-policy
owner: payment
may_change:
  - payment/domain/**
  - payment/application/**
may_not_change:
  - order/**
contracts:
  - RefundProvider
invariants:
  - REFUND-001
assumptions:
  - payment remains authoritative for refund state
completion:
  - behavior tests pass
  - contract tests pass
  - architecture checks pass
```

If an agent repeatedly needs undeclared context, treat that as a signal of an implicit boundary, hidden shared state, unstable contract, or unclear ownership.

For this repository, the persisted Agent work units are in `architecture/work-units.yaml`. Use the selected unit's `may_change`, `must_not_change`, `implementation_symbols`, `test_paths`, `contracts`, `invariants`, and `shared_hotspots` as the work-scope contract. Use `architecture/implementation.yaml` to resolve each symbol to current source files and tests. Do not infer an Agent scope from `architecture/modules/` alone.
