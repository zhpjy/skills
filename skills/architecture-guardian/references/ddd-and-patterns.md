# DDD and pattern policy

Use this reference only when domain modeling or a named pattern is relevant. Pattern names are not architecture evidence.

## DDD

### Bounded context
- Keep a coherent domain language per context.
- Make translation between contexts explicit when semantics differ.
- Do not share internal domain models merely to avoid duplication.
- Do not invent bounded contexts without distinct language/ownership/change pressure.

### Aggregate
Defaults:
- external mutation enters through the aggregate root
- aggregate boundary protects invariants/consistency
- reference other aggregates by identity unless a stronger invariant requires otherwise

A transaction spanning multiple aggregates is a diagnostic signal, not an automatic error.

### Entity/value object
- Entity: identity/lifecycle matters across time.
- Value object: equality by value; prefer immutability.
- Do not create entities for data with no lifecycle identity.

### Repository
Use for aggregate-oriented persistence abstraction when it protects domain boundaries or provides a real seam. Do not create repositories for every table or CRUD object by default.

### Domain event
Use for a meaningful domain fact that occurred. When crossing process boundaries, define delivery/idempotency/ordering assumptions that affect correctness.

### Ubiquitous language
Persist canonical terms only when vocabulary drift can cause modeling or integration errors.

## Hexagonal / ports and adapters
Use ports at real external/architectural boundaries. Do not add a port around every internal function.

If domain isolation is a chosen constraint:
- domain must not depend on HTTP/ORM/broker/UI/framework types
- application may depend on domain
- adapters implement inbound/outbound ports
- dependency direction points inward

## CQRS
Use only when read/write needs materially diverge. Do not introduce separate infrastructure merely to satisfy the label.

## Event-driven design
Use when temporal decoupling, ownership, fan-out, resilience, or independent evolution justify eventual consistency.

Define relevant:
- event owner
- delivery semantics
- idempotency
- ordering assumptions
- retry/dead-letter behavior

## Saga/process manager
Use for long-running cross-boundary workflows that cannot be one local transaction. Model compensation and terminal failure explicitly.

## Common design patterns
Apply only when their force exists now or is supported by committed/repeated evolution:
- Strategy: multiple real replaceable behaviors
- Adapter: isolate an external interface/model
- Factory: creation complexity/invariants justify centralization
- State: lifecycle behavior materially varies by state

Avoid speculative factories, interfaces, inheritance, and generic frameworks for a single stable implementation.
