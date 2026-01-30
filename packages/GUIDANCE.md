# Packages Workspace Guidance

## Purpose
The `packages/` workspace contains the implementation modules that realize Diamond’s crystalline vision. Every sub-project must remain aligned with the foundational manuscripts:

- **`diamond.md`** — intent-oriented language design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — grammar, semantic typing, algebraic effects, and module-level capability injection rules.

All code within `packages/` must reinforce secure-by-default execution, resumable effects, and semantic intent capture while providing production-grade tooling.

---

## Directory Contract

| Path | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `compiler/` | Language + Runtime | Front-end, mid-tier (HIR), and backend emitters targeting the Wasm Component Model. |
| `runtime/` | Runtime + Security | Capability manager, effect dispatcher, continuation tiers, host bindings, telemetry adapters. |
| `stdlib/` | Language + Developer Experience | Curated standard modules (`std.agent`, `std.memory`, `std.unit`, …) with explicit capability manifests. |
| `language-server/` | Developer Experience | LSP server, formatting, diagnostics, and semantic navigation. |
| `tooling/` | Developer Experience + ML Enablement | CLI utilities, transpilers, prompt packs, corpus generators, and test harnesses. |
| `README.md` | All WGs | High-level orientation, build matrix, and cross-links to subpackages. |
| `*/GUIDANCE.md` (planned) | Subpackage owners | Localized contribution guidance (test matrix, code style, API stability). |

Subdirectories must not be created without an owning working group, README, and guidance note.

---

## Cross-Cutting Authoring Standards

1. **Metadata & Documentation**
   - Each crate or tool requires a `README.md` detailing purpose, architecture, build instructions, and spec alignment.
   - Maintain `CHANGELOG.md` or release notes per subpackage with semantic versioning.
   - Embed crate-level doc comments referencing relevant spec sections.

2. **Coding Conventions**
   - Rust code follows `rustfmt` + `clippy` (deny warnings); Python/Golang/TypeScript tools follow equivalent format/lint rules.
   - Enforce explicit capability wiring; ambient authority is prohibited.
   - Effects must be modeled with resumable continuations; document persistence tiers (hot/warm/cold).

3. **Testing & Quality**
   - Provide unit, integration, and property/fuzz tests where applicable.
   - Nightly jobs should run extended suites (synthetic corpus validation, continuation resume stress tests).
   - Benchmark regressions route through `benchmarks/` with shared fixtures.

4. **Security Discipline**
   - Capability manifests must live alongside binaries (`capabilities/` or `config/`).
   - Integrate security scans (dependency auditing, capability diff checks, Wasm policy verification).
   - Sensitive configuration defaults to least privilege; document escalation paths.

5. **Telemetry**
   - Emit structured logs, metrics, and traces with OpenTelemetry conventions.
   - Provide instrumentation hooks toggled via configuration to support observability examples.

6. **Governance & Traceability**
   - Significant API or behavior changes require an RFC (`docs/design-decisions/rfcs/`).
   - Link PRs to roadmap milestones (`docs/spec/roadmap.dm`) and relevant design decisions.
   - Keep `CODEOWNERS` (planned) in sync with current maintainers.

---

## Subpackage Expectations

### `compiler/`
- Crate structure: `frontend`, `hir`, `backend`, `cli`, plus shared utilities.
- Provide golden tests for lexer/parser, AST snapshots, type checking, effect inference, and Wasm emission.
- Implement diagnostics aligned with language server: IDs, severity, remediation hints.
- Ensure deterministic outputs for synthetic corpus validation; expose `--emit` modes (AST, HIR, Wasm).

### `runtime/`
- Components: `continuations/`, `effects/`, `host/` (capabilities, sandboxes, manifests).
- Continuation store must support tiered persistence with documented durability SLAs.
- Capability manager enforces attenuation and sandbox boundaries; include fuzzing harnesses for misuse scenarios.
- Provide sample host integrations (CLI runner, embeddable library) with telemetry hooks.

### `stdlib/`
- Module layout mirrors spec taxonomy (`std-agent`, `std-memory`, `std-unit`, etc.).
- Each module ships with capability manifests, examples, and unit/property tests.
- Document stability levels (`unstable`, `experimental`, `stable`) and semantic versioning.
- Enforce semantic refinements via verifier integration; ensure types align with compiler and runtime expectations.

### `language-server/`
- Deliver LSP features: hover, completion, diagnostics, formatting, code actions, symbol navigation.
- Maintain protocol compatibility matrix (VS Code, Neovim, JetBrains adapters).
- Provide integration tests using fixture workspaces and simulated compiler responses.
- Expose telemetry on diagnostic latency and completion accuracy.

### `tooling/`
- Subdirectories: `transpiler/`, `prompt-packs/`, and future utilities (e.g., `fmt`, `docgen`).
- Transpiler integrates with synthetic corpus pipeline; document supported language subsets and limitations.
- Prompt packs include metadata (model targets, capability requirements, safety constraints).
- Ensure tools respect capability and security posture (no ambient environment access).

---

## Development Workflow

1. **Proposal**
   - File issue with scope, spec alignment, affected packages, success metrics, and capability implications.
   - Determine required RFCs and reviewers.

2. **Implementation**
   - Follow guidance, maintain docs/tests, and include scaffolding for observability and security.
   - Keep commits focused; avoid mixing refactors with feature work.

3. **Review**
   - Enforce multi-disciplinary reviews (Language, Runtime, Security, Developer Experience, ML as appropriate).
   - Validate CI results (format, lint, tests, security, benchmarks).
   - Confirm documentation and changelog updates.

4. **Release**
   - Tag crates/tools per semantic versioning.
   - Publish release notes summarizing features, breaking changes, security considerations, and telemetry impact.
   - Update roadmap status and public documentation.

5. **Maintenance**
   - Monitor telemetry dashboards for regressions.
   - Address security advisories promptly; document mitigation steps.
   - Schedule technical debt reviews and API stability audits each milestone.

---

## Quality Checklist (Pre-Merge)

- [ ] Code follows formatting/lint rules and passes test suites.
- [ ] Capability manifests updated and reviewed; least privilege enforced.
- [ ] Telemetry instrumentation present with documentation.
- [ ] Documentation (README, CHANGELOG) reflects changes and references trilogy sections.
- [ ] Security implications and mitigations recorded.
- [ ] Benchmarks (where applicable) updated or appended.
- [ ] Roadmap, issues, and RFC links added for traceability.
- [ ] Release plan drafted for externally consumed packages.

---

## Planned Enhancements

- Shared `packages/Makefile` or task runner to unify build/test workflows.
- Monorepo manifest (`packages/index.yaml`) cataloging crates, owners, versions, stability, and capability requirements.
- Template generator for new crates/tools honoring security and telemetry defaults.
- Automated coverage reporting and fuzzing integration pipelines.
- Semantic search across package APIs using Diamond’s `<~>` similarity semantics.

---

Maintaining disciplined guidance within `packages/` ensures every implementation layer—from compiler to runtime, standard library, language server, and tooling—delivers on Diamond’s promise: secure, resumable, semantically precise agent engineering.