# Diamond Module Dependency Policy V1

This policy defines cycle handling and initialization ordering for Diamond inline module blocks (`@name{...}`).

## Scope

Applies to real module blocks inside one `.dmd` compilation unit.

External contract-only blocks declared via `//@x exposes ...` are excluded from ordering and are emitted as external stubs after real blocks.

## Dependency graph

For each block `@b`, dependencies are inferred from qualified cross-block references inside function bodies:

- `a.f(...)` inside block `b` creates dependency `b -> a`
- intra-block references do not create graph edges

## Cycle policy

Cycles among real blocks are rejected at compile time.

Error shape:

- `module.dmd: module block cycle detected: @a -> @b -> @a`

## Deterministic initialization order

Real blocks are emitted in topological order (dependencies first).

Tie-break rule for independent blocks:

- preserve original source order

This guarantees deterministic lowering while maintaining source-order stability when no dependency requires reordering.

## Enforcement

Implementation:

- `src/transpiler/parse_to_ir.py`

Regression tests:

- `src/transpiler/module_system_regression_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`
