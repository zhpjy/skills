---
name: architecture-guardian
description: Extract, govern, and evolve software architecture during AI-assisted development. Use when analyzing or reverse-engineering an existing codebase architecture; bootstrapping architecture state from code; reviewing architecture or drift; or designing a feature, refactor, migration, API/domain-model change, service/module split, data-ownership change, dependency change, ADR, architecture-first/ABSD/spec-driven workflow, or post-implementation review that may affect boundaries, ownership, contracts, invariants, persistence, consistency, deployment, or long-term evolvability. Separate observed code facts from intended architecture, classify change impact before redesign, prefer the smallest justified evolution, persist only verified durable facts, and avoid heavy ceremony for local work.
---

# Architecture Guardian

Keep an AI-modified codebase coherent without turning architecture into a documentation tax.

Treat architecture as durable constraints on change: boundaries, ownership, contracts, invariants, dependency direction, persistence/consistency semantics, failure domains, and costly decisions. Do not treat directory structure, pattern names, or diagrams as architecture by themselves.

## Core policy

1. Inspect evidence before redesigning anything.
2. Use the lowest architecture impact level supported by evidence.
3. Prefer the smallest architecture change that makes the requested change natural.
4. Preserve established ownership, contracts, invariants, and dependency direction unless concrete pressure requires evolution.
5. Persist only durable architectural facts that are likely to constrain multiple future changes or are costly to rediscover.
6. Do not introduce abstractions for hypothetical reuse, scale, or future flexibility.
7. Separate declared intent, observed implementation facts, inferences, conflicts, assumptions, decisions, and unknowns.
8. Never equate current code structure with intended architecture without reconciliation.
9. Ask the user to choose only when alternatives materially change product semantics, compatibility, ownership, consistency, irreversible data decisions, security/compliance, migration risk, or operational cost.
10. After implementation, reconcile code and intended architecture instead of silently accepting drift.
11. Promote repeated architecture lessons into rules or automated checks only after evidence shows recurrence.
12. For this repository, all human-readable architecture descriptions and unresolved-conflict documents must use Simplified Chinese. Keep machine-readable keys, identifiers, status values, class names, table names, and paths unchanged.

## 1. Choose the task mode

Use the mode that matches the request:

- **Change design**: place a feature or behavior into an existing system.
- **Architecture review**: evaluate boundaries, ownership, dependencies, contracts, invariants, and structural risk.
- **Refactor/migration**: evolve architecture while controlling transition risk.
- **Drift review**: compare implemented code with intended architecture.
- **Greenfield**: define only the minimum architecture required by the next real milestones.
- **Architecture extraction**: reverse-engineer boundaries, ownership, contracts, invariants, dependencies, and conflicts from an existing codebase using evidence-backed inference.
- **Architecture-state bootstrap**: create a compact persistent `architecture/` model when the project will benefit from one.

Do not force all modes through the same workflow.

For **Architecture extraction**, follow `references/architecture-extraction.md`. Use the bundled discovery/dependency scripts when repository access exists, then inspect the code behind architecture-relevant findings. Keep `DECLARED`, `OBSERVED`, `INFERRED`, and `CONFLICTED` distinct. Do not persist unresolved hypotheses as Architecture IR. If extraction is performed only to support a specific change, keep it focused on that change surface.

## 2. Classify architecture impact before designing

For a pure extraction/reverse-architecture request, do not invent a change level. Use L0-L4 only when evaluating or planning a change.

Use `references/change-levels.md`.

- **L0 — Mechanical/local**: no semantic architecture impact.
- **L1 — In-boundary behavior**: meaningful behavior change inside one established owner/boundary.
- **L2 — Cross-boundary interaction**: affects multiple owners/boundaries or an existing public contract, without changing authoritative ownership or major system topology.
- **L3 — Boundary evolution**: changes ownership, public API semantics, dependency direction, persistence ownership, consistency boundary, or subsystem boundary.
- **L4 — System evolution**: decomposition/merge, major migration, rewrite, new subsystem/platform, event-sourcing/CQRS adoption, or broad topology change.

Use the lowest level supported by evidence. Do not escalate work merely because a sophisticated design is possible.

## 3. Gather the smallest sufficient evidence

Inspect only what is needed to understand the affected area. Prefer:

1. project architecture docs and live ADRs, if present
2. relevant package/module/service boundaries and public interfaces
3. affected domain model and terminology
4. persistence/schema ownership
5. dependency edges across affected boundaries
6. tests that encode contracts or invariants
7. deployment, reliability, security, scale, latency, or failure constraints when materially relevant
8. roadmap/evolution evidence only when it is concrete enough to affect today's decision

If the project maintains `architecture/`, load a minimal context pack rather than the whole directory. Read `references/context-pack.md`. When `implementation.yaml` exists, use it to bind logical boundaries to real source files, symbols, and tests. When `work-units.yaml` exists, use it as the authoritative Agent file-scope and shared-hotspot ownership map; do not assign work from `modules/` alone. Read `references/context-pack.md`.

