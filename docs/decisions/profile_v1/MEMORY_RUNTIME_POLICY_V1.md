# Diamond Memory/Runtime/ABI Policy V1

This policy defines memory model, safety boundary, and FFI/ABI lifecycle guarantees for Diamond V1.

## Contract

1. Memory strategy:
- Python/JS semantics rely on host GC.
- Rust compatibility runtime uses `Rc<RefCell<T>>` parity mode.
- Manual memory management is out-of-profile in V1.
- Deterministic language-level destructors are out-of-profile in V1.

1. Safety boundary:
- Diamond surface has no `unsafe` feature.
- Rust runtime unsafe blocks are disallowed in V1 policy gate.
- Audit model is static policy validation in CI.

1. FFI/ABI lifecycle:
- C ABI interop path is host-extern bridge via `extern` lowering.
- Runtime symbol is `extern_call`.
- Default behavior is deterministic `NotImplementedError` / panic fallback unless host bridge is configured.

## Machine-readable source of truth

- `docs/decisions/profile_v1/memory_runtime_profile_v1.json`

## Enforcement

Validator:

- `scripts/memory/validate_memory_runtime_policy.py`

Regression tests:

- `scripts/memory/validate_memory_runtime_policy_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`
