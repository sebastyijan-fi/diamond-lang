# .github Guidance

## Purpose
The `.github/` directory centralizes automation, community health files, and workflow configuration for the Diamond project. Every asset in this folder should reinforce the language’s core principles described in the specification trilogy (`diamond.md`, `diamond2.md`, `diamond3.md`): secure-by-default execution, resumable agent workflows, and semantic intent capture.

## Required Subdirectories & Files
- `.github/workflows/`: Continuous integration and governance automation.
  - `ci.yml`: Comprehensive pipeline with the following jobs:
    - **guidance-check**: Validates presence and structure of GUIDANCE.md files.
    - **docs-lint**: Markdown linting and broken link detection.
    - **spec-guard**: Protects specification files, requires RFC linkage for changes.
    - **compiler-check**: Rust formatting, linting, and tests (when workspace exists).
    - **runtime-check**: Runtime workspace validation (when workspace exists).
    - **tooling-check**: Python tooling and prompt pack validation.
    - **ci-summary**: Aggregates results and reports status.
- `.github/ISSUE_TEMPLATE/` _(planned)_:
  - `bug_report.md`: Collects reproduction steps, capability context, and affected spec sections.
  - `feature_request.md`: Captures motivation, spec references, and proposed effect/type additions.
  - `rfc_proposal.md`: Links to drafts under `docs/design-decisions/rfcs/`.
- `.github/PULL_REQUEST_TEMPLATE.md` _(planned)_:
  - Checklist for spec alignment, capability impact assessment, and artificial decision coverage.
- `.github/CODEOWNERS` _(planned)_:
  - Maps directories to working-group owners (Language, Runtime, Security, ML Enablement, DX).
- `.github/labels.yml` _(planned)_:
  - Declarative label definitions (e.g., `spec`, `runtime`, `capability`, `transpiler`, `ml-pipeline`).

## Governance Patterns
All automation should encode the following policy guidelines:

1. **Spec Integrity**
   - Workflows must fail if changes touch `docs/spec/` without linking to an open RFC.
   - Pull requests editing the three core spec documents require approvals from both Language and Runtime owners.

2. **Security Guardrails**
   - PR templates mandate capability impact summaries.
   - CI enforces that new workflows run with least privilege (explicit permission scopes, no default `GITHUB_TOKEN` write access).

3. **Durable Build Discipline**
   - Workflows cache toolchains declaratively; every job emits reproducibility metadata (Rust toolchain version, Python environment hashes).
   - Scheduled workflow (future `nightly.yml`) validates `scripts/bootstrap_corpus.py` output against the compiler front-end once it exists.

## Suggested Workflow Skeletons

### Current CI Jobs (Implemented)

| Job | Purpose | Blocks Merge |
| --- | --- | --- |
| `guidance-check` | Validates GUIDANCE.md presence and structure | Yes |
| `docs-lint` | Markdown linting and link checking | No (warnings) |
| `spec-guard` | Flags spec changes requiring RFC | No (warnings) |
| `compiler-check` | Rust workspace checks | No (until toolchain matures) |
| `runtime-check` | Runtime workspace checks | No (until toolchain matures) |
| `tooling-check` | Python and prompt pack validation | No (warnings) |

### Nightly Synthetic Corpus Validation (Planned)
```/dev/null/nightly_bootstrap.yml#L1-14
name: Nightly Bootstrap Corpus
on:
  schedule:
    - cron: '0 3 * * *'
jobs:
  transpile-and-verify:
    runs-on: ubuntu-latest
    steps:
      - checkout repo
      - setup rust toolchain
      - run python env for transpiler
      - execute scripts/bootstrap_corpus.py
      - run packages/compiler CLI against generated samples
      - upload artifact & failure report
```

## Contribution Expectations
- Update this guidance file whenever new automation folders or templates are introduced.
- For each workflow addition, document intent, triggers, and security posture in a short comment block at the top of the YAML.
- Coordinate significant CI changes via RFCs to keep tooling decisions auditable alongside language evolution.

## CI Validation Rules

### GUIDANCE.md Requirements
The `guidance-check` job enforces:
1. All key directories must have a `GUIDANCE.md` file.
2. Every `GUIDANCE.md` must include a `## Purpose` section.
3. Guidance files should reference the specification trilogy where applicable.

### Spec Change Protection
The `spec-guard` job monitors changes to:
- `diamond.md`, `diamond2.md`, `diamond3.md` (core manuscripts)
- Files under `docs/spec/`

Changes to these files trigger a warning requiring:
- An associated RFC in `docs/design-decisions/rfcs/`
- Approval from Language WG and Runtime WG leads
- Updated `CHANGELOG.md` entry

### Adding New CI Jobs
When adding new CI jobs:
1. Follow the existing job structure pattern.
2. Use meaningful job names that describe the check.
3. Add the job to the `ci-summary` dependency list.
4. Document the job purpose in this guidance file.
5. Prefer warnings over failures during early development.

Keeping `.github/` disciplined ensures Diamond’s implementation roadmap remains enforceable, reproducible, and aligned with the language’s foundational philosophy.