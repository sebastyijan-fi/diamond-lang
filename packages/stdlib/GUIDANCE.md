# Standard Library Package Guidance

## Purpose
The `packages/stdlib/` workspace contains Diamond's curated standard library—the foundational modules that ship with every Diamond installation. These modules provide essential functionality for agent development while exemplifying Diamond's capability-first, effect-aware design philosophy. All implementations must align with the foundational manuscripts:

- **`diamond.md`** — Intent-oriented design, capability discipline, and agentic abstractions.
- **`diamond2.md`** — Architectural feasibility, zero-trust execution, and synthetic bootstrapping.
- **`diamond3.md`** — Grammar, semantic typing, algebraic effects, and module-level capability injection.

The standard library is Diamond's showcase—demonstrating best practices for secure, resumable, semantically-typed agent code.

---

## Directory Contract

| Path | Owner Working Groups | Scope & Expectations |
| --- | --- | --- |
| `std-agent/` | Language + Runtime | Core agent primitives, decision utilities, prompt abstractions. |
| `std-memory/` | Runtime | Memory management, caching, persistence abstractions. |
| `std-unit/` | Language | Unit types, refinement primitives, semantic type utilities. |
| `std-io/` | Runtime (planned) | Console, file system, network I/O abstractions. |
| `std-time/` | Runtime (planned) | Time, duration, scheduling utilities. |
| `std-collections/` | Language (planned) | Data structures: lists, maps, sets, queues. |
| `std-text/` | Language (planned) | String manipulation, formatting, parsing. |
| `std-json/` | Language (planned) | JSON encoding/decoding with semantic types. |
| `std-crypto/` | Security (planned) | Cryptographic primitives, hashing, signing. |
| `README.md` | All WGs | Library overview, module index, usage guide. |
| `GUIDANCE.md` | All WGs | This file—contribution and quality standards. |

Each module must have:
- A `README.md` documenting purpose, API, and capability requirements.
- A `GUIDANCE.md` (or reference to this parent guidance).
- Explicit capability manifests (`capabilities.toml`).
- Comprehensive tests (unit, property, integration).
- Examples demonstrating idiomatic usage.

---

## Module Design Principles

### 1. Capability-First Design
Every module must:
- Declare required capabilities in module imports.
- Document capability requirements in the README.
- Provide capability-minimal alternatives where possible.
- Never assume ambient authority.

```diamond
// Example: std-io module with explicit capability
import std/io requires { FileSystem, Network }

// Or with attenuated capabilities
import std/io requires { FileSystem(read) }
```

### 2. Effect-Aware APIs
Standard library functions that perform side effects must:
- Use algebraic effects via `perform`.
- Document which effects are performed.
- Support handler customization for testing.
- Enable resumable operation where semantically meaningful.

```diamond
// Effect-aware file reading
fn read_file(path: String) -> String performs FileSystem {
    perform FileSystem.read(path)
}

// Pure alternative when possible
fn parse_config(content: String) -> Config {
    // Pure parsing logic, no effects
}
```

### 3. Semantic Type Richness
Leverage Diamond's semantic type system:
- Use refinement types for validated data.
- Provide typed newtypes for domain concepts.
- Document semantic constraints in types.

```diamond
// Semantic types in std-unit
type Email = String where { valid_email }
type Url = String where { valid_url }
type PositiveInt = Int where { > 0 }
type Percentage = Float where { >= 0.0, <= 100.0 }
```

### 4. Decision Operator Integration
For modules supporting agent workflows:
- Provide utilities for structured decision-making.
- Support the Diamond operator (`<>`) patterns.
- Document decision semantics and routing behavior.

---

## Module Structure

Each standard library module follows this layout:

```
std-<name>/
├── README.md               # Module documentation
├── GUIDANCE.md             # Local guidance (or defer to parent)
├── capabilities.toml       # Required capability declarations
├── src/
│   ├── lib.dm              # Module root, public exports
│   ├── types.dm            # Type definitions
│   ├── functions.dm        # Function implementations
│   └── effects.dm          # Effect declarations (if applicable)
├── tests/
│   ├── unit/               # Unit tests
│   ├── property/           # Property-based tests
│   └── integration/        # Integration tests
├── examples/
│   └── *.dm                # Usage examples
└── benches/
    └── *.dm                # Performance benchmarks
```

---

## Stability Levels

Each module and API declares its stability level:

| Level | Meaning | Commitment |
| --- | --- | --- |
| `unstable` | Experimental, may change or be removed | No compatibility guarantees |
| `experimental` | Feature-complete but API may evolve | Best-effort migration support |
| `stable` | Production-ready, backwards-compatible | Semantic versioning guarantees |
| `deprecated` | Scheduled for removal | Migration path documented |

### Stability Annotations
```diamond
/// @stability unstable
/// @since 0.2.0
fn experimental_feature() -> Result[T, E] { ... }

/// @stability stable
/// @since 0.1.0
fn established_function() -> T { ... }
```

---

## Authoring Standards

### Documentation
Every public item must have:
- Doc comment with description and examples.
- Parameter and return type documentation.
- Effect and capability requirements.
- Reference to relevant spec sections.

