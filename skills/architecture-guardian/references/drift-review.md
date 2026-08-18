# Architecture drift review

Review only architecture-relevant deltas.

## Check order

1. **Ownership**
   - Did a new writer appear for another boundary's authoritative state?
   - Did a projection/cache become an accidental authority?

2. **Contracts**
   - Did cross-boundary calls bypass declared interfaces/events?
   - Did a public contract leak storage/framework internals?
   - Did compatibility/failure/idempotency semantics change silently?

3. **Dependencies**
   - Did a forbidden edge or cycle appear?
   - Did dependency direction reverse?
   - Did implementation require broad context that suggests an implicit boundary?

4. **Invariants and consistency**
   - Can the change violate a previously protected invariant?
   - Did a transaction boundary or consistency guarantee weaken?

5. **Persistence/data**
   - Did another module begin reading/writing internal tables directly?
   - Did data migration create dual-write or split-brain ownership risk?

6. **Operational boundaries**
   - Did deployment/failure/security semantics change without an explicit decision?

7. **Speculative structure**
   - Did implementation add abstractions, services, queues, caches, or frameworks not required by current pressure?

## Classification

### Implementation defect
The accepted architecture still fits, but code violates it.

Action: fix implementation; do not update architecture to excuse the violation.

### Architecture evolution
New evidence shows the durable architecture should change.

Action: accept explicitly, update persistent state/ADR if justified, and make implementation consistent.

### Benign implementation detail
The difference does not affect a durable architectural fact.

Action: do nothing architecturally.

### Unresolved risk
Migration/evidence is incomplete and neither code nor architecture can yet be declared final.

Action: record the concrete risk, owner, and exit/verification condition.

## Drift rule

Never resolve drift by automatically treating whichever side changed last as correct.
