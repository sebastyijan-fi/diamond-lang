# Diamond Interop Policy V1

This policy defines the enforced interoperability contract for Diamond V1.

## Scope

V1 interop is constrained to deterministic and testable surfaces:

1. C ABI interop through generated host code plus `extern` builtin lowering.
1. Embedding through Python runtime surface.
1. WASM-target alignment through JS backend/runtime compatibility contract.
1. Cross-language data interchange through canonical JSON builtins (`jenc`/`jdec`).

## Source of truth

Machine-readable contract:

- `docs/decisions/profile_v1/interop_profile_v1.json`

## Enforcement

Validator:

- `scripts/interop/validate_interop_profile.py`

Regression suite:

- `scripts/interop/validate_interop_profile_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`

## Invariants

1. `extern` lowering contract is present and wired to runtime symbol `extern_call`.
1. Python runtime exposes `extern_call`, `call_with`, `json_dumps`, `json_loads`.
1. JS and Rust runtime surfaces expose `json_dumps` and `json_loads`.
1. Python, JS, and Rust backends map `jenc` and `jdec`.
1. Semantic validator declares `jenc` and `jdec` builtin signatures.

This keeps interop behavior measurable and prevents silent backend drift.
