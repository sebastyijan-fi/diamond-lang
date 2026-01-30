# Frontend Crate Guidance

## Purpose
The `packages/compiler/crates/frontend/` crate implements the lexical analysis and parsing phases of the Diamond compiler. This crate transforms raw `.dm` source text into a well-structured Abstract Syntax Tree (AST) that serves as the foundation for all downstream compilation phases. All implementation must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented language design, decision semantics (`<>`), and capability discipline.
- **`diamond2.md`** — Architectural feasibility, synthetic bootstrapping strategy, and zero-trust WebAssembly runtime.
- **`diamond3.md`** — Grammar specification, semantic typing, algebraic effects, and module-level capability injection rules.

The frontend is the first point of contact between Diamond source code and the compiler—correctness, performance, and error quality here cascade through the entire toolchain.

---

## Module Contract

| Module | Scope & Expectations |
| --- | --- |
| `lexer/` | Tokenization with layout-sensitive rules (indentation tracking, optional braces). |
| `parser/` | Recursive descent parser producing AST with error recovery. |
| `ast/` | AST node definitions, traversal traits, and visitor patterns. |
| `span/` | Source span representation, source maps, and location tracking. |
| `diagnostic/` | Parse-time diagnostic construction, error codes, and remediation hints. |
| `lib.rs` | Public API exports: `parse()`, `tokenize()`, and related entry points. |

---

## Grammar Implementation

The frontend must implement Diamond's hybrid layout-sensitive grammar as specified in `diamond3.md`:

### Lexical Rules

1. **Layout Sensitivity**
   - Track indentation levels for significant whitespace.
   - Support both indentation-based blocks and explicit braces.
   - Decision blocks (`<>`) encourage brace usage for clarity.
   - Maintain compatibility between layout modes within a file.

2. **Token Categories**
   - **Keywords**: `fn`, `let`, `if`, `else`, `match`, `effect`, `handler`, `perform`, `resume`, `import`, `export`, `requires`, `type`, `struct`, `enum`, `trait`, `impl`, etc.
   - **Operators**: Diamond operator `<>`, comparison `<`, `>`, `<=`, `>=`, `==`, `!=`, assignment `=`, arithmetic, logical, similarity `<~>`.
   - **Delimiters**: `()`, `[]` (generics), `{}`, `,`, `:`, `::`, `.`, `->`, `=>`.
   - **Literals**: Integers, floats, strings, booleans, unit `()`.
   - **Identifiers**: Standard identifier rules with capability-aware naming conventions.

3. **Comments**
   - Single-line: `//`
   - Multi-line: `/* ... */`
   - Documentation: `///` and `//!`

### Syntactic Constructs

1. **Module Structure**
   ```diamond
   // Capability-aware imports
   import std/net requires { Network }
   import std/fs requires { FileSystem(read) }
   
   // Exports
   export fn main() { ... }
   ```

2. **Generics with Square Brackets**
   ```diamond
   fn identity[T](x: T) -> T { x }
   type List[T] = ...
   ```

3. **Decision Operator**
   ```diamond
   let result = <> {
       option1 -> handle_option1(),
       option2 -> handle_option2(),
       _ -> fallback()
   }
   ```

4. **Effect Declarations and Handling**
   ```diamond
   effect Console {
       fn print(msg: String) -> ()
       fn read_line() -> String
   }
   
   fn greet() performs Console {
       perform Console.print("Hello!")
   }
   
   handler console_handler for Console {
       fn print(msg, resume) { ... }
       fn read_line(resume) { ... }
   }
   ```

---

## AST Design Principles

1. **Full Fidelity**
   - Preserve all source information including comments and whitespace positions.
   - Enable perfect round-trip formatting.
   - Store trivia (whitespace, comments) associated with tokens.

2. **Span Coverage**
   - Every AST node carries a `SourceSpan` for precise error reporting.
   - Spans reference byte offsets into the source file.
   - Support multi-span diagnostics (primary + secondary locations).

3. **Typed Nodes**
   - Use Rust enums for node variants.
   - Separate expression, statement, type, and pattern node hierarchies.
   - Enable exhaustive matching for analysis passes.

4. **Visitor Pattern**
   - Provide `Visitor` and `MutVisitor` traits.
   - Support both pre-order and post-order traversal.
   - Enable fold operations for transformations.

---

## Error Recovery

The parser must provide robust error recovery for IDE integration:

1. **Recovery Strategies**
   - Synchronize at statement boundaries on syntax errors.
   - Insert missing delimiters when inferable.
   - Skip malformed tokens while preserving structure.
   - Continue parsing to collect multiple errors.

2. **Error Quality**
   - Report primary location and context.
   - Suggest likely corrections ("did you mean...?").
   - Reference spec sections for complex syntax.
   - Provide stable error codes (E0001–E0999 range).

