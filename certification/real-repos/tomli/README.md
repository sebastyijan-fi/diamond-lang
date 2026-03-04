# Phase B3 Candidate: `hukkin/tomli`

Status: complete for current Phase B3 scope (fresh GitHub clone + multi-file Diamond parity run passing).

## Why this project

`tomli` is parser-heavy and meaningfully harder than prior ports:

- core parser module is large (`_parser.py`, ~780 LOC),
- secondary parsing utilities (`_re.py`) include datetime/number conversion logic,
- broad test corpus (`16 tests`, `744 subtests` in current snapshot).

This is used as a stress test for multi-file Diamond integration against real upstream tests.

Full-port status tracker:

- `docs/reference/certification/tomli/FULL_PORT_GAP.md`

## Frozen snapshot

- Upstream commit: `c20c491`
- Snapshot path: `certification/real-repos/tomli/upstream/tomli/`

## Baseline run

```bash
. .venv/bin/activate
./scripts/certification/tomli/run_upstream_tests.sh
```

Current baseline result:

- `16 passed, 744 subtests passed`

## Port scope (current attempt)

Multi-file Diamond conversion target:

- `_re.py` conversion helpers split across multiple `.dm` files:
  - timezone offset construction,
  - datetime/time conversion from regex groups,
  - number conversion.

Package parity strategy:

- keep upstream `_parser.py` unchanged,
- replace `_re.py` behavior through transpiled Diamond modules + adapter layer,
- run full upstream tests against the transpiled package.

## Commands

Baseline:

```bash
./scripts/certification/tomli/run_upstream_tests.sh
```

Transpiled parity:

```bash
./scripts/certification/tomli/build_and_test_transpiled.sh
```

Current transpiled parity result:

- `16 passed, 744 subtests passed`

Differential all-case parity:

```bash
./scripts/certification/tomli/run_differential_cases.sh
```

Compatibility note:

These commands are canonicalized through `scripts/certification/tomli/*`; the
`certification/real-repos/tomli/*` paths are wrappers for existing workflows.

Current differential result:

- `0 mismatches` across `733` executable cases
- `11` non-UTF8 invalid fixtures skipped (same policy as upstream tests)
