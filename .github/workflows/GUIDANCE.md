# Workflow Guidance

## Purpose
The `.github/workflows/` directory encodes automated policy for the Diamond project. Every workflow must operationalize the language’s three foundational commitments articulated in `diamond.md`, `diamond2.md`, and `diamond3.md`:

1. **Secure-by-default execution** — mirror the capability discipline and zero-ambient-authority stance.
2. **Resumable, effect-aware processes** — treat long-running jobs as resumable effects, emitting state that can be resumed or retried deterministically.
3. **Semantic intent capture** — expose structured metadata so supervisors (people or agents) can reason about the workflow’s goals and outcomes.

## Mandatory Files (Current & Planned)
| File | Status | Guidance |
| --- | --- | --- |
| `ci.yml` | present | Baseline lint/build/test gate; enforces spec/RFC policy. |
| `nightly.yml` | planned | Synthetic corpus generation and front-end validation. |
| `security-audit.yml` | planned | Capability and dependency scanning aligned with OCap rules. |
| `release.yml` | planned | Tagged release pipeline producing signed Wasm artifacts and changelog updates. |

Additions or removals must be tracked through the design-decision RFC process to preserve auditability.

## Workflow Design Checklist
Before committing a workflow, ensure:

- **Spec linkage**: reference relevant spec section or RFC in a header comment.
- **Capability scoping**: request the minimal GitHub permissions; default to read-only tokens.
- **Effect resumability**: for multi-step jobs, upload intermediate artifacts, enabling manual resume if a step fails.
- **Semantic telemetry**: emit JSON summaries (intent, affected packages, capability deltas) to `artifacts/telemetry/`.

## `ci.yml` Expectations
- Validates documentation formatting, spec deltas, and placeholder code builds.
- Blocks direct edits to the diamond specification trilogy unless the PR references an approved RFC.
- Runs language-aware linting (Rust, Python, Markdown) once the corresponding tooling exists.

### Suggested Skeleton
```/dev/null/workflows/ci.yml#L1-22
name: Diamond Continuous Integration
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
jobs:
  prepare:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Report workflow intent
        run: echo '{"intent":"spec_guard","spec_files":"docs/spec/**"}' > intent.json
      - uses: actions/upload-artifact@v4
        with:
          name: workflow-intent
          path: intent.json
  spec-guard:
    needs: prepare
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: workflow-intent
      - name: Enforce RFC linkage
        run: scripts/dev/verify_spec_changes.sh
```

## Nightly Bootstrap Workflow (Planned)
Purpose: generate synthetic Diamond corpus, run compiler front-end golden tests, and archive diagnostics for ML teams.

Key behaviors:
- Dispatch as a resumable job; each major step uploads state.
- Tag artifacts with `nightly-<date>` and capability context.
- Notify the ML enablement channel on failure with summary JSON.

### Pseudocode Blueprint
```/dev/null/workflows/nightly.yml#L1-28
name: Nightly Bootstrap Corpus
on:
  schedule:
    - cron: '0 3 * * *'
jobs:
  synthesize:
    runs-on: ubuntu-latest
    steps:
      - checkout repository
      - setup rust stable toolchain
      - setup python with poetry
      - run scripts/ci/bootstrap_corpus.sh
      - upload artifact: corpus.tar.zst
  compile:
    needs: synthesize
    runs-on: ubuntu-latest
    steps:
      - download artifact: corpus.tar.zst
      - run cargo test -p diamond-frontend --features nightly
      - archive diagnostics: diagnostics.json
  notify:
    needs: [compile]
    if: failure()
    runs-on: ubuntu-latest
    steps:
      - run scripts/ci/post_failure_summary.py diagnostics.json
      - use webhook secret to post structured alert
```

## Security Audit Workflow (Planned)
Focus: enforce OCap discipline on dependencies and check for privileged token usage.

- Run on a weekly cron.
- Execute SPDX/cycloneDX generation for dependency manifests.
- Compare requested permissions in workflow files against allowlist.
- Emit machine-readable report (`security/audit-<timestamp>.json`).

## Release Workflow (Planned)
Trigger: tagged commits (`v*`).

Responsibilities:
- Build compiler/runtime Wasm components.
- Sign artifacts with project key.
- Publish release notes sourced from `CHANGELOG.md`.
- Validate that standard library modules include capability manifest snapshots.

## Contribution & Review Process
1. Draft or update guidance here when introducing a new workflow.
2. File an RFC for workflows affecting security posture, effect handling, or release process.
3. Obtain approvals from relevant working-group leads (Language for spec-related checks, Runtime for effect/resume logic, Security for OCap enforcement).
4. Keep telemetry schemas backwards compatible to support automated analysis.

## Future Enhancements
- **Effect lineage tracking**: adopt a shared metadata format for workflow steps mirroring runtime continuation descriptors.
- **Adaptive retries**: integrate a supervisor action that retries failing jobs with context injection, paralleling Diamond’s effect resumption semantics.
- **Model-in-the-loop validation**: before running expensive jobs, query a verifier model to predict risk hotspots (aligns with semantic refinement philosophy).

Maintaining robust workflow guidance ensures automation evolves in tandem with the language’s intent-oriented, capability-secure, and effect-resumable architecture.