For repository-wide or legacy-code extraction, use `scripts/discover_repository.py` and `scripts/extract_dependencies.py` as deterministic evidence collectors when useful. Their output is structural evidence only; semantic boundaries and ownership still require code-level interpretation. Read `references/architecture-extraction.md`.

If evidence is incomplete, proceed with explicit reversible assumptions when possible. Stop for user input only when a useful decision cannot be made safely without it.

### Language of persisted architecture

The persisted architecture state under `architecture/` and any architecture extraction report for this repository must use Simplified Chinese for prose, descriptions, decisions, assumptions, and conflict analysis. YAML field names, module and contract IDs, status values, code symbols, database identifiers, and file paths remain stable machine-readable identifiers and should not be translated.

## 4. Model current state before target state

For the affected area, identify:

- responsibility/boundary
- authoritative owner of mutable business facts
- public contracts and integration paths
- inbound/outbound dependencies
- invariants
- persistence and consistency boundary
- operational constraints if relevant
- known transition state or accepted debt

Do not infer ownership from folder names alone. Do not produce a full-system map unless the request needs one.

## 5. Run the architecture fit test

Before introducing or changing an architectural element, ask:

1. Which existing owner most naturally owns this behavior or fact?
2. Can the change fit there while preserving invariants?
3. Does it require a new cross-boundary dependency or public contract?
4. Would it duplicate ownership of state or business rules?
5. Does it leak internal representation or framework types across a boundary?
6. Does it create a dependency cycle or reverse an intended dependency direction?
7. Is a new abstraction solving repeated present pressure, or only imagined future reuse?
8. Is a new module/service justified by ownership, independent lifecycle, deployment, scale, security, failure isolation, or team/runtime boundary needs?
9. Is the target design simpler than an explicit transition path from the current state?

Choose one outcome:

- **Preserve**: no architecture change.
- **Extend**: add capability inside existing ownership/boundaries.
- **Evolve**: deliberately change a boundary, contract, ownership rule, dependency direction, or consistency rule.
- **Introduce**: add a new architectural element because existing boundaries cannot absorb the requirement cleanly.
- **Migrate**: define current state, target state, transition states, and rollback/reversal strategy.

Read `references/decision-framework.md` when the choice is non-obvious.

## 6. Spend architecture ceremony in proportion to impact

Use `references/output-templates.md`.

- **L0**: implement/review directly. At most note that there is no material architecture impact.
- **L1**: use a short Architecture Change Packet only if architecture guidance adds value. Do not create an ADR.
- **L2**: use a Change Packet focused on affected boundaries/contracts/invariants. Create an ADR only for a durable, costly, or non-obvious decision.
- **L3**: use a Change Packet and normally record the durable decision; include compatibility/migration implications.
- **L4**: use transition architecture, staged migration, rollback/reversal, observability and acceptance gates, and only the ADRs required to explain durable choices.

Do not generate alternatives when one design clearly dominates. Do not generate an ADR for a local, cheap, easily reversible decision.

## 7. Persist architecture state only when it earns its maintenance cost

A project does not need an `architecture/` directory merely because this Skill is active.

Persist a fact when at least one is true:

- it constrains multiple future changes or agents
- it defines authoritative ownership or a public boundary
- violating it would create meaningful correctness, compatibility, security, or operational risk
- it is costly or ambiguous to rediscover from code
- it is a durable decision whose rationale matters during future change
- it can be checked by tests/static validation and benefits from explicit declaration

Do **not** persist transient implementation detail, one-feature plans, file inventories, obvious code facts, speculative future designs, or prose that will immediately go stale.

When persistent state is justified, use the compact IR in `references/architecture-ir.md`. Bootstrap from `assets/architecture-starter/` only when the user/project wants durable architecture state.

For a repository that supports Agent parallelism, persist the implementation mapping separately from logical boundaries and persist Agent work units separately from both. Implementation mappings describe current code evidence; work units describe allowed change scope, forbidden scope, tests, contracts, invariants, and shared-hotspot ownership. Neither layer should pretend that a conceptual boundary is already a code module.

Update architecture state only for **architecture deltas**. Do not rewrite unrelated files after every feature.

## 8. Translate decisions into agent-safe implementation constraints

When implementation planning is requested, create only as much plan as needed. For parallel AI work, use implementation units with:

- owned scope
- allowed context
- contracts to consume or change
- invariants to preserve
- files/modules that may change
- files/modules that must not change
- completion tests/checks

Freeze or version shared public contracts before parallel work when multiple agents depend on them. Avoid fake parallelism that makes several agents edit the same unstable core files.

Read `references/context-pack.md` for agent context packs.

## 9. Review implementation for drift

