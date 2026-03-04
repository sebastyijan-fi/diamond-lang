# Diamond Project Structure

## Top-level

- `src/` — compiler/transpiler implementation and tests
- `scripts/` — validation scripts and reproducible checks
- `docs/` — language contracts, policies, and references
- `research/` — exploratory material and experimental notes
- `certification/` — evidence artifacts for formal claims and real-repo compatibility
- `tmp/` — ephemeral runtime artifacts; ignored when generated
- `tests/` — public-facing acceptance guidance
- `CONTRIBUTING.md`, `SECURITY.md`, `Makefile` — onboarding and standard contributor entrypoints
- `examples/` — reference programs and syntax probes
- `pyproject.toml` — project metadata and tooling defaults

### Canonical / compatibility split

- Canonical runbooks and automation live in `scripts/` and `docs/`.
- Compatibility entry points are preserved in `certification/real-repos/*` as shim scripts and historical invocation notes.
- Historical and superseded material is preserved under `docs/archive/` and marked as non-normative.

## Documentation tiers

- Normative: `docs/decisions/profile_v1/` and V1 policy files
- Reference: `docs/INDEX.md`, `docs/REFERENCE_MAP.md`
- Current status: `docs/START_HERE.md`, `docs/STATUS.md`, `docs/completeness/STATUS_REPORT.md`
- Archive: `docs/archive/legacy_notes/`

## Validation entry point

- Use `scripts/ci/validate_v1_gates.sh` as the mandatory milestone gate.
