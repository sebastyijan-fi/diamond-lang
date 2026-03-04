# Diamond Panic/Cleanup Policy V1

This policy defines panic/abort and cleanup guarantees for Diamond V1.

## Contract

1. Panic/error transport uses one exception channel.
1. Cleanup/recovery is expressed through `try(body, e: handler)`.
1. `reraise` maps to a deterministic rethrow sentinel (`RERAISE`) in runtime.
1. `propagate` preserves exception identity and rethrows after trace logging.

## Machine-readable source of truth

- `docs/decisions/profile_v1/panic_cleanup_profile_v1.json`

## Enforcement

Validator:

- `scripts/panic/validate_panic_cleanup_policy.py`

Regression tests:

- `scripts/panic/validate_panic_cleanup_policy_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`

## Runtime conformance anchors

Required runtime cases:

1. `try_catch.handle`
1. `try_catch.reraise`
1. `try_catch.over.propagate`
1. `propagate.error`
