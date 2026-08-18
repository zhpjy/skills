# Architecture anti-patterns and evidence thresholds

## Premature service extraction
Warning signs:
- extraction justified by diagram cleanliness, file size, or "future scale"
- shared database remains the real owner
- synchronous chatty calls replace local calls

Evidence that can justify extraction:
- independent ownership/lifecycle
- deployment/failure isolation requirement
- distinct security/compliance boundary
- materially different scaling/runtime profile
- repeated independent change pressure

## Speculative abstraction
Warning signs:
- one implementation, one caller, no variation pressure
- interface/factory/strategy exists only to be "flexible"

Require at least one real force: repeated variation, external boundary, test seam with material benefit, or committed evolution.

## Shared database as integration contract
Warning signs:
- multiple boundaries write the same tables
- schema becomes public API unintentionally

Prefer explicit ownership and contract; allow exceptions only when tradeoff is deliberate and documented.

## Event-driven by fashion
Warning signs:
- no need for temporal decoupling/fan-out/resilience
- eventual consistency cost is not modeled
- delivery/idempotency/order failure semantics are unspecified

## CQRS/event sourcing without decision pressure
Require concrete read/write divergence, audit/reconstruction needs, consistency model, or scale/operational pressure. Pattern name alone is insufficient.

## Generic platform/framework too early
Warning signs:
- feature work is delayed to build a reusable internal platform
- extension points have no real consumers

Prefer product-specific implementation until repeated pressure reveals stable commonality.

## Architecture documentation mirroring code
Warning signs:
- architecture files enumerate classes/files
- every refactor requires documentation edits

Persist durable constraints, not implementation inventory.

## Target-state-only migration
Warning signs:
- proposal explains final architecture but not coexistence, data movement, compatibility, rollback, or cutover

For L4 work, transition states are part of the architecture.
