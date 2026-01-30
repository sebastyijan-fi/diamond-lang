# Compiler Crates Workspace Guidance

## Purpose
The `packages/compiler/crates/` directory contains the modular Rust crates that comprise the Diamond compiler. This workspace follows a clean separation of concerns, enabling independent development, testing, and evolution of each compilation phase. All crates must remain aligned with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection rules.

---

## Directory Contract

| Crate | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `frontend/` | Language | Lexer, parser, AST construction, syntax error recovery, source mapping. |
| `hir/` | Language + Runtime | High-level Intermediate Representation, type checking, effect inference, semantic analysis. |
| `backend/` | Language + Runtime | HIR-to-Wasm lowering, code generation, optimization passes, component model emission. |
| `cli/` | Developer Experience | Command-line interface, driver orchestration, diagnostic formatting, build modes. |
| `GUIDANCE.md` | All WGs | This file; workspace-wide conventions and cross-crate standards. |

Additional utility crates may be added as needs emerge (e.g., `diagnostics/`, `symbols/`, `testing/`). Each new crate requires:
- An owning working group assignment.
- A local `README.md` documenting purpose and API surface.
- A local `GUIDANCE.md` (or reference to this parent guidance).

---

## Crate Organization Standards

### Cargo Workspace Configuration
```toml
# packages/compiler/Cargo.toml (workspace root)
[workspace]
members = ["crates/*"]
resolver = "2"

[workspace.package]
version = "0.1.0"
edition = "2021"
license = "Apache-2.0 OR MIT"
repository = "https://github.com/<org>/diamond"

[workspace.dependencies]
# Shared dependencies with version pinning
```

### Individual Crate Structure
```
<crate-name>/
├── Cargo.toml          # Crate manifest referencing workspace dependencies
├── README.md           # Purpose, architecture, public API overview
├── GUIDANCE.md         # Local contribution guidance (or defer to parent)
├── src/
│   ├── lib.rs          # Crate root, public API exports
│   └── ...             # Modular implementation files
├── tests/              # Integration tests
├── benches/            # Performance benchmarks (optional)
└── examples/           # Usage examples (optional)
```

---

## Cross-Crate Dependencies

The compiler crates follow a directed dependency graph:

```
cli
 └── backend
      └── hir
           └── frontend
```

- **frontend** has no internal compiler dependencies; it produces AST.
- **hir** depends on frontend; it transforms AST to typed HIR.
- **backend** depends on hir; it lowers HIR to Wasm.
- **cli** depends on all; it orchestrates the pipeline.

Avoid circular dependencies. Shared utilities should be factored into separate crates or the workspace root.

---

## Coding Standards

1. **Rust Idioms**
   - Follow `rustfmt` formatting (enforced in CI).
   - Enable `#![deny(warnings)]` and comprehensive `clippy` lints.
   - Use `thiserror` for error types; `miette` or similar for rich diagnostics.
   - Prefer `&str` and borrowed types in public APIs where ownership isn't required.

2. **Documentation**
   - Every public item must have doc comments with examples where applicable.
   - Reference spec sections: `/// See diamond3.md §5.2 for grammar rules`.
   - Maintain `README.md` with architecture diagrams and module overview.

3. **Error Handling**
   - Use `Result` types pervasively; avoid panics in library code.
   - Diagnostics should include source spans, error codes, and remediation hints.
   - Integrate with language server diagnostic protocol for consistent messaging.

4. **Testing Strategy**
   - **Unit tests**: In-module `#[cfg(test)]` for internal logic.
   - **Integration tests**: In `tests/` directory for cross-module behavior.
   - **Golden tests**: Snapshot comparisons for parser output, HIR dumps, Wasm emission.
   - **Fuzz tests**: Property-based testing for parser robustness and type checker soundness.

5. **Performance**
   - Profile before optimizing; use `criterion` benchmarks in `benches/`.
   - Cache expensive computations (interned strings, type IDs).
   - Document complexity expectations for critical algorithms.