3. **Partial AST**
   - Return partial AST even when errors occur.
   - Mark error nodes for downstream phases to handle.
   - Enable language server to provide assistance mid-edit.

---

## Public API

### Core Entry Points

```rust
/// Parse Diamond source code into an AST.
pub fn parse(source: &str) -> ParseResult {
    ParseResult {
        ast: Option<Ast>,
        diagnostics: Vec<Diagnostic>,
    }
}

/// Tokenize Diamond source code.
pub fn tokenize(source: &str) -> TokenStream {
    // Returns iterator of tokens with spans
}

/// Parse a single expression (for REPL/eval).
pub fn parse_expr(source: &str) -> ParseResult<Expr> { ... }
```

### Type Definitions

```rust
pub struct Ast {
    pub module: Module,
    pub source_map: SourceMap,
}

pub struct Module {
    pub imports: Vec<Import>,
    pub items: Vec<Item>,
    pub span: SourceSpan,
}

pub struct SourceSpan {
    pub start: usize,
    pub end: usize,
    pub file_id: FileId,
}

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

---

## Testing Strategy

### Test Categories

| Category | Location | Purpose |
| --- | --- | --- |
| Unit Tests | `src/**/*.rs` | Test individual lexer/parser functions. |
| Golden Tests | `tests/golden/` | Snapshot AST output for known inputs. |
| Error Tests | `tests/errors/` | Validate diagnostic quality and recovery. |
| Fuzz Tests | `tests/fuzz/` | Property-based parser robustness. |

### Golden Test Format

```
tests/golden/
├── parse/
│   ├── expressions/
│   │   ├── literals.dm
│   │   ├── literals.ast.json
│   │   ├── binary_ops.dm
│   │   └── binary_ops.ast.json
│   ├── statements/
│   ├── modules/
│   └── effects/
└── lexer/
    ├── tokens/
    └── layout/
```

### Error Test Format

```
tests/errors/
├── E0001_unexpected_token.dm
├── E0001_unexpected_token.expected
├── E0042_unclosed_brace.dm
└── E0042_unclosed_brace.expected
```

---

## Performance Considerations

1. **String Interning**
   - Intern identifiers and keywords.
   - Use arena allocation for AST nodes.
   - Minimize allocations during lexing.

2. **Streaming**
   - Support lazy tokenization.
   - Enable incremental re-lexing for editor integration.
   - Cache lexer state at line boundaries.

3. **Benchmarks**
   - Track parse time per 1000 lines of code.
   - Benchmark common patterns (function definitions, expressions).
   - Maintain performance regression tests.

---

## Dependencies

Recommended crate dependencies:

- `logos` or `chumsky` — Lexer generation (or hand-rolled for performance).
- `rowan` — Lossless syntax trees (optional, for IDE quality).
- `smol_str` or `string-interner` — String interning.
- `miette` or `ariadne` — Diagnostic rendering (for CLI output).
- `serde` — AST serialization for golden tests.

---

## Review & Approval Matrix

| Change Type | Required Approvals |
| --- | --- |
| New syntax support | Language WG + RFC |
| Lexer modifications | Language WG |
| Parser error recovery | Language WG + DX WG |
| AST structure changes | Language WG (impacts downstream crates) |
| Performance optimizations | Language WG + benchmarks |

---

## Quality Checklist (Pre-Merge)

- [ ] Code follows `rustfmt` and passes `clippy` without warnings.
- [ ] All public items have doc comments with examples.
- [ ] Grammar implementation matches `diamond3.md` specification.
- [ ] Error messages are clear, actionable, and have stable codes.
- [ ] Error recovery produces usable partial ASTs.
- [ ] Golden tests updated for any AST changes.
- [ ] Fuzz tests pass without panics.
- [ ] Performance benchmarks show no regression.
- [ ] Source spans are accurate for all nodes.
- [ ] README reflects current module structure.

---

## Contribution Workflow

1. **Grammar Changes**
   - Draft RFC for new syntax.
   - Update `diamond3.md` specification first.
   - Implement lexer changes with tests.
   - Implement parser changes with golden tests.
   - Update downstream crates (HIR lowering).

2. **Error Improvements**
   - Add error test case demonstrating current behavior.
   - Improve diagnostic message and recovery.
   - Update expected output.
   - Verify IDE integration isn't regressed.

3. **Performance Work**
   - Establish baseline with `cargo bench`.
   - Implement optimization.
   - Verify no functionality regression.
   - Document complexity improvements.

---

## Future Enhancements

- Incremental parsing for editor responsiveness.
- Concrete Syntax Tree (CST) layer for perfect formatting.
- Macro expansion support (if Diamond adds macros).
- Tree-sitter grammar generation for editor highlighting.
- WebAssembly-compiled parser for browser-based tools.

---

The frontend crate is Diamond's gateway—transforming text into structure. Every token matters; every span must be precise. Build with the discipline that downstream phases and end users deserve.