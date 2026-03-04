# Phase B Candidate: `invl/retry`

Status: selected, baselined, and first transpiled parity run complete.

## Why this project

`retry` is a strong first real-project port because it is small, test-backed, and matches constructs already proven in Diamond:

- Retry loop with arithmetic backoff (`delay *= backoff`)
- Exception handling and re-raise
- Conditional logic (`max_delay`, jitter modes)
- Higher-order behavior (`retry` decorator + `retry_call`)

## Hard-criteria check

- License: Apache-2.0 (from installed package metadata and project homepage)
- Existing tests: yes (`retry/tests/test_retry.py`)
- Size: under 500 lines total Python in this snapshot
  - `retry/api.py`: 101 lines
  - `retry/compat.py`: 18 lines
  - `retry/__init__.py`: 18 lines
  - `retry/tests/test_retry.py`: 185 lines
  - Total: 322 lines

## Snapshot source

Frozen upstream snapshot for reproducible Phase B work:

- `certification/real-repos/retry/upstream/retry/`

This snapshot was copied from the local environment package install to avoid network instability during the porting run.

## Baseline validation

Run from repo root:

```bash
. .venv/bin/activate
PYTHONPATH=certification/real-repos/retry/upstream python -m pytest -q certification/real-repos/retry/upstream/retry/tests/test_retry.py
```

Current result: `9 passed`.

## Transpiled parity validation

Canonical command for this repo is now:
`./scripts/certification/retry/build_and_test_transpiled.sh` (compatibility wrapper remains at `./certification/real-repos/retry/build_and_test_transpiled.sh`).

Run from repo root:

```bash
./scripts/certification/retry/build_and_test_transpiled.sh
```

Current result:

- `retry_call` subset (`-k retry_call`): `4 passed`
- Full upstream suite: `9 passed`

## Deliverables in this phase folder

- Diamond source: `diamond/api_dm.dm`
- Build + test harness: `build_and_test_transpiled.sh`
- Frozen upstream snapshot: `upstream/retry/`
- Generated parity package (latest run): `out/pkg/`

Detailed construct mapping is tracked in `PORT_MAP.md`.
