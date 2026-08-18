# Architecture Extraction / Reverse Architecture

Use this workflow when architecture must be recovered from an existing codebase, especially when documentation is missing, stale, partial, or contradicted by implementation.

The goal is not to describe folders. The goal is to recover durable architectural facts and explicitly surface ambiguity or drift.


## Contents

1. Choose extraction scope
2. Discover declared intent
3. Collect deterministic repository evidence
4. Build an evidence ledger
5. Infer boundaries from behavior, not folders
6. Infer authoritative ownership
7. Extract contracts
8. Extract invariants
9. Reconcile current structure and intended architecture
10. Produce a provisional architecture model
11. Persist only verified durable facts
12. Extraction quality bar

## Core rule

Separate evidence collection from architectural interpretation:

`repository facts -> evidence ledger -> architecture hypotheses -> reconciliation -> verified durable facts -> optional Architecture IR`

Scripts extract facts. The model infers architecture. Never let a directory layout, class name, framework annotation, or current dependency edge become an architectural truth by itself.

## 1. Choose extraction scope

Use the smallest scope that satisfies the request:

- **Focused extraction**: one feature area, subsystem, service, domain, or change surface.
- **Baseline extraction**: enough of the repository to create an initial architecture map.
- **Full-system extraction**: only when the user explicitly needs a broad system model, migration baseline, or architecture audit.

For a focused change, do not map the whole repository merely because it is available.

## 2. Discover declared intent

Before inferring from code, look for explicit architecture declarations:

- architecture docs and diagrams
- ADRs/RFCs/design docs
- module/service READMEs
- public API or schema documentation
- ownership files such as CODEOWNERS when relevant
- deployment manifests when topology matters
- database/schema ownership notes

Treat these as **DECLARED**, not automatically correct. Verify live facts when drift is plausible.

For this repository, write all persisted architecture prose and extraction reports in Simplified Chinese. Preserve YAML keys, IDs, status values, code symbols, database identifiers, and paths as machine-readable identifiers.

If the repository has `implementation.yaml` or `work-units.yaml`, treat them as separate layers: the former maps logical boundaries to observed code seams; the latter defines Agent change scope and shared-hotspot ownership. Do not use a logical boundary as an Agent work boundary unless the implementation mapping and work-unit path rules support it.

## 3. Collect deterministic repository evidence

When repository access exists, use the bundled scripts as accelerators:

```bash
uv run .agents/skills/architecture-guardian/scripts/discover_repository.py <repo-root> --output /tmp/repo-discovery.json
uv run .agents/skills/architecture-guardian/scripts/extract_dependencies.py <repo-root> --output /tmp/repo-dependencies.json
```

These scripts use PEP 723 comment metadata for dependencies. `uv` creates the isolated runtime from the declaration in each script; do not use `pip install` or assume that the system Python has `PyYAML`.

Read the generated summaries, then inspect the code behind architecture-relevant findings.

`discover_repository.py` inventories language/file distribution, manifests, likely architecture docs, tests, schema/migration locations, entrypoint candidates, and top-level structure.

`extract_dependencies.py` extracts best-effort static import/dependency evidence for supported source forms. It does not know semantic boundaries or ownership and must not be treated as a full compiler/static analyzer.

For ecosystems with stronger native tooling, prefer project-native dependency or build tools when available and interpret their results using the same evidence rules.

## 4. Build an evidence ledger

Every architecture-relevant statement must be one of:

- **DECLARED**: explicitly stated by architecture docs, ADRs, schemas, or other authoritative project declarations.
- **OBSERVED**: directly demonstrated by live code, configuration, tests, runtime topology, database schema, or dependency facts.
- **INFERRED**: the best architectural explanation of multiple observations, but not explicitly declared.
- **CONFLICTED**: credible evidence points to incompatible interpretations or declared intent and implementation disagree.

Use confidence labels `high`, `medium`, or `low`. Avoid fake numerical precision.

Example:

