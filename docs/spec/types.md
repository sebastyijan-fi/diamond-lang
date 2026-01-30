# Diamond (<>) Type System Specification

**Status:** Draft v0.1  
**Audience:** Language designers, compiler engineers, runtime authors, and contributors implementing semantic analysis or tooling for Diamond (<>) source files.

---

## 1. Scope and Goals

The Diamond type system balances structural flexibility with semantic guarantees tailored for LLM-authored code.

- **Structural First:** Compatibility is determined by shape (fields, members) rather than nominal declarations.
- **Semantic Refinement:** `where` clauses attach machine-checkable constraints (grammars, verifier models).
- **Effect Awareness:** Functions implicitly carry effect sets derived from their call graph.
- **Capability Safety:** Types model capability possession to enforce object-capability (OCap) boundaries.
- **Interoperability:** Types map cleanly to JSON schemas, WebAssembly interface types, and Gem registry manifests.

---

## 2. Type Categories

| Category                | Example                            | Notes                                                                    |
|-------------------------|------------------------------------|--------------------------------------------------------------------------|
| Primitive               | `Int`, `Float`, `Bool`, `String`   | Value semantics, immutable, interoperable with host types                |
| Structural Records      | `struct User { id: Int }`          | Fields may specify defaults and refinements                              |
| Tuples                  | `(Int, String)`                    | Ordered, fixed arity                                                     |
| Arrays & Lists          | `List[String]`, `Array[Byte; 32]`  | `List` dynamic, `Array` fixed length (optional length spec)              |
| Enums (Tagged Unions)   | `type Result = Ok(T) | Err(E)`     | Exhaustive matching enforced                                             |
| Semantic Types          | `type Email = String where …`      | Runtime/decoder constraints, optional verifiers                          |
| Capability Types        | `capability Network`               | Encapsulate authority; injected at module boundary                       |
| Effects (Type Level)    | `func f() -> Int ! { Tool, Wait }` | Annotated or inferred; `!` suffix is rendering convention                |
| Traits & Interfaces     | `trait Summarize { ... }`          | Structural conformance with optional capability requirements             |
| Type Classes (Future)   | TBD frameworks                     | Deferred to RFC                                                          |

---

## 3. Structural Typing Rules

### 3.1 Field Compatibility

Two record types `A` and `B` are compatible if:

1. For every field `f` in `A`, `B` contains `f` with a compatible type.
2. Semantic refinements on `B.f` are equal to or stricter than those on `A.f`.
3. Optional fields default to refinement-compliant values.

```
Let A = { name: String where len <= 50 }
Let B = { name: String where len <= 30, age: Int? }
Then B <: A (B refines `name` more strictly and has extra optional fields).
```

### 3.2 Width & Depth Subtyping

- **Width subtyping:** Additional fields allowed (records behave like open structs).
- **Depth subtyping:** Field types must be covariant; refinements must strengthen (never weaken) the parent type’s guarantees.

### 3.3 Tuple & Array Variance

- Tuples are invariant in length and covariant per element.
- Arrays (`Array[T; N]`) are invariant in both element type and length.
- Lists (`List[T]`) are covariant in `T`.

---

## 4. Generic Types

Generics are expressed using square brackets to avoid conflict with the `< >` operator.

```
struct Page[T]:
    items: List[T]
    total: Int
```

Constraints:

- Upper bounds use `where` style: `T: Summary`.
- Trait constraints reference structural contracts (see §7).

---

## 5. Semantic Refinements

### 5.1 Syntax

```
type Email = String where:
    regex "[^@\\s]+@[^@\\s]+\\.[^@\\s]+"
    prompt "Ensure the address belongs to a verified corporate domain."
```

- `regex` clauses compile to deterministic grammars for constrained decoding.
- `prompt` clauses route to verifier models, run locally when feasible.
- Custom validators can reference stdlib hooks: `validate(self, rules.no_profanity)`.

### 5.2 Enforcement Phases

| Phase         | Enforcement Mechanism                                |
|---------------|------------------------------------------------------|
| Compile-time  | Linting via verifier models (optional, non-blocking) |
| Generation    | Constrained decoding masks for regex/enum cases      |
| Runtime       | Verifier or validator invocation prior to effect execution |

### 5.3 Casting & Trust Boundaries

- `as` keyword initiates effectful casting, returning `Result[T, SemanticError]` or raising an effect.
- Unsafe casts (`as?`) are under discussion; default pipeline must be failure-safe.

---

## 6. Capability Types

Capabilities encapsulate authority.

```
capability Network:
    allow hosts: ["api.stripe.com"]

struct PaymentClient:
    net: Network
```

Rules:

1. Capabilities cannot be copied arbitrarily; move semantics by default.
2. Traits can require capabilities: `trait Fetch requires Network`.
3. Functions must receive capabilities via parameters or module-level injection; there is no global namespace.

---

## 7. Traits & Structural Contracts

Traits declare required members and optional capabilities.

```
trait Summarize:
    func summarize(self) -> Summary ! { Prompt }

trait RemoteFetch requires Network:
    func fetch(self, url: Url) -> Response ! { Net }
```

- An implementing struct conforms if it supplies matching members with compatible types/effects.
- Capability requirements propagate to implementers.

---

## 8. Effect Typing

Functions inherently track the union of effects they can perform.

```
func analyze(text: String) -> Report ! { Prompt, Memory }:
    ...
```

Inference:

- Calls to `perform EffectX(...)` add `EffectX` to the signature.
- Higher-order functions aggregate effect sets of callbacks.
- Tooling surfaces inferred sets even if annotations omitted.

Effect compatibility:

- Callers must have authority to handle or propagate required effects.
- `handle` blocks may discharge effects, reducing the outward effect set.

---

## 9. Type Inference & Annotation

- Local type inference is Hindley–Milner inspired with structural awareness.
- Function return types must be explicit for public APIs; private helpers may omit when inference succeeds.
- Semantic refinements are not inferred; contributors must annotate intentionally.

---

## 10. Type Checking Algorithm Outline

1. **Parsing:** Build AST using grammar spec.
2. **Symbol Resolution:** Resolve identifiers, imports, capability manifests.
3. **Kinding:** Validate generic arity and trait constraints.
4. **Type Evaluation:** Apply structural compatibility rules, propagate refinements.
5. **Effect Analysis:** Walk body to collect performed effects, unify with handlers.
6. **Capability Verification:** Ensure required capabilities are in scope.
7. **Constraint Emission:** Generate constrained-decoding grammars and verifier hooks for semantic types.
8. **Wasm ABI Generation:** Map types to component signatures (records → structs, enums → variants, etc.).

---

## 11. Interop Semantics

- **JSON**: Structural records map to JSON objects; semantic refinements carry schema metadata.
- **Wasm Component Model**: Types convert to WIT interface types; capabilities become handles.
- **Gem Registry**: Type manifests included in package metadata for compatibility checking.

---

## 12. Error Reporting Guidelines

- Emit structural mismatch diagnostics with field-by-field diff.
- Highlight refinement conflicts with both producer and consumer definitions.
- Suggest capability imports when missing authority detected.
- Include effect provenance chain in errors to aid debugging.

---

## 13. Open Questions & RFC Hooks

1. Variance rules for generic traits.
2. Integration of type classes or default method implementations.
3. Formal verification hooks for semantic refinements.
4. Persistence of refinement proofs across continuation serialization.
5. Explicit type-level capability constraints on generic parameters.

Changes to this document must reference the relevant RFC in `docs/design-decisions/`.

---