# Compiler Package Guidance

## Purpose
The `packages/compiler/` workspace contains the Diamond language compiler—the core toolchain that transforms `.dm` source files into executable WebAssembly components. Every component must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented language design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection rules.

The compiler is the cornerstone of Diamond's promise: transforming probabilistic intent into deterministic, capability-safe execution.

---

## Directory Contract

| Path | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `crates/` | Language + Runtime | Rust workspace containing modular compiler crates. |
| `crates/frontend/` | Language | Lexer, parser, AST definitions, source diagnostics. |
| `crates/hir/` | Language + Runtime | High-level intermediate representation, type inference, effect inference. |
| `crates/backend/` | Runtime | Code generation, Wasm component emission, optimization passes. |
| `crates/cli/` | Developer Experience | Command-line interface, build orchestration, output modes. |
| `tests/` | All Compiler WGs | Golden tests, conformance suites, regression tests. |
| `README.md` | All WGs | Architecture overview, build instructions, contributor orientation. |
| `GUIDANCE.md` | All WGs | This file—localized contribution and quality standards. |
| `Cargo.toml` | Language + Runtime | Workspace manifest defining crate dependencies and features. |

Subdirectories must not be created without an owning working group, README, and guidance note.

---

## Architecture Overview

```
                    ┌─────────────┐
                    │   Source    │
                    │   (.dm)     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Frontend   │
                    │  (Lexer +   │
                    │   Parser)   │
                    └──────┬──────┘
                           │ AST
                    ┌──────▼──────┐
                    │    HIR      │
                    │  (Types +   │
                    │  Effects)   │
                    └──────┬──────┘
                           │ Typed HIR
                    ┌──────▼──────┐
                    │  Backend    │
                    │  (Wasm      │
                    │  Emission)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Wasm      │
                    │ Component   │
                    └─────────────┘
```

---

## Crate Responsibilities

### `frontend/`
- **Lexer**: Tokenize `.dm` source with layout-sensitive rules (indentation + optional braces).
- **Parser**: Produce concrete syntax tree, handle error recovery for IDE integration.
- **AST**: Define abstract syntax tree nodes, source spans, and diagnostic attachment points.
- **Diagnostics**: Emit structured errors with source locations, severity, and remediation hints.

### `hir/`
- **Lowering**: Transform AST to high-level intermediate representation.
- **Type Inference**: Implement bidirectional type inference with semantic refinement support.
- **Effect Inference**: Track algebraic effects, ensure capability requirements are explicit.
- **Name Resolution**: Resolve imports, handle module-level capability injection (`import ... requires { ... }`).
- **Semantic Analysis**: Validate decision operator usage, enforce capability discipline.

### `backend/`
- **Code Generation**: Emit Wasm component model artifacts.
- **Optimization**: Apply optimization passes (inlining, dead code elimination, effect specialization).
- **Capability Manifests**: Generate capability descriptors alongside Wasm binaries.
- **Debug Info**: Emit source maps and debug metadata for runtime introspection.

### `cli/`
- **Command Interface**: Parse arguments, orchestrate compilation pipeline.
- **Output Modes**: Support `--emit` flags (AST, HIR, Wasm, diagnostics).
- **Watch Mode**: File watching for incremental rebuilds (future).
- **Integration**: Hook into language server for IDE-driven compilation.

---

## Coding Standards

1. **Rust Conventions**
   - Follow `rustfmt` formatting; run `cargo fmt` before committing.
   - Enable `clippy` with `deny(warnings)`; address all lints.
   - Use `#[must_use]` for functions returning important values.
   - Prefer `Result` over panics; reserve panics for invariant violations.

2. **Error Handling**
   - Use structured diagnostic types with error codes.
   - Attach source spans to all diagnostics.
   - Provide actionable remediation hints.
   - Support error recovery for IDE-quality parsing.

3. **Documentation**
   - Write crate-level doc comments explaining purpose and architecture.
   - Document public APIs with examples.
   - Reference spec sections for semantic justifications.
   - Keep `README.md` in each crate up-to-date.

4. **Testing**
   - Unit tests for individual components.
   - Golden tests for parser output (AST snapshots).
   - Integration tests for full compilation pipeline.
   - Property-based tests for parser robustness.
   - Fuzz tests for security-critical paths.

5. **Performance**
   - Profile before optimizing; use `cargo flamegraph` or similar.
   - Benchmark critical paths (parsing, type inference, codegen).
   - Avoid allocations in hot paths where feasible.
   - Document performance characteristics.

---

## Build & Development

### Prerequisites
- Rust toolchain (stable, pinned version in `rust-toolchain.toml`).
- `wasm-tools` for Wasm component manipulation.
- `wasmtime` or equivalent for runtime testing.

### Common Commands
```bash
# Build all compiler crates
cargo build --workspace

# Run tests
cargo test --workspace

# Run with specific emit mode
cargo run -p diamond-cli -- compile input.dm --emit=ast

# Format code
cargo fmt --all

# Lint
cargo clippy --workspace -- -D warnings

# Generate documentation
cargo doc --workspace --no-deps --open
```

### Workspace Layout
The compiler uses a Cargo workspace defined in `packages/compiler/Cargo.toml`:

