# Diamond Documentation Portal

Welcome to the Diamond (<>) documentation workspace. This directory houses the living specifications, architectural blueprints, security analyses, and historical design context that guide the language, runtime, and ecosystem.

## Directory Map

- `spec/` — canonical language reference (grammar, typing, effects, capabilities) and the official roadmap.
- `architecture/` — runtime design docs, sequence diagrams, WebAssembly integration notes, and operational playbooks.
- `bootstrapping/` — synthetic corpus strategy, transpiler plans, evaluation harnesses, and LLM enablement research.
- `security/` — threat models, object-capability policies, sandbox audits, and secure coding guidelines.
- `design-decisions/` — accepted proposals, RFC archives, and rationale for major trade-offs.

## How to Use This Space

1. **Start with the overview**: read `spec/overview.md` (once published) to understand the high-level language model.
2. **Follow the roadmap**: `spec/roadmap.dm` tracks milestones across specification, compiler, runtime, and ecosystem tracks.
3. **Dive into architecture** when implementing runtime features or effect handlers.
4. **Consult bootstrapping** when generating or validating Diamond corpora and LLM workflows.
5. **Review security** before modifying capabilities, sandbox boundaries, or supervisor behaviors.
6. **Check design decisions** to understand the historical context and avoid reopening settled questions.

## Contribution Guidance

- Keep documents versioned and reference related RFCs or issues.
- Prefer diagrams and sequence charts (stored in `architecture/`) for complex flows.
- When adding specifications, include examples in `.dm` format and link to relevant tests or prototypes.
- Changes that alter language semantics or runtime guarantees should be paired with an RFC entry in `design-decisions/`.

## Status

The documentation set is currently in the **Definition & Planning** phase. Expect rapid iteration as the specification, bootstrap tooling, and runtime evolve. Please coordinate with the documentation working group before making sweeping structural changes.

“From probabilistic intent to deterministic action.” This documentation space captures the knowledge required to make Diamond the crystalline substrate for the agentic era.