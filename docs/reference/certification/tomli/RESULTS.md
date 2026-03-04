# Phase B3 Results: `hukkin/tomli`

Run date: `2026-03-03` (UTC)

## Baseline

Command:

```bash
. .venv/bin/activate
./scripts/certification/tomli/run_upstream_tests.sh
```

Result:

- `16 passed, 744 subtests passed`

## Transpiled Parity

Command:

```bash
. .venv/bin/activate
./scripts/certification/tomli/build_and_test_transpiled.sh
```

Result:

- `16 passed, 744 subtests passed`

## Static Validation on Diamond Sources

Commands:

```bash
python src/transpiler/semantic_validate.py --in certification/real-repos/tomli/diamond --max-warnings 0
python src/transpiler/capability_validate.py --in certification/real-repos/tomli/diamond --max-warnings 0
```

Results:

- Semantic: `modules=3 functions=5 warnings=0 errors=0`
- Capability: `modules=3 functions=5 warnings=0 errors=0`

## Differential Case Parity

Command:

```bash
. .venv/bin/activate
./scripts/certification/tomli/run_differential_cases.sh
```

Result summary:

- total corpus: `744` TOML cases
- executed: `733`
- valid parity: `228/228`
- invalid parity: `505/505` (`TOMLDecodeError` in both, exact message match)
- skipped non-UTF8 fixtures: `11` (matches upstream test policy)
- mismatches: `0`

## Scope Note

This phase ports the `_re` conversion path via multi-file Diamond modules and keeps upstream `_parser.py` in place.
The test pass demonstrates compatibility of transpiled Diamond logic in a parser-critical dependency path.