```toml
[workspace]
members = [
    "crates/frontend",
    "crates/hir",
    "crates/backend",
    "crates/cli",
]
resolver = "2"
```

---

## Testing Strategy

### Test Categories

| Category | Location | Purpose |
| --- | --- | --- |
| Unit Tests | `crates/*/src/**` | Test individual functions and modules. |
| Golden Tests | `tests/golden/` | Snapshot tests for parser, HIR, and Wasm output. |
| Conformance | `tests/conformance/` | Spec compliance validation. |
| Integration | `tests/integration/` | End-to-end compilation scenarios. |
| Fuzz | `tests/fuzz/` | Parser and type checker robustness. |

### Golden Test Workflow
1. Place `.dm` input in `tests/golden/input/`.
2. Run `cargo test` to generate or compare output.
3. Review diffs carefully before accepting changes.
4. Use `UPDATE_GOLDEN=1 cargo test` to regenerate baselines.

### Synthetic Corpus Validation
- Nightly CI validates against synthetic corpus from `scripts/bootstrap_corpus.py`.
- Track parse rate and type-check rate metrics.
- Failures are reported but non-blocking during bootstrap phase.

---

## Diagnostic Standards

Compiler diagnostics must be:

1. **Precise**: Pinpoint exact source location (file, line, column, span).
2. **Actionable**: Suggest specific fixes when possible.
3. **Consistent**: Use stable error codes for tooling integration.
4. **Accessible**: Write messages for humans, not just compiler authors.

### Diagnostic Structure
```rust
pub struct Diagnostic {
    pub code: DiagnosticCode,
    pub severity: Severity,
    pub message: String,
    pub span: SourceSpan,
    pub labels: Vec<Label>,
    pub notes: Vec<String>,
    pub suggestions: Vec<Suggestion>,
}
```

### Error Code Scheme
- `E0001–E0999`: Parse errors
- `E1000–E1999`: Name resolution errors
- `E2000–E2999`: Type errors
- `E3000–E3999`: Effect errors
- `E4000–E4999`: Capability errors
- `E5000–E5999`: Code generation errors

---

## Capability & Effect Integration

The compiler must enforce Diamond's security model:

1. **Capability Tracking**
   - Track required capabilities through the type system.
   - Validate `import ... requires { ... }` declarations.
   - Generate capability manifests as compilation artifacts.
   - Reject code that assumes ambient authority.

2. **Effect Inference**
   - Infer effect signatures for all functions.
   - Ensure `perform` calls match declared effects.
   - Track effect handlers and resumption points.
   - Validate continuation serialization boundaries.

3. **Decision Operator**
   - Parse and validate `<>` decision blocks.
   - Ensure branches are exhaustive or have defaults.
   - Track semantic routing metadata for runtime.

---

## Review & Approval Matrix

| Change Type | Required Approvals |
| --- | --- |
| Grammar or syntax changes | Language WG + RFC |
| Type system modifications | Language WG + Runtime WG |
| Effect semantics changes | Language WG + Runtime WG + RFC |
| Wasm emission changes | Runtime WG |
| CLI interface changes | Developer Experience WG |
| Diagnostic improvements | Language WG |
| Performance optimizations | Language WG + benchmarks |

---

## Quality Checklist (Pre-Merge)

- [ ] Code follows `rustfmt` and passes `clippy` with no warnings.
- [ ] All existing tests pass (`cargo test --workspace`).
- [ ] New functionality includes appropriate tests.
- [ ] Golden tests updated if output format changes.
- [ ] Diagnostics are clear, actionable, and have stable codes.
- [ ] Public APIs are documented with doc comments.
- [ ] Performance impact assessed for critical paths.
- [ ] Capability and effect implications documented.
- [ ] README and CHANGELOG updated as needed.
- [ ] RFC linked for significant semantic changes.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the change.
   - For grammar/semantic changes, draft an RFC first.
   - Identify affected crates and reviewers.

2. **Implementation**
   - Create a feature branch.
   - Make focused commits with conventional messages.
   - Add tests alongside implementation.
   - Update documentation as you go.

3. **Review**
   - Request reviews from appropriate working groups.
   - Address feedback promptly.
   - Ensure CI passes before merge.

4. **Post-Merge**
   - Monitor for regressions.
   - Update roadmap and milestone tracking.
   - Announce significant changes in changelog.

---

## Roadmap Alignment

The compiler development follows the project roadmap:

1. **Phase 1**: Lexer and parser with golden tests.
2. **Phase 2**: AST to HIR lowering, name resolution.
3. **Phase 3**: Type inference with semantic refinements.
4. **Phase 4**: Effect inference and capability validation.
5. **Phase 5**: Wasm component emission.
6. **Phase 6**: Optimization passes and production hardening.

Each phase requires conformance tests validating spec alignment.

---

## Future Enhancements

- Incremental compilation for fast iteration.
- Query-based architecture (salsa or similar) for IDE integration.
- Parallel compilation for large codebases.
- Plugin system for custom analyses and transforms.
- Self-hosting: compile the Diamond compiler in Diamond.

---

The compiler is Diamond's gateway from intent to execution. Every line of code should uphold the language's promise: secure, resumable, semantically precise agent engineering. Build with care, test thoroughly, and document generously.