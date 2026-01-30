# Diamond (<>) Programming Language

Diamond (<>) is an agent-native programming language, runtime, and toolchain engineered for the age of autonomous AI. The project harmonizes probabilistic LLM reasoning with deterministic execution through structural typing, algebraic effects, and object-capability security — all compiled to WebAssembly for zero-trust deployment.

## Vision

- **Agent-Centric Abstractions**: First-class prompts, decisions, semantic types, and effect handlers map directly onto agent cognition loops.
- **Deterministic Surfaces**: Structural typing with semantic refinements collapses hallucinations at compile-time or within constrained decoding.
- **Algebraic Durability**: Algebraic effects plus resumable continuations make long-lived workflows resilient without bespoke workflow engines.
- **Zero-Trust Runtime**: Object capabilities and Wasm sandboxing guarantee that authority is explicit, auditable, and attenuated.

## Repository Structure

```
docs/                 ← specifications, architecture, bootstrapping theory, security guidance, design notes
packages/             ← implementation projects (compiler, runtime, stdlib, language server, tooling)
  compiler/           ← front-end, HIR, back-end, CLI, conformance tests
  runtime/            ← host runtime, effect system, continuation storage
  stdlib/             ← curated batteries (`std-agent`, `std-memory`, `std-unit`, …)
  language-server/    ← editor integrations (LSP, diagnostics, formatting)
  tooling/            ← transpiler, prompt packs, auxiliary developer tools
examples/             ← canonical samples (getting started, agents, integration patterns)
scripts/              ← CI and developer automation
.github/workflows/    ← continuous integration pipelines
benchmarks/           ← performance and effect/continuation stress suites
research/             ← experiments, papers, benchmark studies
design/               ← UX flows, logos, branding, interaction prototypes
```

## Guidance Documentation

Every directory includes a `GUIDANCE.md` file providing localized contribution instructions, quality checklists, and alignment with the foundational manuscripts (`diamond.md`, `diamond2.md`, `diamond3.md`).

### Key Guidance Files

| Area | Guidance File | What It Covers |
| --- | --- | --- |
| Compiler | `packages/compiler/GUIDANCE.md` | Rust crates, testing strategy, diagnostics |
| Runtime | `packages/runtime/GUIDANCE.md` | Effects, continuations, capability enforcement |
| Standard Library | `packages/stdlib/GUIDANCE.md` | Module design, API stability, semantic types |
| Language Server | `packages/language-server/GUIDANCE.md` | LSP features, responsiveness, editor integration |
| Tooling | `packages/tooling/GUIDANCE.md` | Transpiler, prompt packs, synthetic corpus |
| Examples | `examples/GUIDANCE.md` | Agent archetypes, integration patterns |
| Design Decisions | `docs/design-decisions/GUIDANCE.md` | RFCs, decision records, governance |
| CI/Automation | `.github/GUIDANCE.md` | Workflows, spec guards, nightly jobs |

**Before contributing to any area, read the relevant `GUIDANCE.md` file first.**

## Language Highlights

- **`.dm` Source Files**: Concise extension for Diamond modules (alias `.dia` reserved).
- **Diamond Operator `< >`**: Declarative probabilistic branching with semantic routing.
- **Semantic Types**: Refinement clauses enforced via grammars and verifier models.
- **Module-Scoped Capabilities**: Import-time security contracts eliminate ambient authority.
- **Prompt Primitives**: Declarative, typed prompt blocks with constrained decoding baked in.

## Implementation Roadmap

1. **Specification Freeze** — lock grammar, effect semantics, capability model, decision operator.
2. **Synthetic Bootstrapping** — Python→Diamond transpiler, LLM-guided evolution, corpus curation.
3. **Compiler Toolchain** — layout-sensitive parser, type/effect inference, Wasm component back-end.
4. **Runtime & Effects** — effect dispatcher, continuation store, prompt execution pipeline, capability enforcement.
5. **Standard Library & Bridges** — batteries for agent cognition, persistence, units; Wasm bridges to existing ecosystems.
6. **LLM Enablement** — continued pre-training, prompt packs, model benchmarks on Diamond tasks.
7. **Developer Experience** — LSP, formatter, playgrounds, documentation, CI templates.

## Getting Started (Roadmap)

Until the compiler toolchain is released, track progress via:

- `docs/spec/`: evolving language reference
- `docs/architecture/`: runtime blueprints and Wasm component model integration
- `docs/bootstrapping/`: synthetic data strategy, evaluation harnesses
- `packages/tooling/transpiler/`: early experiments for Python subset translation

## Contributing

Diamond will operate as an open governance project:

1. Read `docs/design-decisions/` for accepted proposals.
2. Join discussions in the forthcoming SIGs (Language, Runtime, Security, ML Enablement, DX).
3. Submit RFCs through the repository issue templates once they are published in `.github/`.

Contribution focus areas include:

- Formal verification of semantic refinements and effect handlers
- Optimized Wasm component pipelines and capability descriptors
- LLM evaluation harnesses and synthetic data validation
- Standard library design for agent cognition patterns

## Governance & Values

- **Security by Construction**: every feature must respect least authority and deterministic review surfaces.
- **Agent Ergonomics**: optimize for LLM cognition without sacrificing human clarity.
- **Open Protocols**: interoperable with existing languages via Wasm components and signed capability manifests.
- **Evidence-Based Evolution**: changes advance with benchmarks, formal reasoning, or empirical studies.

## Status

Diamond is currently in the **Definition & Planning** phase:

- ✅ Foundational design documents (`diamond.md`, `diamond2.md`, `diamond3.md`)
- 🚧 Directory scaffolding for compiler/runtime/tooling packages
- 🛠️ Specification, bootstrapping, and implementation tracks under active development

Follow the roadmap in `docs/spec/roadmap.dm` (coming soon) for detailed milestones and release planning.

---

**“From probabilistic intent to deterministic action.”** Diamond aims to become the crystalline substrate for the agentic era.