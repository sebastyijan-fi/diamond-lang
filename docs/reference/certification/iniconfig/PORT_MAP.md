# Port Map: `pytest-dev/iniconfig` -> Diamond

## Scope for initial pass

Target parity for first executable pass:

- `iniconfig._parse.parse_ini_data`
- `iniconfig._parse.parse_lines`
- `iniconfig.__init__.IniConfig` and `SectionWrapper`
- `iniconfig.exceptions.ParseError`

## Why this is Phase B2

This project stresses a different shape than `retry`:

- heavy string scanning
- state assembly into nested mappings
- section/key lookups and duplicate detection
- deterministic parse errors with line/column context

It also validates multi-file port flow:

- `exceptions` <- `_parse` <- `__init__`

## Behavioral checkpoints

From upstream tests (`testing/test_iniconfig.py`):

1. Tokenization of sections/keys/values and continuations
2. Comment handling (`#` and `;`) in multiple positions
3. Duplicate section/key detection and error paths
4. Source line tracking (`lineof`)
5. Stable iteration order and lookup behavior
6. Optional inline-comment stripping behavior

## Anticipated semantic gaps

1. Newline-sensitive continuation parsing
2. Precise parse error formatting (`path:line: message`)
3. Dict ordering and section iteration parity
4. Optional strip flags (`strip_inline_comments`, `strip_section_whitespace`)

## Planned conversion staging

1. Start with `_parse.py` core scanner/parser behavior
2. Port error type + parse error context assembly
3. Port `IniConfig` wrappers/access helpers
4. Build adapter package for upstream test import paths
5. Run full upstream test suite against transpiled output

## Current execution status

- Stage 1 complete for parity execution:
  - Diamond entry module `diamond/parse_dm.dmd` transpiles and is exercised by upstream tests.
  - API adapter keeps upstream import/typing surface stable.
  - Current parity result: `49/49` upstream tests passing.
- Stage 2 complete for parse-data flow:
  - `parse_ini_data` reduction and duplicate checks are now represented in Diamond expressions
    (fold/state pipeline), not a single runtime monolith call.
- Next refinement target:
  - Move `parse_lines` continuation assembly from runtime helper implementations into direct Diamond expressions where practical.
