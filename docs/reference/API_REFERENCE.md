# Diamond Reference

## Command surface

- `scripts/ci/validate_v1_gates.sh`
  - Canonical milestone gate for V1 conformance and safety contracts.
- `make v1-gates`
  - Runs the same gate through a convenience wrapper.
- `make format`
  - Runs local formatting helper script.
- `make lint`
  - Runs a check-only pass of the formatting helper.

## Core directories

- `src/transpiler/`: compiler, parser, and semantic tooling.
- `docs/decisions/profile_v1/`: normative policy documents.
- `docs/completeness/`: workbook and status evidence.
- `research/`: corpus and benchmark exploration.
- `certification/`: externally checkable evidence artifacts.
