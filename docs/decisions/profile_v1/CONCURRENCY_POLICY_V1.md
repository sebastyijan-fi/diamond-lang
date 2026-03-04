# Diamond Concurrency Policy V1

This policy defines concurrency scope for Diamond V1.

## Contract

1. V1 semantic domain is single-thread only.
1. Async/coroutine/generator runtime model is out-of-profile in V1.
1. Synchronization primitives (`mutex`, `atomic`, channels, task groups) are out-of-profile in V1.
1. Memory ordering modes are out-of-profile in V1.
1. Structured cancellation is out-of-profile in V1.

## Machine-readable source of truth

- `docs/decisions/profile_v1/concurrency_profile_v1.json`

## Enforcement

Validator:

- `scripts/concurrency/validate_concurrency_policy.py`

Regression tests:

- `scripts/concurrency/validate_concurrency_policy_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`

## Deterministic rule

If out-of-profile concurrency tokens appear in Diamond source, validation fails with deterministic diagnostics including file and line number.