```diamond
/// Read the contents of a file as a string.
///
/// # Arguments
/// * `path` - The file path to read.
///
/// # Returns
/// The file contents as a UTF-8 string.
///
/// # Performs
/// * `FileSystem.read` - Requires `FileSystem` capability.
///
/// # Example
/// ```diamond
/// let content = read_file("config.toml")
/// ```
///
/// @capability FileSystem(read)
/// @stability stable
/// @since 0.1.0
fn read_file(path: String) -> String performs FileSystem { ... }
```

### Code Style
- Follow Diamond syntax conventions (square-bracket generics, explicit `perform`).
- Keep functions focused and composable.
- Prefer pure functions; isolate effects.
- Use descriptive names reflecting semantic intent.
- Include inline comments for non-obvious logic.

### Error Handling
- Use `Result[T, E]` for fallible operations.
- Provide typed error enums with context.
- Document error conditions and recovery options.
- Prefer recoverable errors over panics.

---

## Testing Requirements

### Unit Tests
- Test all public functions.
- Cover edge cases and error paths.
- Use deterministic inputs for reproducibility.

### Property Tests
- Test invariants with property-based testing.
- Use generators for semantic types.
- Verify refinement type constraints.

### Integration Tests
- Test module interactions.
- Verify capability enforcement.
- Test effect handler behavior.

### Example-Based Tests
- Ensure all README examples are tested.
- Examples should be runnable as-is.

---

## Capability Manifest Format

Each module includes a `capabilities.toml`:

```toml
[module]
name = "std-io"
version = "0.1.0"
stability = "experimental"

[[required_capabilities]]
capability = "FileSystem"
permissions = ["read", "write"]
justification = "File I/O operations require filesystem access"

[[required_capabilities]]
capability = "Network"
permissions = ["read"]
justification = "HTTP client functionality requires network access"

[[optional_capabilities]]
capability = "FileSystem"
permissions = ["delete"]
justification = "Optional cleanup operations"
```

---

## Versioning Policy

The standard library follows semantic versioning:

- **Major**: Breaking API changes (reserved for 1.0+).
- **Minor**: New features, backwards-compatible.
- **Patch**: Bug fixes, documentation updates.

### Pre-1.0 Policy
Before version 1.0:
- Minor versions may include breaking changes.
- Document all breaking changes in CHANGELOG.
- Provide migration guides for significant changes.

---

## Review & Approval Matrix

| Change Type | Required Approvals |
| --- | --- |
| New module proposal | Language WG + RFC |
| New public API | Language WG |
| Capability requirements | Security WG |
| Effect declarations | Language WG + Runtime WG |
| Breaking changes | Language WG + RFC |
| Stability promotion | Language WG + Runtime WG |

---

## Quality Checklist (Pre-Merge)

- [ ] All public items have comprehensive doc comments.
- [ ] Capability requirements documented and manifested.
- [ ] Effects declared and documented.
- [ ] Unit tests cover all public functions.
- [ ] Property tests verify type invariants.
- [ ] Examples are runnable and tested.
- [ ] README documents usage and capabilities.
- [ ] CHANGELOG updated for user-facing changes.
- [ ] Stability level declared for new APIs.
- [ ] No ambient authority assumptions.
- [ ] Semantic types enforce constraints correctly.
- [ ] Code follows Diamond style conventions.

---

## Contribution Workflow

1. **Proposal**
   - Open an issue describing the module or feature.
   - For new modules, draft an RFC.
   - Identify capability and effect requirements.
   - Propose API surface with examples.

2. **Implementation**
   - Create module structure following the template.
   - Implement with comprehensive documentation.
   - Write tests alongside code.
   - Include examples for each major feature.

3. **Review**
   - Request review from appropriate working groups.
   - Address feedback on API design and security.
   - Ensure capability and effect hygiene.

4. **Publication**
   - Update stdlib index in README.
   - Add CHANGELOG entry.
   - Announce new modules in release notes.

5. **Maintenance**
   - Monitor for issues and regressions.
   - Update for Diamond language evolution.
   - Document deprecations with migration paths.

---

## Module-Specific Expectations

### `std-agent/`
Core agent primitives:
- Prompt construction and validation.
- Decision tree utilities.
- Agent lifecycle management.
- Tool invocation helpers.

### `std-memory/`
Memory and persistence:
- In-memory caching.
- Continuation-aware state management.
- Serialization utilities.
- Memory pool abstractions.

### `std-unit/`
Type system utilities:
- Common refinement types (Email, Url, etc.).
- Unit type constructors.
- Type conversion utilities.
- Validation predicates.

---

## Future Enhancements

- Module bundling for tree-shaking unused code.
- Capability-based module loading at runtime.
- Cross-module type sharing protocols.
- Documentation generation from source.
- Interactive playground for stdlib exploration.
- Community module contribution pathway.

---

The standard library is Diamond's foundation for agent development. Every module should exemplify the language's principles: explicit capabilities, algebraic effects, semantic types, and secure-by-default design. Build modules that developers trust and learn from.