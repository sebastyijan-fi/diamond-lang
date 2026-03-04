# Diamond V1 Capability Model

Status: normative for V1 profile behavior.

## 1. Capability declaration surface

- Capabilities are declared in tool headers with identifier-safe tokens.
- Control tools (`c`, `t`, `b`, `e`) are not capabilities.
- V1 canonical capability names use snake_case identifiers (for example `time_sleep`, `rng_uniform`, `net`, `db`).

## 2. Static composition

- Required capabilities are computed as the transitive union of:
  - direct builtin requirements,
  - required capabilities of called local functions and methods.
- Method self-calls (`#.m()`) are included in the call graph as `Class__m`.
- If a declaration contains explicit capabilities, they are a restriction ceiling and must include all computed requirements.

## 3. Runtime authority policy

- Runtime supports:
  - `allow_all` mode,
  - `allow_list` mode with explicit granted capabilities.
- In `allow_list`, missing required capabilities are runtime errors.

## 4. Gate policy

- Capability validation is a release gate in CI.
- Core lane enforces strict warning/error budget.

## 5. Conformance anchors

- `src/transpiler/capability_validate.py`
- `src/transpiler/capability_validation_tests.py`
- `src/transpiler/runtime/diamond_runtime.py`
- `src/conformance/cases/runtime_v0_core.json`
- `src/conformance/run_stdlib_conformance.py`