```yaml
claim: Payment is the authoritative owner of payment state
status: INFERRED
confidence: high
evidence:
  - PaymentRepository is defined under the payment subsystem
  - payment state transitions are enforced by payment domain logic
  - payment migrations define the authoritative payment tables
conflicts:
  - OrderService directly updates payment.status
interpretation: likely ownership violation; requires reconciliation before persistence
```

## 5. Infer boundaries from behavior, not folders

A candidate boundary becomes credible when multiple signals align, for example:

- cohesive business responsibility and vocabulary
- independent state lifecycle or authoritative data ownership
- stable public interface or integration surface
- dependency direction that separates internals from consumers
- tests organized around the same responsibility
- deployment/failure/scaling/security boundary when materially relevant
- change history or ownership patterns, if available and relevant

Folder/package structure is supporting evidence only.

Do not create a boundary merely because a directory exists. Do not merge responsibilities merely because code shares a package.

## 6. Infer authoritative ownership

For each important mutable business fact, ask which component is authoritative.

Strong ownership evidence includes:

- writes/creates the canonical state
- enforces lifecycle transitions and business invariants
- owns the persistence schema or repository abstraction
- emits authoritative state-change events
- serves the canonical read/command interface
- other components call it rather than mutate its storage directly

If several components independently mutate the same fact, classify this as **CONFLICTED** or an explicit shared-ownership design; do not silently choose one.

Projections, caches, search indexes, and replicas are not authoritative merely because they contain the data.

## 7. Extract contracts

Look for actual cross-boundary interaction surfaces:

- exported/public modules
- HTTP/RPC/GraphQL endpoints and clients
- message/event schemas and producers/consumers
- command/query interfaces
- shared data schemas
- database access crossing a candidate owner boundary

Capture behavior that matters for compatibility and correctness: input/output shape, error semantics, idempotency, ordering, retries, versioning, and consistency only when evidence supports them.

Do not call every internal function a contract.

## 8. Extract invariants

Look for durable rules encoded in:

- state transition checks
- domain validation
- database constraints
- transaction boundaries
- contract/integration tests
- property tests
- security/authorization checks
- explicit comments/docs that match code behavior

An observed check is not automatically a business invariant. Prefer rules that must remain true across implementations.

Mark an inferred invariant as provisional until evidence is strong enough to govern future changes.

## 9. Reconcile current structure and intended architecture

Do not equate implementation with intent.

For each important discrepancy, classify it as:

- **Accepted architecture**: declaration and implementation align, or evidence strongly supports the design.
- **Implementation defect**: code violates a credible declared/intended architectural constraint.
- **Architecture evolution**: implementation reveals a deliberate or necessary new durable boundary/contract/ownership rule.
- **Historical residue**: transitional or obsolete structure that should not define future architecture.
- **Unresolved conflict**: evidence is insufficient to choose safely.

Example:

```text
Observed: OrderService writes payment tables directly.
Declared: Payment owns payment lifecycle and storage.
Interpretation: implementation defect, not a new Order -> payment.persistence architectural rule.
```

## 10. Produce a provisional architecture model

For a baseline extraction, summarize only evidence-supported concepts:

- candidate boundaries and responsibilities
- authoritative ownership map
- cross-boundary contracts
- key invariants
- allowed/actual dependency directions
- persistence/consistency boundaries
- deployment/failure boundaries when relevant
- conflicted areas and unknowns

Do not hide uncertainty to make the architecture look clean.

## 11. Persist only verified durable facts

If the project wants persistent `architecture/` state, write only facts that pass both tests:

1. **Evidence test**: confidence is sufficient and material conflicts are resolved or explicitly modeled.
2. **Durability test**: the fact will constrain future changes or is expensive/ambiguous to rediscover.

Do not persist the entire evidence ledger, transient hypotheses, raw file inventories, or every dependency edge. Those are extraction artifacts, not Architecture IR.

Use `references/architecture-ir.md` for the durable form.

## 12. Extraction quality bar

A useful extraction must make clear:

- what is directly declared
- what is directly observed
- what is inferred and why
- what conflicts
- what remains unknown
- which current code relationships are likely architectural versus incidental
- which facts are safe to persist and govern against

A neat diagram without this provenance is not sufficient.
