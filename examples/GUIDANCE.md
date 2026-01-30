# Examples Workspace Guidance

## Purpose
The `examples/` workspace demonstrates how to build Diamond (`.dm`) agents that honor the language’s crystalline commitments articulated in the core manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and structured decision-making (`<>`).
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping, and zero-trust runtime execution.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

Every example must reinforce secure-by-default execution, resumable effects, and semantic intent capture.

---

## Directory Contract

| Path | Status | Expectations |
| --- | --- | --- |
| `README.md` | present | Orientation, contribution workflow, roadmap. |
| `getting-started/` | present | Onboarding scenarios; each subfolder needs a README and runnable steps. |
| `agents/` | present | Opinionated agent archetypes (ReAct, supervisor flows, swarm orchestration). |
| `integration/` | present | Interop examples (Wasm components, external systems, telemetry). |
| `<category>/<example>/` | planned | Each example should live in its own subdirectory with assets, README, configs, fixtures, and tests if applicable. |
| `templates/` | planned | Starter kits or scaffolds for new examples. |
| `assets/` | planned | Shared diagrams, datasets, or mock transcripts (document provenance). |

Before creating a new directory, add a local README describing scope and review owners.

---

## Authoring Standards

1. **Metadata**
   - Each example directory must include a `README.md` with:
     - Title, authors, status (`Draft`, `Review`, `Stable`, `Deprecated`).
     - Alignment references (specific sections of the trilogy).
     - Dependencies (packages, scripts, external services).
     - Execution steps and expected outputs.
     - Telemetry expectations (logs, traces, metrics).
     - Security and capability notes (required manifests, sandbox constraints).

2. **Source Layout**
   - Prefer `src/` for `.dm` files when multiple modules exist.
   - Store configuration under `config/` (capability manifests, runtime settings).
   - Place deterministic fixtures under `fixtures/`.
   - Keep generated artifacts out of version control (`.gitignore` with `target/`, `logs/`, etc.).

3. **Code Quality**
   - Adhere to current syntax (square-bracket generics, explicit `perform`, module capability imports).
   - Include inline comments that reference relevant spec clauses when demonstrating nuanced behavior.
   - Maintain idempotent runs; tests should reset continuation stores and stateful backends.

4. **Security Discipline**
   - Ship explicit capability manifests (`capabilities.toml`/`json`) with explanations.
   - Highlight attack mitigations (prompt injections, capability misuse) in the README.
   - Avoid embedding secrets; use mock credentials with provenance notes.

5. **Telemetry & Observability**
   - Demonstrate logging, metrics, and tracing where meaningful.
   - Reference dashboards or scripts in `benchmarks/` or `scripts/` to inspect results.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the example: problem statement, teaching goals, targeted audience, linkage to spec sections, and expected outputs.
   - Identify reviewers from relevant working groups (Language, Runtime, Security, ML Enablement, Developer Experience).

2. **Implementation**
   - Scaffold directory structure and README.
   - Implement `.dm` code, configuration, and optional tests.
   - Document execution steps and troubleshooting tips.

3. **Review**
   - Seek feedback on correctness, style, capability usage, and telemetry.
   - Ensure references to spec documents and design decisions are accurate.
   - Provide CI instructions or scripts for reproducible verification.

4. **Publish**
   - Update `examples/README.md` with a short summary and status.
  - Link to supporting RFCs or decision records.
  - Add changelog entries if the example introduces or clarifies normative behavior.

5. **Maintain**
   - Revisit examples whenever spec changes land.
   - Mark outdated examples with `> **Status:** Outdated – see <link>` and create follow-up issues.
   - Archive deprecated examples into `archive/` (planned) with rationale and replacement pointers.

---

## Quality Checklist

- [ ] README includes metadata, alignment references, and execution instructions.
- [ ] Code compiles with current toolchain and respects grammar/effect rules.
- [ ] Capability manifests are explicit and justified.
- [ ] Telemetry guidance documented (logs/traces/metrics).
- [ ] Security considerations and failure modes described.
- [ ] Example scoped to a single teaching goal with clear narrative.
- [ ] Tests or validation scripts provided when feasible.
- [ ] Linked to relevant docs (`docs/spec/`, `docs/architecture/`, `docs/security/`, `docs/design-decisions/`).
- [ ] Changelog/roadmap updates created if scope impacts milestones.

---

## Future Enhancements

- Automated smoke tests for examples (CI job once compiler/runtime mature).
- Example index (`examples/index.yaml`) enumerating tags, difficulty, and dependencies.
- Reusable templates for common archetypes (LLM tool-use, human-in-the-loop, swarm orchestration).
- Semantic search support leveraging Diamond’s `<~>` similarity semantics.
- Integration with documentation portal for live playground experiences.

---

A well-maintained `examples/` workspace accelerates adoption, clarifies best practices, and keeps Diamond’s crystalline intent tangible from “hello world” to production-grade agents. Keep every contribution precise, reproducible, and security-conscious.