# Diamond Match Exhaustiveness Policy V1

This policy defines how Diamond match expressions are required to behave in V1.

## Contract

1. Match expressions are syntax-supported only when they are statically verifiable as catch-all safe.
1. Every match expression must include at least one fallback arm.
   - A fallback may be `_` (wildcard), or
   - a capture pattern `IDENT`.
1. Matches that use only literal patterns are rejected without a fallback arm.
1. Duplicate literal arms are rejected.

## Machine-readable source of truth

- `docs/decisions/profile_v1/match_exhaustiveness_profile_v1.json`

## Enforcement

- `src/transpiler/semantic_validate.py` (`_validate_match_arms`)
- `src/transpiler/semantic_validation_tests.py`
- `scripts/ci/validate_v1_gates.sh` (via semantic validation)

## Deterministic diagnostics

- `match expression must include a wildcard or capture arm for exhaustiveness`
- `duplicate match literal pattern '...')`
- `match expression must include at least one arm`
