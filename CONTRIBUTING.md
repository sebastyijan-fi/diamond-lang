# Contributing

Diamond is a language-research project moving toward production language tooling. Contributions should be oriented to the V1 gate contract and maintain deterministic behavior.

## Before you start

- Read the current scope in [docs/completeness/STATUS_REPORT.md](docs/completeness/STATUS_REPORT.md).
- Keep edits aligned to V1 contracts in [docs/decisions/profile_v1](docs/decisions/profile_v1/).

## Workflow

1. Implement behind a small, reviewable diff.
2. Update relevant contract or workbook docs when behavior changes.
3. Run the V1 gate before proposing milestone-ready changes:

```bash
make v1-gates
```

## PR expectations

- No behavior changes without test updates in relevant suites under `src/`.
- No new legacy syntax unless explicitly marked out-of-profile.
- Keep names, scripts, and docs discoverable and minimally noisy.
- Add or update docs for each non-trivial architectural decision.

## Validation policy

- `make v1-gates` is the milestone default.
- Add focused evidence in `certification/` only for externally facing claims.
