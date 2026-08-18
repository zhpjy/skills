# Architecture decision framework

## Decision order

Prefer outcomes in this order unless evidence requires escalation:

`Preserve -> Extend -> Evolve -> Introduce -> Migrate`

### Preserve
Use when the requirement fits the current owner, contract, invariants, and dependency direction.

Question: can this be implemented naturally without creating hidden coupling or duplicated ownership?

### Extend
Use when an existing boundary remains correct but needs a new capability or contract operation.

Require:
- owner remains authoritative
- compatibility/failure semantics are understood
- extension does not leak internal representation

### Evolve
Use when a durable architecture fact must change.

Typical triggers:
- ownership moves
- contract semantics change
- dependency direction changes
- persistence/consistency boundary changes

Require explicit consequences and migration/compatibility handling when relevant.

### Introduce
Add a new architectural element only when existing boundaries cannot absorb the pressure cleanly.

Evidence can include:
- distinct authoritative ownership/lifecycle
- independent deployment or failure-isolation need
- strong security/compliance boundary
- materially different scaling/runtime constraints
- repeated independent change pressure

A cleaner diagram is not evidence.

### Migrate
Use when current and target states must coexist.

Define:
- current state
- target state
- transition states
- compatibility/data movement
- cutover gate
- rollback/reversal
- observability
- cleanup conditions

## Decision pressure test

A new abstraction or boundary should answer at least one present pressure:
- correctness/invariant protection
- ownership clarity
- compatibility
- independent lifecycle
- failure isolation
- security/compliance
- measurable performance/scale constraint
- repeated variation/change pressure
- migration constraint

If none applies, prefer a simpler implementation.

## Reversibility test

For expensive decisions, state:
- what makes reversal hard
- how to preserve an exit path
- what evidence would justify reconsideration

Do not over-engineer reversibility for cheap local decisions.
