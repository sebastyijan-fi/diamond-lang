# Diamond Runtime & Architecture Hub

This space curates system-level documentation for the Diamond (<>) language stack. It connects specification artifacts with implementation blueprints so contributors can reason about how source code, compiler pipelines, runtime services, and deployment infrastructure converge into a cohesive platform.

---

## Document Index

| Path | Purpose |
|------|---------|
| `docs/architecture/runtime-overview.md` | High-level runtime topology, execution lifecycle, and component responsibilities. |
| `docs/architecture/compiler-pipeline.md` | Front-end → HIR → Wasm back-end flow, intermediate representations, and build orchestration. |
| `docs/architecture/effects-runtime.md` | Effect dispatcher internals, continuation persistence, and supervisor integration. |
| `docs/architecture/capability-flow.md` | Capability issuance, attenuation, enforcement, and auditing across compiler/runtime boundaries. |
| `docs/architecture/decision-engine.md` | Diamond operator (`<>`) implementation details, embedding services, and fallback heuristics. |
| `docs/architecture/prompt-router.md` | Prompt execution pipeline, constrained decoding enforcement, and verifier model strategy. |
| `docs/architecture/observability.md` | Telemetry surfaces (metrics, logs, traces), correlation IDs, and redaction policies. |
| `docs/architecture/deployment-modes.md` | Embedded, daemon, clustered, and sandbox deployment topologies with configuration guidance. |
| `docs/architecture/security-threat-model.md` | End-to-end threat analysis, trust boundaries, and recommended mitigations. |

> **Status:** Some files are placeholders; update the table when new documents merge.

---

## Structure & Conventions

1. **Context-First Summaries**  
   Each document starts with rationale, scope, and audience to align readers quickly.

2. **Layered Detail**  
   Diagrams, sequence charts, and interface definitions progress from high-level concepts to implementation contracts.

3. **Traceability**  
   Inline references link back to canonical specs (e.g., `docs/spec/runtime.md`, `docs/spec/capabilities.md`) and accepted RFCs in `docs/design-decisions/`.

4. **Change Control**  
   Architectural updates that modify runtime guarantees, effect semantics, or capability flows require an RFC. Each file maintains a changelog section with version history.

5. **Artifacts & Assets**  
   Store editable diagrams under `design/` (e.g., `.drawio`, `.affinity`) and export read-only `PNG/SVG` assets alongside the documents with clear naming.

---

## Contribution Workflow

1. **Propose / Synchronize**  
   - Review existing docs to avoid duplication.  
   - Sync with relevant working groups (Runtime, Compiler, Security, ML Enablement, Developer Experience).

2. **Draft & Review**  
   - Author markdown in this directory, ensuring sections for background, architecture, data flows, and failure modes.  
   - Add diagrams or sequence charts where they illuminate effect, capability, or execution paths.  
   - Submit a PR referencing related issues or RFCs. Request reviews from topic-owning teams.

3. **Finalize**  
   - Update the index table above with links and one-line summaries.  
  - Cross-link new docs from `docs/spec/roadmap.dm` or relevant design decisions.

---

## Related References

- `docs/spec/` — Canonical language and runtime specifications.
- `docs/bootstrapping/` — Synthetic data strategy and model enablement plans.
- `packages/runtime/` — Source for runtime host, effects engine, and continuation services.
- `packages/compiler/` — Front-end, HIR, back-end crates, and CLI.
- `packages/tooling/` — Transpiler, prompt packs, and auxiliary developer utilities.
- `benchmarks/` — Performance and durability stress suites.

---

## Changelog

| Version | Date | Author | Notes |
|---------|------|--------|-------|
| v0.1 | 2024-XX-XX | (to be filled on merge) | Initial architecture hub scaffold. |

---

**Mission:** Establish a crystal-clear architecture narrative so that every contributor—from spec authors to runtime implementers—can build and validate Diamond with confidence.