---

## Crate-Specific Expectations

### `frontend/`
- Implements layout-sensitive lexer supporting both indentation and brace modes.
- Parser handles Diamond grammar including:
  - Square-bracket generics `Type[T]`
  - Diamond operator `<>` for decisions
  - Effect declarations and `perform` expressions
  - Module-level capability imports
- Produces well-structured AST with full source span information.
- Provides robust error recovery for IDE integration.
- Exports `parse()` function returning `Result<Ast, Vec<Diagnostic>>`.

### `hir/`
- Transforms AST to High-level Intermediate Representation.
- Performs semantic analysis:
  - Name resolution and scope tracking
  - Type inference and checking
  - Effect inference and capability validation
  - Semantic type refinement verification
- Maintains symbol tables and type environments.
- Exports `lower_to_hir()` and `type_check()` functions.

### `backend/`
- Lowers typed HIR to WebAssembly Component Model.
- Implements code generation for:
  - Core Wasm instructions
  - Effect handler trampolines
  - Continuation capture/restore
  - Capability manifest embedding
- Provides optimization passes (constant folding, dead code elimination).
- Exports `emit_wasm()` returning component bytes.

### `cli/`
- Provides `diamondc` command-line interface.
- Supports subcommands: `build`, `check`, `emit`, `fmt`, `version`.
- Implements `--emit` modes: `ast`, `hir`, `wasm`, `wasm-text`.
- Formats diagnostics for terminal (colors, source snippets).
- Integrates with build caching and incremental compilation (future).

---

## Development Workflow

1. **Setup**
   ```bash
   cd packages/compiler
   cargo build --workspace
   cargo test --workspace
   cargo clippy --workspace -- -D warnings
   ```

2. **Adding a New Crate**
   - Create directory under `crates/`.
   - Add to workspace `members` in root `Cargo.toml`.
   - Create `README.md` and `GUIDANCE.md`.
   - Define public API in `src/lib.rs`.
   - Add integration points with existing crates.

3. **Testing Changes**
   - Run unit tests: `cargo test -p <crate-name>`
   - Run integration tests: `cargo test -p <crate-name> --test '*'`
   - Update golden files: `UPDATE_EXPECT=1 cargo test`
   - Benchmark: `cargo bench -p <crate-name>`

4. **Documentation**
   - Generate docs: `cargo doc --workspace --no-deps --open`
   - Ensure all public items are documented.
   - Update README files for significant changes.

---

## CI Integration

The compiler crates integrate with repository CI:

- **Format check**: `cargo fmt --check`
- **Lint check**: `cargo clippy -- -D warnings`
- **Test suite**: `cargo test --workspace`
- **Doc build**: `cargo doc --workspace --no-deps`
- **Benchmark regression**: Compare against baseline metrics

Golden test artifacts are stored in `packages/compiler/tests/` and validated nightly against the synthetic corpus.

---

## Quality Checklist (Pre-Merge)

- [ ] Code follows `rustfmt` and passes `clippy` without warnings.
- [ ] All public items have doc comments with spec references.
- [ ] Unit and integration tests cover new functionality.
- [ ] Golden tests updated for parser/HIR/Wasm output changes.
- [ ] Error messages include spans, codes, and remediation hints.
- [ ] No panics in library code; all errors use `Result`.
- [ ] Performance-sensitive code has benchmarks.
- [ ] README/GUIDANCE updated for architectural changes.
- [ ] Changelog entry added for user-facing changes.

---

## Future Enhancements

- Incremental compilation support with dependency tracking.
- Parallel compilation for independent modules.
- Query-based architecture (salsa-style) for IDE responsiveness.
- Debug info emission for source-level debugging.
- Profile-guided optimization integration.
- Plugin architecture for custom optimization passes.

---

The `crates/` workspace is the heart of Diamond's compilation pipeline. Maintain rigorous standards to ensure the compiler is correct, performant, and aligned with the language's crystalline vision.