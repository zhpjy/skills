# Architecture review checklist

Use selectively; do not turn every review into a full audit.

## Boundary and ownership
- Is each changed mutable business fact authoritative in one place?
- Does another boundary mutate that state directly?
- Did the change create hidden shared state?
- Is responsibility split because of implementation convenience rather than domain/lifecycle pressure?

## Contracts
- Are cross-boundary interactions explicit enough to preserve ownership?
- Does a contract expose internal storage/framework types?
- Are failure/idempotency/ordering semantics explicit when correctness requires them?
- Is the contract stable under internal refactoring?

## Dependencies
- Is dependency direction consistent with intended ownership/control flow?
- Did the change create a cycle?
- Is a new dependency necessary or merely convenient?

## Invariants and consistency
- Which invariant can this change violate?
- Is every new durable invariant owned somewhere?
- Can critical invariants be verified?
- Did consistency weaken without an explicit tradeoff?

## Evolution
- Is an abstraction justified by current/repeated pressure or only an uncertain future?
- Does `uncertain` roadmap material incorrectly drive architecture?
- Is a major choice reversible enough for its uncertainty?

## AI parallelism
- Are work units actually independent?
- Are shared contracts stable before parallel edits?
- Will several agents edit the same unstable core files?
- Does an agent need broad repository context because boundaries are implicit?

## Smells

### Excessive context radius
A local change requires reading many unrelated areas.
Possible causes: hidden global state, implicit boundary, poor naming, missing contract.

### Excessive change radius
A local business change modifies many owners/modules.
Possible causes: scattered responsibility, leaking representation, missing domain concept.

### Cross-boundary transaction
One transaction mutates multiple authoritative owners.
Possible causes: boundary error or need for explicit process/consistency design.

### Unstable contract
Public contract changes with internal refactors.
Possible cause: implementation detail leaking through the boundary.

### Pattern cargo cult
Abstractions exist mainly because a named architecture style was selected.
Action: remove or justify with concrete pressure.
