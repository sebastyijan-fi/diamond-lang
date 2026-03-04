# Port Map: `tomli` (Phase B3)

Goal: validate a difficult multi-file real-repo port path.

## Upstream modules

- `src/tomli/__init__.py`
- `src/tomli/_parser.py`
- `src/tomli/_re.py`
- `src/tomli/_types.py`

## Diamond conversion scope (this phase)

Converted to Diamond (multi-file):

- `_re.py` conversion logic
  - `match_to_datetime`
  - `match_to_localtime`
  - `match_to_number`
  - timezone-offset helper

Kept upstream Python:

- `__init__.py`
- `_parser.py`
- `_types.py`

Rationale:

- exercises multi-file Diamond integration in parser-critical path,
- avoids boiling the ocean by not rewriting `_parser.py` (~780 LOC) in one step,
- still validates that transpiled Diamond logic can substitute a core dependency module.
