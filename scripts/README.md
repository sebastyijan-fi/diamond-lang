# Diamond Scripts Directory

The `scripts/` workspace hosts automation that keeps the Diamond (<>) language project consistent, reproducible, and developer-friendly. Scripts are organized by lifecycle concerns—continuous integration and local development—and are expected to be idempotent, well-documented, and security-conscious.

## Layout

- `ci/`
  - Automation used by the continuous integration pipeline.
  - Examples: compilation badges, lint/test aggregators, release gating checks, security scans.
- `dev/`
  - Utilities for local development and contributor ergonomics.
  - Examples: bootstrap installers, formatters, watch-mode runners, benchmark harnesses.

> Additional subdirectories may be introduced as the project grows (e.g., `release/`, `ops/`). Each new category should include its own README explaining scope and usage.

## Conventions

1. **Language & Portability**
   - Prefer POSIX-compliant shell scripts for portability; use higher-level languages (Python, Rust, Node.js) only when necessary.
   - Include shebangs and set `-euo pipefail` (or equivalent) to fail fast on errors.

2. **Documentation**
   - Every script should have a header comment describing its purpose, inputs, outputs, and prerequisites.
   - Provide usage examples via `--help` or inline comments.

3. **Security**
   - Avoid sourcing untrusted environments or executing downloaded code without verification.
  - Ensure secrets are never logged; rely on environment variables provided by the CI/CD platform.

4. **Idempotency**
   - Scripts should be safe to run multiple times without causing inconsistent state.
   - Clean up temporary files and artifacts to keep working directories tidy.

5. **Integration**
   - CI scripts should integrate with the workflows under `.github/workflows/`.
   - Development scripts should align with instructions in `CONTRIBUTING.md`.

## Usage Guidelines

1. **Setup**
   - Make scripts executable (`chmod +x`) after checkout.
   - Ensure required dependencies are installed (refer to comments within each script or package-specific documentation).

2. **Running in CI**
   - Scripts intended for CI must exit with non-zero status on failure to ensure pipeline accuracy.
   - When adding a new CI script, update the relevant workflow to call it explicitly.

3. **Running Locally**
   - Use `./scripts/dev/<script-name>` for local tooling.
   - Provide environment checks (e.g., rustup, wasm tools) and informative error messages when prerequisites are missing.

4. **Adding New Scripts**
   - Place them in the appropriate subdirectory (`ci/` or `dev/`).
   - Document purpose, expected environment, and invocation instructions in this README and the script’s header.
   - If the script supports configuration (flags, environment variables), document defaults and overrides.

## Roadmap

| ID | Description | Status |
|----|-------------|--------|
| SCR-001 | Bootstrap script to install compiler/runtime prerequisites | Planned |
| SCR-002 | Unified lint/test runner for local and CI usage | In Progress |
| SCR-003 | Benchmarks harness integrating with `benchmarks/` suite | Planned |
| SCR-004 | Release verification script (capability audit + changelog) | Planned |

---

**Goal:** Keep automation clear, auditable, and aligned with Diamond’s commitment to security, determinism, and developer excellence.