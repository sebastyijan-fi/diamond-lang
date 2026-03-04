# Release process

Diamond releases are milestone-gated. A release can only proceed after:

- V1 contract gate passes: `scripts/ci/validate_v1_gates.sh`
- Documentation status is up to date: `docs/completeness/STATUS_REPORT.md`
- Decision registry is current: `docs/PROJECT_STRUCTURE.md`

## Release checklist

1. Update [CHANGELOG.md](CHANGELOG.md)
2. Bump version where packaging metadata requires it.
3. Refresh completeness and status docs.
4. Run `make v1-gates`.
5. Produce any reproducible evidence into `certification/`.
6. Tag and publish with milestone notes.
