# Compiler Tests Guidance

## Purpose
The `packages/compiler/tests/` directory houses the comprehensive test suites that validate the Diamond compiler's correctness, performance, and conformance to the language specification. All tests must verify behavior aligned with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection rules.

Testing is the guardian of Diamond's crystalline promise—every test validates that source intent becomes correct, secure execution.

---

## Directory Structure

```
tests/
├── GUIDANCE.md             # This file
├── README.md               # Test suite overview, running instructions
├── golden/                 # Snapshot-based golden tests
│   ├── parse/              # Parser output snapshots
│   │   ├── expressions/    # Expression parsing tests
│   │   ├── statements/     # Statement parsing tests
│   │   ├── declarations/   # Declaration parsing tests
│   │   ├── modules/        # Module-level parsing tests
│   │   └── effects/        # Effect declaration parsing tests
│   ├── hir/                # HIR lowering snapshots
│   │   ├── types/          # Type inference snapshots
│   │   ├── effects/        # Effect inference snapshots
│   │   └── capabilities/   # Capability validation snapshots
│   └── wasm/               # Wasm emission snapshots
│       ├── text/           # Wasm text format (.wat) output
│       └── component/      # Component model output
├── conformance/            # Specification conformance tests
│   ├── grammar/            # Grammar rule validation
│   ├── types/              # Type system conformance
│   ├── effects/            # Effect system conformance
│   ├── capabilities/       # Capability model conformance
│   └── decisions/          # Diamond operator conformance
├── errors/                 # Error message quality tests
│   ├── parse/              # Parse error tests
│   ├── type/               # Type error tests
│   ├── effect/             # Effect error tests
│   └── capability/         # Capability error tests
├── integration/            # End-to-end compilation tests
│   ├── compile_run/        # Compile and execute tests
│   ├── multi_module/       # Multi-module compilation tests
│   └── stdlib/             # Standard library integration tests
├── fuzz/                   # Fuzz testing configurations
│   ├── parser/             # Parser robustness fuzzing
│   └── typechecker/        # Type checker fuzzing
├── corpus/                 # Test input corpus
│   ├── valid/              # Valid Diamond programs
│   └── invalid/            # Programs expected to fail
├── fixtures/               # Shared test fixtures
│   ├── modules/            # Reusable module fixtures
│   └── configs/            # Test configuration fixtures
└── harness/                # Test harness utilities
    ├── mod.rs              # Test harness library
    ├── golden.rs           # Golden test helpers
    └── runtime.rs          # Wasm execution helpers
```

---

## Test Categories

### Golden Tests
Snapshot-based tests comparing compiler output against expected baselines.

**Workflow:**
1. Place `.dm` input files in the appropriate category folder.
2. Run tests: `cargo test -p diamond-tests`.
3. On first run, baselines are generated (or use `UPDATE_GOLDEN=1`).
4. Subsequent runs compare output to baselines.
5. Review diffs carefully before updating baselines.

**Naming Convention:**
```
<feature>_<variant>.dm           # Input file
<feature>_<variant>.ast.json     # AST snapshot
<feature>_<variant>.hir.json     # HIR snapshot
<feature>_<variant>.wat          # Wasm text output
```

**Example:**
```
golden/parse/expressions/
├── binary_ops.dm
├── binary_ops.ast.json
├── function_call.dm
├── function_call.ast.json
├── decision_block.dm
└── decision_block.ast.json
```

### Conformance Tests
Validate that the compiler correctly implements the Diamond specification.

**Structure:**
Each conformance test includes:
- A `.dm` file with the test code.
- A `.expected` file describing expected behavior.
- An optional `.flags` file with compiler flags.

**Categories:**
- **Grammar**: Test each syntactic construct from `diamond3.md`.
- **Types**: Validate type inference and checking rules.
- **Effects**: Verify effect tracking and handler semantics.
- **Capabilities**: Test capability propagation and validation.
- **Decisions**: Validate Diamond operator (`<>`) semantics.

### Error Tests
Validate diagnostic quality for error conditions.

