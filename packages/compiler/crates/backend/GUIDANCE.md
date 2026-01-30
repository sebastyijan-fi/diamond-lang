# Backend Crate Guidance

## Purpose
The `packages/compiler/crates/backend/` crate is responsible for lowering Diamond's typed High-level Intermediate Representation (HIR) to WebAssembly Component Model artifacts. This crate embodies Diamond's promise of deterministic, capability-safe execution. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, WebAssembly Component Model integration, zero-trust runtime execution.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection rules.

---

## Scope & Responsibilities

### Code Generation
- Transform typed HIR nodes to Wasm instructions.
- Emit Wasm Component Model compliant binaries.
- Generate WIT (WebAssembly Interface Types) definitions for module interfaces.
- Produce source maps linking Wasm locations to Diamond source spans.

### Effect Compilation
- Emit trampolines for algebraic effect handlers.
- Generate continuation capture and restore sequences.
- Implement effect dispatch tables for runtime resolution.
- Encode effect signatures in component metadata.

### Capability Integration
- Embed capability manifests alongside Wasm components.
- Validate capability requirements are reflected in component imports.
- Generate capability check preambles for sensitive operations.
- Produce auditable capability dependency graphs.

### Optimization Passes
- Constant folding and propagation.
- Dead code elimination.
- Inlining of small functions (respecting effect boundaries).
- Effect specialization for statically-known handlers.
- Branch simplification for deterministic decision blocks.

---

## Directory Structure

```
backend/
├── Cargo.toml              # Crate manifest
├── README.md               # Architecture overview and API documentation
├── GUIDANCE.md             # This file
├── src/
│   ├── lib.rs              # Crate root, public API exports
│   ├── codegen/            # Core code generation logic
│   │   ├── mod.rs
│   │   ├── expr.rs         # Expression lowering
│   │   ├── stmt.rs         # Statement lowering
│   │   ├── func.rs         # Function compilation
│   │   ├── types.rs        # Type representation in Wasm
│   │   └── control.rs      # Control flow (branches, loops, decisions)
│   ├── effects/            # Effect handling compilation
│   │   ├── mod.rs
│   │   ├── handlers.rs     # Handler trampolines
│   │   ├── perform.rs      # Perform instruction emission
│   │   └── continuations.rs# Continuation capture/resume
│   ├── capabilities/       # Capability manifest generation
│   │   ├── mod.rs
│   │   ├── manifest.rs     # Capability descriptor output
│   │   └── validation.rs   # Pre-emission capability checks
│   ├── wasm/               # Wasm-specific utilities
│   │   ├── mod.rs
│   │   ├── component.rs    # Component model emission
│   │   ├── wit.rs          # WIT generation
│   │   └── encoding.rs     # Binary encoding helpers
│   ├── optimize/           # Optimization passes
│   │   ├── mod.rs
│   │   ├── constfold.rs    # Constant folding
│   │   ├── dce.rs          # Dead code elimination
│   │   ├── inline.rs       # Function inlining
│   │   └── effects.rs      # Effect specialization
│   └── debug/              # Debug information generation
│       ├── mod.rs
│       └── sourcemap.rs    # Source mapping
├── tests/                  # Integration tests
│   ├── codegen_tests.rs
│   ├── effects_tests.rs
│   └── optimization_tests.rs
└── benches/                # Performance benchmarks
    └── emission_bench.rs
```

---

## Public API

### Core Functions

```rust
/// Compile typed HIR to a Wasm component.
/// 
/// # Arguments
/// * `hir` - The typed high-level intermediate representation
/// * `options` - Compilation options (optimization level, debug info, etc.)
/// 
/// # Returns
/// * `Ok(WasmComponent)` - The compiled Wasm component with metadata
/// * `Err(Vec<Diagnostic>)` - Compilation errors
pub fn emit_wasm(hir: &TypedHir, options: &EmitOptions) -> Result<WasmComponent, Vec<Diagnostic>>;

/// Emit only the capability manifest without full compilation.
pub fn emit_manifest(hir: &TypedHir) -> Result<CapabilityManifest, Vec<Diagnostic>>;

/// Generate WIT definitions for module interfaces.
pub fn emit_wit(hir: &TypedHir) -> Result<String, Vec<Diagnostic>>;

/// Apply optimization passes to HIR before emission.
pub fn optimize(hir: TypedHir, level: OptimizationLevel) -> TypedHir;
```

### Types

