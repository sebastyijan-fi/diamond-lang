# Phase B3 Full-Port Gap Ledger (`tomli`)

This file tracks what is and is not Diamond-native in the current `tomli` port.

## Current Status

Validated now:

- Upstream baseline: `16/16` tests, `744` subtests.
- Transpiled package parity: `16/16` tests, `744` subtests.
- Differential parity: `0` mismatches across `733` executable corpus cases (`11` non-UTF8 invalid fixtures skipped per upstream policy).

## Module Coverage

| Upstream module | LOC | Current status | Notes |
|---|---:|---|---|
| `src/tomli/_re.py` | 119 | **Diamond-backed** | Implemented via multi-file Diamond modules (`re_tz.dmd`, `re_match.dmd`, `re_number.dmd`) plus adapter. |
| `src/tomli/_parser.py` | 782 | Upstream Python | Largest remaining scope; class-heavy/stateful parse loop and detailed error paths. |
| `src/tomli/__init__.py` | 8 | Upstream Python | Thin public export wrapper. |
| `src/tomli/_types.py` | 10 | Upstream Python | Small typing helper module. |

## What "Full" Means Here

For `tomli`, "full Diamond port" means replacing `_parser.py` logic with Diamond-transpiled modules while preserving:

1. parse behavior on all valid fixtures,
2. error behavior on invalid fixtures (type + message equivalence where practical),
3. public API compatibility (`loads`, `load`, `TOMLDecodeError`), and
4. current parity gates (upstream tests + differential corpus checks).

## Next Execution Steps (If We Push to Full)

1. Split `_parser.py` into parser-focused functional units (scanner, key parsing, value parsing, table assembly, error formatting).
2. Port units incrementally into Diamond modules with adapter wiring.
3. Run full upstream tests and differential checker after each unit lands.
4. Lock only when all parser paths are Diamond-backed and parity remains at zero drift.
