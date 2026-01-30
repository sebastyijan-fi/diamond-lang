# Scripts Workspace Guidance

## Purpose
The `scripts/` workspace orchestrates developer automation, CI/CD tasks, bootstrap pipelines, and operational tooling that bring the Diamond project’s crystalline vision to life. Every script must reinforce the principles set out in the specification trilogy:

- **`diamond.md`** — intent-oriented agents, capability discipline, and deterministic decision points.
- **`diamond2.md`** — architectural feasibility, synthetic bootstrapping, and zero-trust WebAssembly execution.
- **`diamond3.md`** — grammar, algebraic effects, and module-level capability injection.

Scripts should embody secure-by-default execution, resumable workflows, and semantic intent capture while remaining reproducible across environments.

---

## Directory Contract

| Path | Status | Expectations |
| --- | --- | --- |
| `README.md` | present | Overview, quick-start commands, environment requirements. |
| `ci/` | present | Automation invoked by continuous integration (lint, test, spec guards, nightly jobs). |
| `dev/` | present | Developer tooling (local setup, scaffolding, verification helpers). |
| `bootstrap/` | planned | Synthetic corpus generation pipelines, verifier calibration routines. |
| `ops/` | planned | Operational playbooks (deployment hooks, telemetry ingestion, incident tooling). |
| `templates/` | planned | Script templates enforcing security/telemetry conventions. |
| `archive/` | planned | Retired scripts with deprecation notes and replacements. |

Add new directories only after defining local guidance and README files.

---

## Authoring Standards

1. **Metadata & Documentation**
   - Each script requires a leading comment block documenting purpose, owner, spec alignment, required capabilities, and expected inputs/outputs.
   - Maintain per-directory `README.md` files describing usage patterns, environment assumptions, and related design decisions.
   - Update `CHANGELOG.md` (or section-specific logs) when scripts change behavior, add capabilities, or adjust security posture.

2. **Language & Style**
   - Prefer POSIX-compliant shell (`#!/usr/bin/env sh` or `bash` with strict mode) unless a different runtime is warranted (Python, Rust, etc.).
   - Enforce `set -euo pipefail` (or language equivalents) and explicit error handling.
   - Use descriptive function names, safe variable expansion (`"${VAR}"`), and consistent logging conventions.

3. **Security Discipline**
   - Require explicit capability manifests or configuration files; never rely on ambient environment access.
   - Validate inputs rigorously (argument parsing, allowlists, checksum verification).
   - Store secrets outside the repository; scripts should reference secure storage mechanisms via documented interfaces.
   - Emit clear audit logs for actions that modify state, access capabilities, or interact with external services.

4. **Resumable Workflows**
   - For long-running tasks, checkpoint progress and emit resumable state files (aligned with Diamond’s continuation philosophy).
   - Use idempotent operations where possible; document recovery procedures for partial failures.

5. **Telemetry & Observability**
   - Standardize logging format (timestamp, level, component, message) and support `--log-level` toggles.
  - Emit metrics/traces via OpenTelemetry exporters when applicable.
  - Archive artifacts (reports, diagnostics) under predictable paths (`artifacts/`, `reports/`).

6. **Cross-Platform Considerations**
   - Scripts should run on Linux (primary) and macOS when feasible. Document platform-specific behaviors.
   - Leverage containerized environments or toolchain managers for consistent dependencies.

---

## Script Categories

### CI Scripts (`ci/`)
- Lint/spec guards, build/test orchestration, security scanners, nightly synthetic corpus runners.
- Must be deterministic, non-interactive, and tailored for ephemeral environments.
- Document required environment variables and exit codes.

### Developer Scripts (`dev/`)
- Local setup (`setup.sh`), format/lint wrappers, cargo/poetry helpers, benchmark runners.
- Provide dry-run/test modes where possible.
- Include contextual help (`--help`) outlining usage and relevant spec references.

### Bootstrap Scripts (`bootstrap/`, planned)
- Automate synthetic corpus generation, verifier training, and dataset validation.
- Integrate with ML pipelines; record provenance, seeds, and constraints.
- Enforce capability segregation (e.g., network access lists) and log all external interactions.

### Operations Scripts (`ops/`, planned)
- Deployment hooks, capability manifest rollouts, telemetry ingestion, incident response tooling.
- Must include rollback procedures and escalation guidance.
- Align with security and runtime playbooks.

---

## Development Workflow

1. **Proposal**
   - Open an issue describing intent, spec alignment, required capabilities, and target environments.
   - Identify owning working groups (Language, Runtime, Security, ML Enablement, Developer Experience, Operations).

2. **Implementation**
   - Scaffold script with metadata header, strict mode, and logging helpers.
   - Add tests (unit/integration) or dry-run modes; document dependencies.
   - Update documentation, capability manifests, and changelog entries.

3. **Review**
   - Validate security (least privilege, input validation), observability, and resumability.
   - Ensure linting (`shellcheck`, `shfmt`, language-specific linters) and tests pass in CI.
   - Confirm traceability links (issues, RFCs, roadmap milestones).

4. **Release**
   - Tag significant tooling releases; announce changes in developer channels.
   - Provide migration notes if behavior changes.

5. **Maintenance**
   - Monitor telemetry dashboards for anomalies.
   - Retire redundant scripts to `archive/` with replacement plans.
   - Schedule periodic audits for outdated dependencies or capability drift.

---

## Quality Checklist (Pre-Merge)

- [ ] Script header documents purpose, owner, spec alignment, and capabilities.
- [ ] Strict mode enabled; inputs validated; outputs deterministic.
- [ ] Telemetry/logging conforms to standards; artifacts stored predictably.
- [ ] Security posture reviewed (no ambient authority, secrets handled safely).
- [ ] Documentation updated (`README.md`, changelog, inline help).
- [ ] Tests/dry-run mode provided or rationale documented.
- [ ] CI integration configured (format, lint, unit/integration tests).
- [ ] Traceability links (issues, RFCs, roadmap milestones) recorded.

---

## Planned Enhancements

- Shared `Makefile`/task runner to orchestrate common workflows (lint, test, format).
- Script templates enforcing headers, strict mode, logging, and telemetry hooks.
- Automated linting/formatting pipeline for shell, Python, and other runtimes.
- Inventory (`scripts/index.yaml`) cataloging scripts, owners, capabilities, and review cadence.
- Semantic search across script documentation leveraging Diamond’s `<~>` similarity semantics.

---

Maintaining disciplined guidance in `scripts/` ensures every automation artifact remains secure, reproducible, and aligned with Diamond’s crystalline intent—from local developer shortcuts to full-fidelity CI and operational pipelines.