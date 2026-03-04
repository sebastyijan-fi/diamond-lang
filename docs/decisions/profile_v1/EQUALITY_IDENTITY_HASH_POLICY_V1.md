# Diamond Equality/Identity/Hash Policy V1

This policy fixes the object comparison contract for Diamond V1 and prevents backend drift.

## Contract

1. Equality (`==`)
- Structural deep equality for values and objects.
- Must be cycle-safe for object graphs.

1. Identity (`is`)
- Reference identity only.
- Alias references compare `true`; distinct objects compare `false` regardless of structural equality.

1. Hashing
- Objects are unhashable in V1.
- Stable scalar hashing is delegated to backend host runtime.

## Machine-readable source of truth

- `docs/decisions/profile_v1/equality_identity_hash_v1.json`

## Enforcement

Validator:

- `scripts/equality/validate_equality_contract.py`

Regression tests:

- `scripts/equality/validate_equality_contract_tests.py`

Required conformance cases (runtime):

- `obj.alias.identity_true`
- `obj.alias.mutation_visible`
- `obj.eq.structural_true`
- `obj.eq.structural_false`
- `obj.eq.cycle_true`
- `obj.eq.cycle_false`

CI gate:

- `scripts/ci/validate_v1_gates.sh`
