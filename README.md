# Diamond Language

Diamond is an experimental, machine-oriented language for dense LLM-to-code workflows with deterministic transpilation targets.

Current focus is V1 specification maturity: a strict contract, complete feature workbook, and gated validation pipeline.

## Release quality

- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Release process: [RELEASE.md](RELEASE.md)
- CI gate workflow: [.github/workflows/v1-gates.yml](.github/workflows/v1-gates.yml)

## What this repo contains

- A compiler/transpiler stack in `src/`
- Validation tooling in `scripts/`
- Design contracts and evidence in `docs/`
- Research and historical experiment notes in `research/`
- Example programs in `examples/`
- Certification evidence in `certification/`

## Quick start

From a clean checkout:

1. Create/activate your environment.
2. Validate the V1 contract:

```bash
make v1-gates
```

3. Inspect current status:

```bash
cat docs/completeness/STATUS_REPORT.md
```

4. Show release handoff checklist:

```bash
make release
```

## Core docs

- [Start here](docs/START_HERE.md)
- [Project status](docs/STATUS.md)
- [Completeness report](docs/completeness/STATUS_REPORT.md)
- [V1 semantic contracts](docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md)
- [Object semantics](docs/decisions/profile_v1/OBJECT_SEMANTICS_V1.md)
- [Safety policy](docs/decisions/profile_v1/SAFETY_POLICY_V1.md)
- [Capability model](docs/decisions/profile_v1/CAPABILITY_MODEL_V1.md)
- [Reference map](docs/reference/API_REFERENCE.md)
- [Examples index](examples/README.md)
- [Publishability checklist](docs/PUBLISHABILITY_CHECKLIST.md)

## Validation

Milestones are defined through the official V1 gate:

```bash
scripts/ci/validate_v1_gates.sh
```

## Repository map

- `src/` implementation, parsers, and semantic checks
- `scripts/` validation and project automation
- `docs/` language design and policy artifacts
- `research/` explorations and experimental baselines
- `certification/` reproducible evidence artifacts
- `tmp/` ephemeral local workspace files (non-source)
- `docs/archive/` historical notes and superseded materials
- `examples/` baseline programs and syntax probes
- `tests/` regression boundaries and acceptance test guidance

## Repository intent

- `src/` implements parser + IR + backend emitters.
- `scripts/` enforces deterministic quality gates and reproducible certification runs.
- `docs/` holds normative language contracts and design decisions.
- `research/` stores benchmark evidence and language optimization work.
- `certification/` stores externally checkable real-repo compatibility evidence.
- `docs/archive/` and deprecated files contain historical artifacts and are not normative.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, code review expectations, and quality gates.

## License

This repository is distributed under the [LICENSE](LICENSE) file in this tree.
