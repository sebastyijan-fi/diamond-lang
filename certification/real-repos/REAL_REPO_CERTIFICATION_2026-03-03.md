# Real Repo Certification (Pre-Rust)

Run timestamps (UTC):

- Initial certification: `2026-03-03T20:11:45Z`
- Expanded difficult multi-file rerun (`tomli`): `2026-03-03T22:22:00Z`
- Differential all-case parity (`tomli`): `2026-03-03T23:05:00Z`

Purpose: confirm Diamond v1 transpiler quality on legit upstream repos before starting Rust backend work.

## Scope

Repos ported and pinned in Phase B:

1. `invl/retry` (Apache-2.0)
2. `pytest-dev/iniconfig` (MIT)
3. `hukkin/tomli` (MIT)

Checks executed:

1. Upstream baseline tests on frozen snapshot
2. Transpiled-package parity tests (upstream tests against transpiled output)
3. Static semantic validation on Diamond sources
4. Static capability validation on Diamond sources
5. Differential case-by-case parity on `tomli` corpus

## Commands Run

```bash
. .venv/bin/activate
./scripts/certification/common/run_pre_rust_certification.sh
./scripts/certification/retry/run_upstream_tests.sh
./scripts/certification/iniconfig/run_upstream_tests.sh
./scripts/certification/tomli/run_upstream_tests.sh
./scripts/certification/retry/build_and_test_transpiled.sh
./scripts/certification/iniconfig/build_and_test_transpiled.sh
./scripts/certification/tomli/build_and_test_transpiled.sh
./scripts/certification/tomli/run_differential_cases.sh
python src/transpiler/semantic_validate.py \
  --in certification/real-repos/retry/diamond \
  --in certification/real-repos/iniconfig/diamond \
  --in certification/real-repos/tomli/diamond \
  --max-warnings 0
python src/transpiler/capability_validate.py \
  --in certification/real-repos/retry/diamond \
  --in certification/real-repos/iniconfig/diamond \
  --in certification/real-repos/tomli/diamond \
  --max-warnings 0
```

## Results

| Project | Upstream Baseline | Transpiled Parity | Semantic Validate | Capability Validate |
|---|---:|---:|---:|---:|
| retry | 9/9 pass | 9/9 pass (`retry_call` subset 4/4) | pass (0 errors, 0 warnings) | pass (0 errors, 0 warnings) |
| iniconfig | 49/49 pass | 49/49 pass | pass (0 errors, 0 warnings) | pass (0 errors, 0 warnings) |
| tomli | 16/16 pass (+744 subtests) | 16/16 pass (+744 subtests) | pass (0 errors, 0 warnings) | pass (0 errors, 0 warnings) |

Aggregate parity:

- Baseline total: `74/74` pass (+744 subtests on `tomli`)
- Transpiled total: `74/74` pass (+744 subtests on `tomli`)
- Delta: `0` failing tests introduced by transpilation
- `tomli` differential corpus parity: `0` mismatches over `733` executable cases (`11` non-UTF8 invalid fixtures skipped)

## Gate Verdict

Pre-Rust real-repo gate: **PASS**.

Recommendation: proceed to Rust backend implementation, while keeping this certification as a recurring gate after backend changes.
