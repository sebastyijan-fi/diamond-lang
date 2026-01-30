# Transpiler Guidance

## Purpose
The `packages/tooling/transpiler/` directory implements the Python-to-Diamond transpiler—a critical component of Diamond's synthetic bootstrapping strategy. This tool converts Python source code into equivalent Diamond `.dm` code, enabling the generation of a synthetic training corpus for LLM enablement and providing a migration path for existing codebases. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and agentic philosophy.
- **`diamond2.md`** — Synthetic bootstrapping strategy, transpiler architecture, and ML enablement pipelines.
- **`diamond3.md`** — Grammar specification, semantic typing, and module-level capability injection.

The transpiler is foundational to Diamond's bootstrap problem—providing the initial corpus that enables LLMs to learn Diamond syntax and semantics.

---

## Directory Structure

```
transpiler/
├── README.md               # Tool documentation, usage guide
├── GUIDANCE.md             # This file
├── pyproject.toml          # Python package manifest
├── src/
│   └── diamond_transpiler/
│       ├── __init__.py     # Package root
│       ├── cli.py          # Command-line interface
│       ├── parser.py       # Python AST parsing
│       ├── analyzer.py     # Semantic analysis of Python code
│       ├── mapper.py       # Python → Diamond construct mapping
│       ├── emitter.py      # Diamond code emission
│       ├── effects.py      # Effect inference from Python patterns
│       ├── capabilities.py # Capability inference from imports
│       └── config.py       # Configuration handling
├── tests/
│   ├── test_parser.py
│   ├── test_mapper.py
│   ├── test_emitter.py
│   ├── golden/             # Golden tests (input/output pairs)
│   └── fixtures/           # Test fixtures
├── examples/
│   ├── simple_function.py
│   ├── simple_function.dm
│   ├── class_to_struct.py
│   └── class_to_struct.dm
└── docs/
    ├── supported_patterns.md
    ├── limitations.md
    └── migration_guide.md
```

---

## Scope & Responsibilities

### Supported Python Subset

The transpiler targets a pragmatic subset of Python:

| Category | Supported | Notes |
| --- | --- | --- |
| Functions | ✓ | Typed annotations preferred |
| Classes | Partial | Dataclasses → structs, methods → functions |
| Type hints | ✓ | Primary source of type information |
| Control flow | ✓ | if/else, for, while, match |
| Comprehensions | ✓ | List, dict, set comprehensions |
| Generators | Partial | Simple generators → iterators |
| Async/await | Partial | Maps to effect-based patterns |
| Decorators | Partial | Common patterns recognized |
| Imports | ✓ | Maps to Diamond imports with capabilities |
| Exceptions | Partial | Try/except → Result types |

### Unsupported Patterns

- Dynamic typing without hints
- Metaclasses and complex inheritance
- Runtime code generation
- Global mutable state
- Monkey patching
- Most magic methods (`__getattr__`, etc.)

---

## Architecture

### Pipeline Stages

```
Python Source
     │
     ▼
┌─────────────┐
│   Parser    │ ─── Python AST (stdlib ast module)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Analyzer   │ ─── Semantic model (types, effects, capabilities)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│   Mapper    │ ─── Diamond IR (intermediate representation)
└─────┬───────┘
      │
      ▼
┌─────────────┐
│  Emitter    │ ─── Diamond source code (.dm)
└─────────────┘
```

### Key Components

#### Parser (`parser.py`)
- Uses Python's `ast` module for parsing.
- Extracts type annotations from function signatures.
- Collects import statements for capability inference.
- Handles docstrings and comments for preservation.

#### Analyzer (`analyzer.py`)
- Builds semantic model from AST.
- Infers types where annotations are missing (best effort).
- Identifies patterns (I/O, network, file access) for effect mapping.
- Tracks scope and variable bindings.

#### Mapper (`mapper.py`)
- Converts Python constructs to Diamond IR.
- Handles construct-level translation decisions.
- Applies naming convention transformations.
- Generates capability requirements from imports.

#### Emitter (`emitter.py`)
- Produces well-formatted Diamond source code.
- Respects Diamond's layout-sensitive grammar.
- Preserves comments and documentation.
- Applies consistent indentation and style.

---

## Translation Rules

### Functions

```python
# Python
def greet(name: str, times: int = 1) -> str:
    """Greet someone multiple times."""
    return (name + "! ") * times
```

```diamond
/// Greet someone multiple times.
fn greet(name: String, times: Int = 1) -> String {
    (name + "! ").repeat(times)
}
```

### Classes to Structs

```python
# Python
@dataclass
class User:
    name: str
    email: str
    age: int = 0
```

```diamond
struct User {
    name: String,
    email: String,
    age: Int = 0,
}
```

### Imports and Capabilities

```python
# Python
import requests
from pathlib import Path
```

```diamond
import std/net requires { Network }
import std/fs requires { FileSystem }
```

### Async to Effects

```python
# Python
async def fetch_data(url: str) -> dict:
    response = await httpx.get(url)
    return response.json()
```

```diamond
fn fetch_data(url: String) -> Map[String, Value] performs Network {
    let response = perform Network.fetch(url)
    response.json()
}
```

### Exception Handling

```python
# Python
try:
    result = risky_operation()
except ValueError as e:
    result = default_value
```

```diamond
let result = match risky_operation() {
    Ok(value) -> value,
    Err(e) -> default_value,
}
```

---

## CLI Interface

