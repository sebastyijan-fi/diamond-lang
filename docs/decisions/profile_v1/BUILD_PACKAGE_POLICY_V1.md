# Diamond Build/Package Policy V1

This policy defines deterministic source-set locking for Diamond compilation inputs.

## Contract

1. A lockfile captures exact `.dmd` module set with path, checksum, and byte size.
1. Module ordering in lockfile is deterministic (sorted by normalized path).
1. Lock digest is deterministic over ordered module metadata.
1. Validation fails if source content or module set changes without lock regeneration.

## Machine-readable lock format

- `diamond.lock.json`

Required keys:

1. `language` = `diamond`
1. `lock_version` = `1`
1. `module_count`
1. `source_digest`
1. `modules` (array of `{path, sha256, bytes}`)

## Tooling

Generator:

- `scripts/packaging/diamond_lock.py`

Validator:

- `scripts/packaging/validate_diamond_lock.py`

Regression tests:

- `scripts/packaging/diamond_lock_tests.py`

CI gate:

- `scripts/ci/validate_v1_gates.sh`
