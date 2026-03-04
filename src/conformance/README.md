# Stdlib Conformance

Purpose: lock runtime helper semantics behind deterministic fixtures so backend implementations cannot drift.

Primary runner:

```bash
. .venv/bin/activate
python src/conformance/run_stdlib_conformance.py
```

By default this runs all case files in:

- `src/conformance/cases/*.json`

against runtime:

- `src/transpiler/runtime/diamond_runtime.py`

## Case format

Each case file is a JSON object with `cases` list:

```json
{
  "suite": "diamond_runtime_v0_core",
  "cases": [
    {
      "id": "idiv.basic",
      "fn": "idiv",
      "args": [7, 2],
      "expect": 3
    }
  ]
}
```

Supported fields per case:

- `id`: stable identifier
- `fn`: runtime function name
- `args`: positional args (optional; defaults `[]`)
- `kwargs`: keyword args (optional; defaults `{}`)
- `expect`: expected value
- `expect_error`: expected error object:
  - `type`: exception class name
  - `contains`: required substring in error message
- `assert_args_unchanged`: list of positional arg indexes to verify immutability

Fixture value encodings:

- `{"$fn": "name"}` -> function fixture
- `{"$tuple": [1,2]}` -> tuple
- `{"$obj": {"attrs": {"x": 1}}}` -> object with attributes

## Notes

- Results print as CSV-like rows (`file,case,result`) plus summary.
- Exit code is non-zero if any case fails.
- Current suite includes core helpers plus INI parsing helpers used in Phase B2.