```
diamond-transpile [OPTIONS] <INPUT> [OUTPUT]

Arguments:
  <INPUT>   Python source file or directory
  [OUTPUT]  Output file or directory (default: stdout / parallel structure)

Options:
  --config <FILE>       Configuration file path
  --format              Format output Diamond code
  --preserve-comments   Preserve Python comments as Diamond comments
  --infer-types         Attempt type inference for untyped code
  --infer-effects       Infer effects from I/O patterns
  --strict              Fail on unsupported patterns
  --lenient             Skip unsupported patterns with warnings
  --dry-run             Show what would be generated without writing
  --stats               Print transpilation statistics
  -v, --verbose         Verbose output
  -h, --help            Print help
  -V, --version         Print version
```

---

## Configuration

```toml
# diamond-transpile.toml

[transpiler]
# How to handle unsupported patterns
unsupported_handling = "warn"  # "error", "warn", "skip"

# Type inference settings
infer_types = true
default_int_type = "Int"
default_float_type = "Float"

# Effect inference
infer_effects = true
io_patterns = ["print", "input", "open", "read", "write"]
network_patterns = ["requests", "httpx", "aiohttp", "urllib"]

# Output formatting
indent_style = "spaces"
indent_width = 4
max_line_length = 100

[capability_mapping]
# Map Python imports to Diamond capabilities
"requests" = "Network"
"httpx" = "Network"
"pathlib" = "FileSystem"
"os" = "FileSystem"
"random" = "Random"
"datetime" = "Time"

[type_mapping]
# Custom type mappings
"str" = "String"
"int" = "Int"
"float" = "Float"
"bool" = "Bool"
"list" = "List"
"dict" = "Map"
"None" = "()"
```

---

## Quality Metrics

### Target Metrics

| Metric | Target | Description |
| --- | --- | --- |
| Parse Rate | > 95% | Percentage of Python files successfully parsed |
| Translation Rate | > 80% | Percentage of parsed files with valid Diamond output |
| Type Coverage | > 70% | Percentage of values with inferred/declared types |
| Effect Coverage | > 60% | Percentage of I/O operations mapped to effects |

### Validation

1. **Syntax Validation**: Output must be valid Diamond syntax.
2. **Type Consistency**: Emitted types must be internally consistent.
3. **Effect Completeness**: All I/O must be wrapped in effects.
4. **Capability Accuracy**: Required capabilities must match operations.

---

## Testing Strategy

### Unit Tests
- Test each pipeline stage independently.
- Cover all supported Python constructs.
- Verify error handling for unsupported patterns.

### Golden Tests
Store input/output pairs in `tests/golden/`:

```
tests/golden/
├── functions/
│   ├── simple_function.py
│   ├── simple_function.dm
│   ├── default_args.py
│   ├── default_args.dm
│   └── ...
├── classes/
├── control_flow/
├── imports/
└── effects/
```

Run golden tests:
```bash
pytest tests/ -k golden
```

Update golden baselines:
```bash
UPDATE_GOLDEN=1 pytest tests/ -k golden
```

### Integration Tests
- Transpile real-world Python libraries.
- Validate output compiles with Diamond compiler (once available).
- Track metrics across test corpus.

---

## Corpus Generation Pipeline

The transpiler integrates with the synthetic corpus pipeline:

```bash
# Generate synthetic corpus from Python sources
python scripts/bootstrap_corpus.py \
    --source /path/to/python/code \
    --output corpus/synthetic/ \
    --config diamond-transpile.toml \
    --validate
```

### Pipeline Integration Points

1. **Input Sources**: Curated Python code (libraries, examples).
2. **Transpiler**: Converts to Diamond.
3. **Validation**: Check syntax with Diamond parser.
4. **Quality Filtering**: Filter low-quality translations.
5. **LLM Evolution**: Use LLM to improve translations.
6. **Corpus Output**: Store validated Diamond examples.

---

## Coding Standards

1. **Python Style**: Follow PEP 8, use type hints throughout.
2. **Documentation**: Docstrings for all public functions and classes.
3. **Error Handling**: Use explicit exceptions with descriptive messages.
4. **Testing**: Minimum 80% code coverage.
5. **Logging**: Use structured logging for debugging.

---

## Dependencies

```toml
[project]
dependencies = [
    "click>=8.0",           # CLI framework
    "rich>=13.0",           # Rich terminal output
    "pydantic>=2.0",        # Configuration validation
    "libcst>=1.0",          # Concrete syntax tree (optional)
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]
```

---

## Quality Checklist (Pre-Merge)

- [ ] All pipeline stages have unit tests.
- [ ] Golden tests cover all supported constructs.
- [ ] CLI provides helpful error messages.
- [ ] Configuration is validated and documented.
- [ ] Unsupported patterns produce clear warnings.
- [ ] Output is well-formatted Diamond code.
- [ ] Documentation includes examples and limitations.
- [ ] Metrics are tracked and reported.
- [ ] Integration with corpus pipeline tested.
- [ ] No regressions in translation quality.

---

## Future Enhancements

- Bidirectional transpilation (Diamond → Python for interop).
- IDE integration for live Python-to-Diamond preview.
- Support for more Python patterns (decorators, context managers).
- Machine learning-assisted translation improvements.
- Multi-language support (TypeScript, Go, Rust subsets).
- Incremental transpilation for large codebases.

---

The transpiler is Diamond's bridge from existing ecosystems. Every translation should preserve intent, respect Diamond's safety guarantees, and produce idiomatic code. Build a tool that makes migration to Diamond approachable and the resulting code excellent.