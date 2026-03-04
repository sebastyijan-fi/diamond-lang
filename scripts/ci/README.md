# CI Validation

Primary entrypoint:

```bash
./scripts/ci/validate_v1_gates.sh
```

What it checks:
- Diagnose regression checks (`diagnose_regression_tests.py`)
- Parser regression checks for known ambiguity edges (`parser_regression_tests.py`)
- Semantic/type validation:
  - regression checks (`semantic_validation_tests.py`)
  - static scan across configured Diamond inputs (`semantic_validate.py`)
- Module-system regression checks for D10 B-core parsing/resolution (`module_system_regression_tests.py`)
- Capability composition validation:
  - regression checks (`capability_validation_tests.py`)
  - static scan across configured Diamond inputs (`capability_validate.py`)
  - lanes:
    - `core_strict`: zero-warning policy by default
    - `port_relaxed`: warning-budget policy for active ports
- Stdlib/runtime conformance checks (`src/conformance/run_stdlib_conformance.py`)
- Policy validators:
  - evolution policy + migration regressions
  - interop profile regressions
  - equality/identity/hash contract regressions
  - panic/cleanup policy regressions
  - concurrency policy regressions
  - memory/runtime + ABI/FFI policy regressions
- Build/package determinism:
  - lockfile regressions (`scripts/packaging/diamond_lock_tests.py`)
  - lock generation + validation roundtrip (`diamond_lock.py`, `validate_diamond_lock.py`)
- Portfolio14-v4 behavior equivalence (`run_behavior_tests.py --batch all_portfolio14_v4`)
- Construct-tool measurement on `fn_error_portfolio14_v4_math_patch`
- Final gate thresholds from `docs/decisions/profile_v1/CONSTRUCT_TOOL_STYLE_GUIDE.md`:
  - portfolio `net_reduction >= 35%`
  - portfolio `vs_python_with_tools >= 60%`
  - portfolio `tool_overhead <= 15%`
  - per-program `net_reduction >= 5%`
  - per-program `tool_overhead <= 20%`

Useful options:
- `--tokenizer-json PATH` to force tokenizer location
- `--skip-behavior` to run metric gates only

Environment overrides:
- `STDLIB_CONFORMANCE_RUNTIME`, `STDLIB_CONFORMANCE_CASES`
- `CAP_VALIDATION_STRICT_INPUTS`, `CAP_VALIDATION_RELAXED_INPUTS`
- `CAP_VALIDATION_STRICT_MAX_WARNINGS`, `CAP_VALIDATION_RELAXED_MAX_WARNINGS`
- `SEM_VALIDATION_INPUTS`, `SEM_VALIDATION_MAX_WARNINGS`
- `LOCK_INPUTS` comma-separated `.dmd` paths/dirs for lock generation (default `docs/decisions/profile_v1/programs`)
- `LOCK_FILE` lockfile output path for CI roundtrip (default `/tmp/diamond.lock.json`)
- Defaults: strict `0`, relaxed `0`
- Default relaxed/semantic lanes include active ports: `retry`, `iniconfig`, `tomli`.
- legacy override: `CAP_VALIDATION_INPUTS` (maps to strict lane)
- `TOKENIZER_JSON`, `RUN_ID`, `CSV_OUT`, `APPEND_JSONL`
- `BEHAVIOR_OUT_DIR`
- `PORTFOLIO_NET_MIN`, `PORTFOLIO_VS_TOOLS_MIN`, `PORTFOLIO_TOOL_OVERHEAD_MAX`
- `PROGRAM_NET_MIN`, `PROGRAM_TOOL_OVERHEAD_MAX`
