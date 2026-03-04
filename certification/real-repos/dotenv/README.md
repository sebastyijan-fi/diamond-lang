# Phase B4 Candidate: `theskumar/python-dotenv`

Status: baselined from fresh GitHub snapshot; direct Diamond port not started yet.

## Why this project

`python-dotenv` is a difficult multi-file candidate that stresses post-v1 gaps:

- class/decorator-heavy API surface,
- parser/string/state logic across modules,
- generator usage and exception-heavy flows,
- real CLI integration path.

This is intentionally harder than prior Phase B projects and is used to drive core language evolution (not adapter-only growth).

## Snapshot

- Upstream commit: `da0c820`
- Snapshot path: `certification/real-repos/dotenv/upstream/python-dotenv/`
- License: BSD-3-Clause

## Baseline runs

Canonical command for this repo is now:
`./scripts/certification/dotenv/run_upstream_tests.sh` (and `./scripts/certification/dotenv/run_upstream_tests_nocli.sh`).
Legacy commands in `certification/real-repos/dotenv/*` are compatibility wrappers.

Full suite (current probe-mode env):

```bash
./scripts/certification/dotenv/run_upstream_tests.sh
```

Current result:
- `12 failed, 205 passed, 1 skipped`
- known cause: CLI tests expect installed `dotenv` console entrypoint.

Functional baseline excluding CLI entrypoint tests:

```bash
./scripts/certification/dotenv/run_upstream_tests_nocli.sh
```

Current result:
- `176 passed, 1 skipped, 41 deselected`

## Next port scope (planned)

1. Start with parser-centric modules (`parser.py`, `variables.py`) under B-core/C-context module flow.
2. Keep CLI/package-entrypoint tests as separate boundary track.
3. Promote only language-core changes that pass `LANGUAGE_CHANGE_GATE.md`.

## References

- Probe report: `src/probing/reports/run_20260303T210236Z_probe_dotenv_probe.json`
- Core gap backlog: `docs/decisions/profile_v1/CORE_GAP_BACKLOG.md`