After code changes, inspect architecture-relevant deltas, not only test results. Read `references/drift-review.md` and `references/review-checklist.md`.

Classify each discrepancy as:

- **Implementation defect**: code violates an accepted architectural constraint; fix code.
- **Architecture evolution**: the implementation exposes a necessary/better durable boundary; update architecture deliberately.
- **Benign implementation detail**: no durable architecture consequence; do not create documentation churn.
- **Unresolved risk**: evidence is insufficient or migration is incomplete; record the risk and required follow-up.

When an `architecture/` directory exists, run:

```bash
uv run .agents/skills/architecture-guardian/scripts/validate_architecture.py <architecture-dir>
```

Use `--strict` in CI or when bootstrapping should fail on placeholders and unresolved references. Treat structural validation as a baseline, not architectural judgment.

Strict validation must check implementation file paths, Java classes/methods, test paths, work-unit references, may-change/must-not-change overlap, and unique shared-hotspot ownership when `implementation.yaml` and `work-units.yaml` are present.

The bundled Python scripts use PEP 723 inline metadata for their runtime dependencies. Run them with `uv`; do not install `PyYAML` into the project environment or rely on the system Python:

```bash
uv run .agents/skills/architecture-guardian/scripts/discover_repository.py <repo-root> \
  --output /tmp/repo-discovery.json
uv run .agents/skills/architecture-guardian/scripts/extract_dependencies.py <repo-root> \
  --output /tmp/repo-dependencies.json
uv run .agents/skills/architecture-guardian/scripts/validate_architecture.py --strict <architecture-dir>
```

The dependency block is kept as comments at the top of each script so `uv` can create an isolated environment without adding a project-wide Python manifest. `validate_architecture.py` declares `pyyaml`; the evidence collectors declare no third-party dependencies.

## 10. Learn from recurrence

Promote knowledge gradually:

`observation -> heuristic -> guideline -> hard rule -> automated check`

Do not turn one incident into a permanent architecture rule. Automate only objective rules that have stable semantics.

## Anti-overengineering defaults

Treat the following as defaults, not universal laws:

- Do not add a service merely to make a diagram cleaner.
- Do not split a module solely because a file is large.
- Do not add repository/factory/strategy/adapter interfaces without a real boundary or repeated variation pressure.
- Do not add an event bus, queue, cache, plugin system, workflow engine, or distributed coordination for hypothetical future needs.
- Do not split authoritative data ownership without explicit lifecycle and consistency semantics.
- Do not introduce async/distributed coordination when local/synchronous interaction satisfies the requirement.
- Do not cite DDD, SOLID, Clean Architecture, Hexagonal, CQRS, microservices, or a design pattern as sufficient justification.
- Do not rewrite a working subsystem when bounded evolution solves the stated problem.
- Do not optimize for speculative scale without a concrete workload or quality-attribute requirement.

Read `references/anti-patterns.md` when a proposal is abstraction-heavy, distributed, or migration-heavy. Read `references/ddd-and-patterns.md` only when those modeling/pattern questions are actually relevant.

## Decision quality bar

A consequential recommendation must make clear:

- observed pressure or requirement
- relevant current architecture fact
- why the current boundary does or does not fit
- smallest viable architecture delta
- tradeoffs and new failure modes
- invariants/compatibility to preserve
- migration/reversal needs when applicable
- what evidence would cause reconsideration

If these cannot be stated, the architecture recommendation is probably premature.

## Output discipline

- Lead with the decision/consequence, not a generic architecture lecture.
- Prefer a compact change packet over a long design document.
- Cite concrete files, symbols, schemas, tests, or runtime constraints when available.
- Mark assumptions and unknowns explicitly.
- Persist human-readable architecture content in Simplified Chinese for this repository; preserve machine-readable identifiers exactly.
- Keep **Current state**, **Decision**, **Constraints**, **Implementation**, and **Risks** distinct.
- Generate diagrams only when topology or interaction is materially clearer visually.
- For greenfield systems, define a **Minimum Viable Architecture** and explicitly list deferred decisions.

## References

- `references/change-levels.md`: impact classification and ceremony budget.
- `references/workflow.md`: end-to-end state machine and branching rules.
- `references/context-pack.md`: minimal architecture context and agent work-unit packs.
- `references/architecture-extraction.md`: reverse-architecture workflow, evidence provenance, inference, reconciliation, and persistence rules.
- `references/architecture-ir.md`: compact persistent architecture state and write-back policy.
- `references/decision-framework.md`: Preserve / Extend / Evolve / Introduce / Migrate decision tests.
- `references/output-templates.md`: change packet, ADR, implementation unit, migration, and audit formats.
- `references/drift-review.md`: post-implementation drift classification.
- `references/review-checklist.md`: deeper architecture review checks and smells.
- `references/anti-patterns.md`: evidence thresholds for common overengineering moves.
- `references/ddd-and-patterns.md`: conditional DDD and pattern guidance.
