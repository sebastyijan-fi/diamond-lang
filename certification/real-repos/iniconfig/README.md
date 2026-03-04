# Phase B Candidate: `pytest-dev/iniconfig`

Status: selected, baselined, and first transpiled parity run complete.

## Why this project

`iniconfig` is a strong second port target because it is small, parser-heavy, and split across multiple source files:

- String/state-heavy parsing logic (`_parse.py`)
- Structured state objects and section/key lookups (`__init__.py`)
- Focused error type (`exceptions.py`)
- Existing upstream pytest suite

This complements the first Phase B port (`retry`), which was loop/error/backoff-heavy.

## Hard-criteria check

- License: MIT (`upstream/iniconfig/LICENSE`)
- Existing tests: yes (`testing/test_iniconfig.py`)
- Multi-file core: yes (3 source files under `src/iniconfig/`)
- Core size: 428 LOC
  - `src/iniconfig/__init__.py`: 249
  - `src/iniconfig/_parse.py`: 163
  - `src/iniconfig/exceptions.py`: 16
- Test size: 415 LOC
  - `testing/test_iniconfig.py`: 414
  - `testing/conftest.py`: 1

## Frozen snapshot

- Upstream commit: `77db208ab4ae0cd2061d909fe222a1db72867850`
- Snapshot path: `certification/real-repos/iniconfig/upstream/iniconfig/`

## Baseline validation

Run from repo root:

```bash
. .venv/bin/activate
PYTHONPATH=certification/real-repos/iniconfig/upstream/iniconfig/src \
  python -m pytest -q certification/real-repos/iniconfig/upstream/iniconfig/testing/test_iniconfig.py
```

Current result: `49 passed`.

Compatibility note:

Canonical commands for this repo are in `scripts/certification/iniconfig/*`.
Commands listed here are preserved as compatibility entry points.

## Transpiled parity validation

Run from repo root:

```bash
./scripts/certification/iniconfig/build_and_test_transpiled.sh
```

Current result: `49 passed`.

Current transpiled scope:

- Diamond module: `diamond/parse_dm.dm`
- `parse_ini_data` control flow is now emitted from Diamond (`fd`/fold over token rows).
- Runtime-backed parse primitives still used for:
  - line splitting (`splitln`)
  - line tokenization (`ini_parseline`, `ini_parse_lines`)
  - INI-specific helpers (`ini_raise`, `pair`, `q`)
- Adapter package preserving upstream API surface (`iniconfig/_parse.py`, `__init__.py`, `exceptions.py`)

## Deliverables in this phase folder

- Frozen upstream snapshot: `upstream/iniconfig/`
- Baseline runner: `run_upstream_tests.sh`
- Port mapping scaffold: `PORT_MAP.md`
- Transpiled parity runner: `build_and_test_transpiled.sh`
- Diamond workspace for this port: `diamond/`
