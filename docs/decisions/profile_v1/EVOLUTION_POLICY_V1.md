# Diamond Evolution Policy V1

This document defines how Diamond V1 evolves without silent semantic drift.

## Version pin

- Canonical language profile is `v1`.
- V1 is stable and locked to deterministic transpilation semantics.
- Any syntax not in canonical V1 is either rejected or must be transformed by explicit migration tooling.

## Deprecation registry

The machine-readable source of truth is:

- `docs/decisions/profile_v1/evolution_policy_v1.json`

Deprecated syntax in V1:

1. `§` class sigil
- Status: error in V1
- Canonical replacement: `$`
- Autofix support: yes

1. Explicit receiver parameter in method signatures (`self:...`)
- Status: error in V1
- Canonical replacement: implicit receiver with `#` binder
- Autofix support: yes

## Migration tooling

- Tool: `scripts/evolution/migrate_to_v1.py`
- Behavior:
1. rewrites `§` to `$` outside comments and strings
1. removes leading `self:...` receiver parameter in method declarations
1. idempotent on canonical sources

Usage:

```bash
.venv/bin/python scripts/evolution/migrate_to_v1.py --in path/to/sources --write
```

Dry-run (no file writes):

```bash
.venv/bin/python scripts/evolution/migrate_to_v1.py --in path/to/sources
```

## Enforcement in CI

`scripts/ci/validate_v1_gates.sh` validates:

1. policy schema and invariants (`validate_evolution_policy.py`)
1. migration-tool regressions (`migrate_to_v1_tests.py`)
1. policy-validator regressions (`validate_evolution_policy_tests.py`)

This makes versioning, deprecation, and migration a checked contract rather than documentation-only guidance.
