# Phase B2 Results (`iniconfig`)

## Snapshot

- Repo: `pytest-dev/iniconfig`
- Frozen commit: `77db208ab4ae0cd2061d909fe222a1db72867850`
- License: MIT

## Test outcomes

- Upstream baseline (frozen source): `49/49` passing
  - Command: `./scripts/certification/iniconfig/run_upstream_tests.sh`
- Upstream parity against transpiled Diamond package: `49/49` passing
  - Command: `./scripts/certification/iniconfig/build_and_test_transpiled.sh`

## Conversion status

- Diamond source currently in play:
  - `diamond/parse_dm.dmd`
- Direct Diamond control flow now covers:
  - `parse_ini_data` token reduction/state update path
  - duplicate-section and duplicate-name checks
  - source-line mapping assembly
- Runtime primitives still cover:
  - low-level line tokenization (`ini_parseline`, `ini_parse_lines`)
  - helper utilities (`ini_raise`, `ini_pair`, `ini_repr`, `ini_splitlines_keepends`)

## Repo-wide safety check after Phase B2 updates

- `./scripts/ci/validate_v1_gates.sh` passed end-to-end:
  - diagnose regressions: pass
  - parser regressions: pass
  - portfolio behavior tests: `61/61` pass
  - construct-tool gates: pass
