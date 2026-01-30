# Diamond Packages Overview

The `packages/` directory contains the implementation workstreams that transform the Diamond specification into a complete toolchain, runtime, and developer ecosystem. Each subdirectory is self-contained, versioned, and tested with shared CI workflows. The sections below summarize the purpose of each package and highlight primary components and deliverables.

## Layout

- `compiler/`  
  Houses the Diamond compiler proper. It is organized into Rust crates for the front-end parser and analyzer, intermediate representations, Wasm back-end, and command-line tooling. A dedicated `tests/` directory maintains conformance suites and golden outputs.
  - `crates/frontend/` — Layout-sensitive parser, lexer, symbol resolver, and structural type checker.
  - `crates/hir/` — High-level IR definitions, transformations, and effect/type inference passes.
  - `crates/backend/` — WebAssembly Component Model generator, capability manifest emitter, and optimization passes.
  - `crates/cli/` — `diamondc` command-line interface for building, formatting, and linting sources.
  - `tests/` — Integration tests covering grammar acceptance, effect typing, capability enforcement, and ABI generation.

- `runtime/`  
  Implements the host runtime for executing compiled Diamond Wasm components. It includes the effect dispatcher, continuation store, capability manager, and host adapters for system resources.
  - `host/` — Runtime orchestrator, module loader, scheduler, and sandbox integration.
  - `effects/` — Algebraic effect handlers, decision engine bridge, prompt router hooks.
  - `continuations/` — Serialization, storage backends, resumable fiber infrastructure, and integrity checks.

- `stdlib/`  
  Curated standard library modules that provide batteries for agent cognition, persistence, and physical safety.
  - `std-agent/` — Reference cognitive architectures (Chain, ReAct, Tree, Graph) implemented with Diamond primitives.
  - `std-memory/` — Vector stores, semantic recall helpers, persistence abstractions, and capability-aware storage APIs.
  - `std-unit/` — Dimensional analysis types, unit conversions, and verification utilities for physical systems.

- `language-server/`  
  Language Server Protocol implementation offering diagnostics, auto-completion, effect visualization, capability warnings, and formatter integration for editors.

- `tooling/`  
  Auxiliary developer tools that accelerate adoption and ecosystem bootstrapping.
  - `transpiler/` — Python → Diamond transpilation pipeline for synthetic corpus generation and migration tooling.
  - `prompt-packs/` — Canonical prompt templates, structured decision grammars, and reusable LLM invocation profiles.

## Conventions

- All packages adhere to shared CI scripts in `scripts/ci/` and must pass formatting, linting, and security scans before merge.
- Documentation for each package should include an internal `README.md`, architectural diagrams (stored in `design/`), and links to relevant specifications in `docs/spec/`.
- Capability usage within packages must be declared explicitly and tested with the security harness found under `docs/security/`.
- Cross-package changes require coordination via RFCs logged in `docs/design-decisions/`, with version bumps managed through the release process.

## Getting Started

1. Clone the repository and install the required toolchain (Rust nightly, Wasm tooling, Node.js where applicable).
2. Run `scripts/dev/bootstrap.sh` (planned) to install dependencies for compiler, runtime, and LSP builds.
3. Execute `scripts/dev/test.sh` to verify the workspace before making changes.
4. Consult each package’s local documentation for contribution guidelines and module-specific workflows.

The `packages/` tree is the foundation of the Diamond implementation. Keep each package modular, well-tested, and synchronized with the evolving specification to maintain a crystalline, agent-ready language stack.