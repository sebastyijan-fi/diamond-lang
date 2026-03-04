# Corpus Scaffold

This folder is the canonical benchmark workspace for Diamond syntax search.

## Layout

- `reference_python/`: 20 reference programs in Python (baseline source of truth)
- `candidates/`: candidate Diamond syntax renderings grouped by candidate id (`A`, `B`, `C`, ...)
- `tests/`: optional equivalence tests for reference and transpiled outputs

## Workflow

1. Implement/complete each Python reference in `reference_python/`.
2. For a design question, create candidate folders under `candidates/`.
3. Translate a subset (or all) reference programs into each candidate syntax.
4. Run tokenbench against each candidate set with the Qwen tokenizer.
5. Append structured JSONL records to `../measurements/decision_log.jsonl`.

## Suggested Candidate Layout

- `candidates/A/`
- `candidates/B/`
- `candidates/C/`

Each candidate folder should contain files matching the reference program slugs, e.g.:

- `candidates/A/01_fizzbuzz.dm`
- `candidates/A/06_http_handler_routing.dm`

## Program Index

See `program_index.csv` for IDs and slugs.