**Structure:**
```
<error_code>_<description>.dm        # Code that triggers the error
<error_code>_<description>.expected  # Expected diagnostic output
```

**Expected Format:**
```
error[E2001]: type mismatch
  --> <path>:15:10
   |
15 |     let x: Int = "hello"
   |                  ^^^^^^^
   |                  expected `Int`, found `String`
```

### Integration Tests
End-to-end tests that compile and optionally execute Diamond programs.

**Categories:**
- **compile_run**: Compile to Wasm and execute, validating output.
- **multi_module**: Test cross-module compilation and linking.
- **stdlib**: Test standard library integration.

**Test Harness Features:**
- Compile Diamond source to Wasm component.
- Execute with `wasmtime` runtime.
- Capture stdout/stderr for validation.
- Mock capability providers for testing.

### Fuzz Tests
Property-based and fuzz testing for robustness.

**Goals:**
- No panics on any input (graceful error handling).
- Memory safety (no crashes, leaks, or undefined behavior).
- Deterministic output (same input → same output).

**Tools:**
- `cargo-fuzz` for coverage-guided fuzzing.
- `proptest` for property-based testing.
- AFL++ integration for extended fuzzing campaigns.

---

## Test Writing Standards

### General Guidelines

1. **One Test, One Concern**: Each test file should validate a single language feature or behavior.

2. **Descriptive Naming**: Use names that describe what's being tested, not how.
   ```
   Good: generic_type_inference_with_constraints.dm
   Bad:  test1.dm, complex_test.dm
   ```

3. **Spec References**: Include comments referencing the relevant spec sections.
   ```diamond
   // Test: diamond3.md §4.3 - Type compatibility rules
   // Validates that String is not assignable to Int
   ```

4. **Minimal Examples**: Keep test inputs as small as possible while covering the case.

5. **Comments**: Explain non-obvious expected behaviors.

### Golden Test Guidelines

1. **Stability**: Golden tests should be stable across runs. Avoid timestamps, random values, or environment-dependent output.

2. **Human-Readable**: Use JSON with pretty-printing for AST/HIR snapshots. Use `.wat` text format for Wasm.

3. **Selective Snapshots**: Only snapshot the relevant portion of output. Filter out noise.

4. **Update Discipline**: Review all golden changes in PRs. Unexplained changes indicate bugs.

### Error Test Guidelines

1. **Error Codes**: Use stable error codes (E0001, E2001, etc.) for machine-readable matching.

2. **Span Accuracy**: Verify error spans point to the exact problematic location.

3. **Message Quality**: Error messages should be actionable and understandable.

4. **Recovery**: After an error, the compiler should continue and report additional errors if possible.

### Integration Test Guidelines

1. **Isolation**: Each test should be independent. No shared mutable state.

2. **Determinism**: Tests must produce the same result on every run.

3. **Timeouts**: Set reasonable timeouts for Wasm execution tests.

4. **Cleanup**: Clean up generated artifacts after test completion.

---

## Running Tests

### Basic Commands

```bash
# Run all compiler tests
cargo test -p diamond-tests

# Run specific test category
cargo test -p diamond-tests golden
cargo test -p diamond-tests conformance
cargo test -p diamond-tests error
cargo test -p diamond-tests integration

# Run with verbose output
cargo test -p diamond-tests -- --nocapture

# Update golden baselines
UPDATE_GOLDEN=1 cargo test -p diamond-tests golden

# Run fuzz tests (requires nightly)
cargo +nightly fuzz run parser_fuzz
```

### Filtering

```bash
# Run tests matching a pattern
cargo test -p diamond-tests binary_ops
cargo test -p diamond-tests "E2001"

# Run tests in a specific file
cargo test -p diamond-tests --test golden_parse
```

### CI Integration

Tests run in CI with the following configuration:
- All test categories run on every PR.
- Golden test changes require explicit approval.
- Fuzz tests run nightly with extended duration.
- Coverage reports are generated and tracked.

---

## Test Harness API

### Golden Test Helpers

