# Diamond Compiler Package

This package contains the reference implementation of the Diamond (<>) compiler. Its goal is to transform `.dm` source modules into capability-scoped WebAssembly (Wasm) components while enforcing the language’s structural typing, semantic refinements, and algebraic effect semantics.

## Goals

- **Spec Fidelity**: Track the canonical language specification (`docs/spec/`) with automated regression suites.
- **Deterministic Output**: Emit reproducible Wasm artifacts annotated with capability manifests and constrained-decoding grammars.
- **Tooling Reuse**: Expose reusable libraries for the language server, transpiler, and runtime diagnostics.
- **Security-aware Compilation**: Surface capability, effect, and semantic refinement violations at compile time.

## Directory Structure

```
crates/
  frontend/     <- Lexer, parser, symbol resolver, structural type checker
  hir/          <- High-level IR (HIR), effect inference, transformation passes
  backend/      <- Wasm Component Model generator, capability manifest emitter
  cli/          <- `diamondc` command-line interface (build, fmt, lint, repl)
tests/          <- Integration and conformance suites (AST, HIR, Wasm golden files)
```

- **`crates/frontend/`**  
  Implements the layout-sensitive lexer, Pratt-style parser, and structural type checker. Responsible for semantic refinements (`where` clauses), decision operator parsing (`<>`), and capability import validation.

- **`crates/hir/`**  
  Defines the compiler’s intermediate representation. Handles algebraic effect inference, continuation analysis, and optimization-friendly transformations (e.g., inline decisions, capability propagation).

- **`crates/backend/`**  
  Lowers HIR to the WebAssembly Component Model. Produces WIT interface definitions, capability manifests, constrained-decoding metadata, and sandbox-safe host bindings.

- **`crates/cli/`**  
  Provides the `diamondc` binary with subcommands:
  - `build`: Compile `.dm` sources to Wasm components
  - `fmt`: Format source files using canonical spacing/bracing rules
  - `lint`: Run static analysis (capability leakage, unused effects, semantic drift)
  - `check`: Syntax/type verification without emission
  - `repl` (planned): Interactive shell for quick experimentation

- **`tests/`**  
  Houses integration and conformance tests. Each suite pairs source fixtures with expected AST snapshots, HIR dumps, and Wasm outputs. Includes negative tests for security and capability violations.

## Development Workflow

1. **Bootstrap**: Install Rust (nightly toolchain), wasm32-wasi target, and Wasm component tooling.
2. **Build**: `cargo build --workspace` within the `compiler` package.
3. **Test**: `cargo test --workspace` to execute unit and integration suites.
4. **Format/Lint**: `cargo fmt` and `cargo clippy --all-targets --all-features`.
5. **Golden Updates**: Regenerate golden outputs via `cargo test -p compiler-tests -- --bless` (planned).
6. **Diagnostics**: Use `RUST_LOG=debug` to inspect parser/type-checker tracing.

## Roadmap Highlights

- **Short Term**
  - Parser test harness covering all grammar productions
  - Semantic refinement enforcement with deterministic regressions
  - Capability-aware import resolver and diagnostic improvements

- **Medium Term**
  - HIR optimization passes (decision flattening, effect hoisting)
  - Wasm component emission with capability signatures and metadata
  - CLI integration with formatter and linting surfaces

- **Long Term**
  - Incremental compilation and caching
  - Multi-module builds and dependency graph resolution
  - Verified compilation paths for security-critical deployments

## References

- Specification: `docs/spec/overview.md`, `docs/spec/grammar.md`, `docs/spec/types.md`
- Effects & Runtime Contracts: `docs/spec/effects.md`, `docs/spec/runtime.md`
- Capability Model: `docs/spec/capabilities.md`, `docs/security/`
- Roadmap: `docs/spec/roadmap.dm`
- Contribution Guidelines: `CONTRIBUTING.md`

---

Maintainers should keep this README synchronized with the repository structure and roadmap milestones. Update it whenever new crates, workflows, or major capabilities are introduced.