```rust
pub struct WasmComponent {
    pub bytes: Vec<u8>,
    pub manifest: CapabilityManifest,
    pub wit: Option<String>,
    pub source_map: Option<SourceMap>,
    pub metadata: ComponentMetadata,
}

pub struct EmitOptions {
    pub optimization_level: OptimizationLevel,
    pub emit_debug_info: bool,
    pub emit_source_map: bool,
    pub emit_wit: bool,
    pub target: WasmTarget,
}

pub enum OptimizationLevel {
    None,
    Basic,
    Aggressive,
}

pub enum WasmTarget {
    Component,      // Full component model
    Core,           // Core Wasm module (limited features)
    Preview2,       // WASI Preview 2
}
```

---

## Coding Standards

1. **Wasm Correctness**
   - Validate all emitted Wasm with `wasmparser` before returning.
   - Use `wasm-encoder` for binary construction—avoid manual byte manipulation.
   - Test emission against `wasmtime` validation.
   - Ensure component model compliance with latest spec.

2. **Effect Handling**
   - Effect handlers must preserve call stack for debugging.
   - Continuation capture must be serializable (prepare for cold storage).
   - Document the ABI for handler trampolines.
   - Test handler resume paths thoroughly.

3. **Capability Safety**
   - Never emit code that bypasses capability requirements.
   - Fail compilation if capabilities cannot be statically verified.
   - Capability manifests must be cryptographically hashable.
   - Log all capability requirements during compilation for auditing.

4. **Error Handling**
   - Use `Result` types for all public functions.
   - Provide rich diagnostics with HIR/source locations.
   - Distinguish between user errors and internal compiler errors.
   - Include error codes from the E5000–E5999 range.

5. **Performance**
   - Benchmark emission time for realistic programs.
   - Avoid repeated allocations in hot loops.
   - Use arena allocation for temporary Wasm structures.
   - Profile and optimize the critical path.

---

## Testing Strategy

### Unit Tests
- Test individual codegen functions in isolation.
- Mock HIR inputs for specific language constructs.
- Validate correct Wasm instruction sequences.

### Golden Tests
- Compare emitted Wasm text format against expected snapshots.
- Cover all major language features.
- Update with `UPDATE_GOLDEN=1` when intentional changes occur.

### Integration Tests
- Compile full Diamond programs and validate output.
- Execute compiled Wasm with `wasmtime` to verify behavior.
- Test effect handlers and continuation resume.

### Fuzzing
- Fuzz the HIR→Wasm path with malformed inputs.
- Ensure graceful error handling without panics.
- Track code coverage for emission paths.

### Benchmark Suite
- Measure compilation time for various program sizes.
- Track Wasm binary size metrics.
- Compare optimization pass effectiveness.

---

## Dependencies

```toml
[dependencies]
# Wasm tooling
wasm-encoder = "0.x"      # Wasm binary construction
wasmparser = "0.x"        # Validation
wit-component = "0.x"     # Component model utilities

# Internal
diamond-hir = { path = "../hir" }

# Error handling
thiserror = "1.x"
miette = "7.x"

# Utilities
indexmap = "2.x"          # Deterministic iteration
bumpalo = "3.x"           # Arena allocation
```

---

## CI Integration

- All emitted Wasm must pass `wasmparser` validation.
- Golden tests run on every PR.
- Benchmark comparisons flag regressions > 10%.
- Fuzz tests run nightly with extended duration.

---

## Quality Checklist (Pre-Merge)

- [ ] All emitted Wasm validates with `wasmparser`.
- [ ] Effect handlers generate correct trampolines.
- [ ] Capability manifests accurately reflect requirements.
- [ ] Source maps correctly locate Wasm to Diamond source.
- [ ] Optimization passes preserve semantics.
- [ ] Error messages include HIR locations and remediation.
- [ ] No panics in library code; all errors use `Result`.
- [ ] Benchmarks show no unexpected regressions.
- [ ] Doc comments reference spec sections.
- [ ] Golden tests updated for emission format changes.

---

## Future Enhancements

- Streaming compilation for large modules.
- Parallel codegen for independent functions.
- Profile-guided optimization support.
- Debug info for native debuggers (DWARF-like).
- Wasm GC integration when stabilized.
- Custom optimization pass plugin system.

---

The backend crate is where Diamond's high-level semantics meet the metal of WebAssembly execution. Every instruction emitted must uphold the language's security guarantees while enabling performant, resumable agent workflows. Build with precision—this code runs in zero-trust environments.