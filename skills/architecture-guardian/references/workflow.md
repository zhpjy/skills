# Architecture governance workflow

## Contents

- Governance state machine
- Architecture extraction state machine
- Decision policy
- Architecture-state write-back policy


## State machine

Use only the states required by the task:

`INTENT -> CLASSIFY -> EVIDENCE -> CURRENT -> FIT -> DECIDE -> [PERSIST] -> [PLAN] -> [IMPLEMENT] -> AUDIT -> LEARN`

Brackets denote optional states.

## Architecture extraction state machine

For reverse architecture, legacy-code discovery, or architecture-state bootstrap from code, use:

`SCOPE -> DECLARED -> SCAN -> INSPECT -> INFER -> RECONCILE -> [PERSIST] -> VERIFY`

### SCOPE
Choose focused, baseline, or full-system extraction. Default to focused extraction when supporting one change.

### DECLARED
Collect explicit architecture intent from ADRs, architecture docs, schemas, public contracts, ownership files, and deployment declarations. Label it `DECLARED`; do not assume it matches implementation.

### SCAN
Collect deterministic repository facts. Run the bundled collectors with `uv run` when helpful, using the PEP 723 dependencies declared in their comment headers. Treat path groups/import edges as structural evidence, not semantic boundaries.

### INSPECT
Read architecture-relevant code behind the scan: state writers, lifecycle logic, public interfaces, schemas/migrations, tests, integration points, and runtime/deployment configuration.

### INFER
Propose boundaries, authoritative ownership, contracts, invariants, dependency direction, and persistence/consistency boundaries. Label inferred claims and confidence explicitly.

### RECONCILE
Compare declared intent with observed implementation. Classify discrepancies as accepted architecture, implementation defect, architecture evolution, historical residue, or unresolved conflict.

### PERSIST
Persist only verified durable facts. Do not persist raw scan output, unresolved hypotheses, or incidental dependencies.

### VERIFY
Check that every persisted fact has enough evidence, material conflicts are represented or resolved, and no folder/name heuristic was promoted to architecture without behavioral evidence.

Read `architecture-extraction.md` for the detailed workflow and evidence rules.


### INTENT
Capture business/engineering outcome and constraints. Do not translate product language into components prematurely.

### CLASSIFY
Assign L0-L4. The level limits ceremony.

### EVIDENCE
Load the smallest sufficient evidence. Prefer live code/contracts/tests over stale prose. If an architecture source of truth exists, use it but verify relevant facts against code when drift is plausible.

### CURRENT
State the relevant current boundary, owner, contract, invariant, and dependency facts. Mark inference as inference.

### FIT
Test whether the requirement fits the existing architecture naturally. Prefer Preserve/Extend before Evolve/Introduce/Migrate.

### DECIDE
Choose the smallest viable architecture delta. Offer alternatives only when the trade-off is real.

### PERSIST
Persist only durable architecture facts. Skip this state for transient/local details. Write architecture deltas, not full rewrites.

### PLAN
Translate decisions into implementation constraints. Create parallel units only when independent scopes and stable contracts actually exist.

### IMPLEMENT
Keep work inside declared boundaries. If implementation discovers a hidden architecture constraint, reclassify rather than silently working around it.

### AUDIT
Compare architecture-relevant code changes against accepted constraints. Passing behavior tests is necessary but not sufficient when architecture changed.

### LEARN
Promote repeated findings gradually. One-off fixes stay local; repeated objective violations can become checks.

## Decision policy

Do not ask the user to choose between fake alternatives. Ask only when alternatives materially affect:
- product/domain semantics
- authoritative ownership
- consistency guarantees
- API/data compatibility
- irreversible data semantics
- security/compliance
- migration complexity/risk
- deployment/operational topology or material cost

Otherwise choose the simplest compliant design and state assumptions.

## Architecture-state write-back policy

Write back only durable deltas such as:
- new/changed authoritative owner
- new/changed public contract or compatibility rule
- new/changed invariant
- new/changed allowed/forbidden dependency
- new/changed consistency/persistence boundary
- accepted transition state
- durable decision with rationale/reconsideration trigger

Do not write back:
- task decomposition
- temporary implementation sequence
- file lists
- private helper structure
- incidental framework mechanics
- speculative future options