```rust
use diamond_tests::golden::{assert_golden, update_golden};

#[test]
fn test_parse_expression() {
    let input = include_str!("golden/parse/expressions/binary_ops.dm");
    let ast = frontend::parse(input).expect("parse failed");
    
    assert_golden!("parse/expressions/binary_ops.ast.json", ast);
}
```

### Error Test Helpers

```rust
use diamond_tests::errors::{expect_error, ErrorMatcher};

#[test]
fn test_type_mismatch() {
    let input = include_str!("errors/type/E2001_type_mismatch.dm");
    let result = compiler::compile(input);
    
    expect_error(result, ErrorMatcher {
        code: "E2001",
        message_contains: "type mismatch",
        span_line: 15,
    });
}
```

### Integration Test Helpers

```rust
use diamond_tests::integration::{compile_and_run, WasmOutput};

#[test]
fn test_hello_world() {
    let output = compile_and_run("integration/compile_run/hello_world.dm");
    
    assert_eq!(output.stdout, "Hello, Diamond!\n");
    assert!(output.stderr.is_empty());
    assert_eq!(output.exit_code, 0);
}
```

---

## Corpus Management

### Valid Programs Corpus
The `corpus/valid/` directory contains well-formed Diamond programs for:
- Parser validation
- Type checker validation
- Compilation success testing
- Performance benchmarking

### Invalid Programs Corpus
The `corpus/invalid/` directory contains malformed programs for:
- Error handling validation
- Recovery testing
- Diagnostic quality assessment

### Synthetic Corpus Integration
Nightly CI jobs:
1. Generate synthetic corpus using `scripts/bootstrap_corpus.py`.
2. Run compiler against generated programs.
3. Track parse rate, type-check rate, and compilation rate.
4. Report metrics and failures.

---

## Adding New Tests

### Checklist

- [ ] Test file follows naming conventions.
- [ ] Spec reference included in comments.
- [ ] Test is minimal and focused on one concern.
- [ ] Golden baselines reviewed and committed.
- [ ] Test runs successfully in CI.
- [ ] README updated if adding new test category.

### Example: Adding a Golden Test

1. Create input file:
   ```bash
   echo 'let x = 1 + 2' > golden/parse/expressions/simple_add.dm
   ```

2. Run to generate baseline:
   ```bash
   UPDATE_GOLDEN=1 cargo test -p diamond-tests simple_add
   ```

3. Review and commit baseline:
   ```bash
   git diff golden/parse/expressions/simple_add.ast.json
   git add golden/parse/expressions/simple_add.*
   git commit -m "test: add simple addition parsing test"
   ```

### Example: Adding an Error Test

1. Create test input that triggers the error:
   ```bash
   cat > errors/type/E2001_string_to_int.dm << 'EOF'
   // Test: E2001 - Type mismatch assigning String to Int
   fn main() {
       let x: Int = "hello"
   }
   EOF
   ```

2. Create expected output:
   ```bash
   cargo run -p diamond-cli -- check errors/type/E2001_string_to_int.dm 2>&1 \
     > errors/type/E2001_string_to_int.expected
   ```

3. Review and commit.

---

## Quality Metrics

### Coverage Targets
- Statement coverage: > 80%
- Branch coverage: > 70%
- Parser grammar rule coverage: 100%
- Error code coverage: 100% of defined codes

### Performance Baselines
- Parser throughput: > 10,000 lines/second
- Type checker throughput: > 5,000 lines/second
- Full compilation: < 100ms for typical module

### Tracked Metrics
- Number of tests by category
- Test execution time
- Golden test stability (churn rate)
- Fuzz test coverage growth

---

## Future Enhancements

- Mutation testing for test quality assessment.
- Visual diff tool for golden test updates.
- Parallel test execution for faster CI.
- Property-based test generation from grammar.
- Test case minimization for failure debugging.
- Cross-platform test matrix (Linux, macOS, Windows).

---

The test suite is Diamond's quality guarantee. Every test written today prevents a bug tomorrow. Invest in comprehensive, maintainable tests that clearly communicate expected behavior and catch regressions early.