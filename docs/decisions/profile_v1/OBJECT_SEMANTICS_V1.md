# Diamond V1 Object Semantics Contract

Status: normative for V1 profile behavior.

This contract defines `§Class` object behavior across Python, Rust, and WASM/TypeScript backends.

## 1. Scope and goals

- Preserve identical observable semantics across backends.
- Keep V1 semantics explicit, even where backend performance is not yet optimal.
- Prefer deterministic compile-time errors for invalid object operations.

## 2. Object model and shape policy

- V1 objects are **closed-shape** after construction.
- Construction defines the full field set.
- Reading or writing an undeclared field is invalid:
  - compile-time error when statically known,
  - runtime error only when static proof is unavailable.
- Dynamic field injection is out-of-profile for V1.

## 3. Construction and initialization

- Header arguments are promoted to fields in declaration order (left-to-right).
- Body fields initialize in lexical order (top-to-bottom).
- A field initializer may reference:
  - header fields,
  - already-initialized earlier body fields.
- Forward reference to later fields is invalid.
- Constructor failure aborts instance creation; no partially-initialized object escapes.

## 4. Receiver mutability model

- Declared object fields are mutable by default in V1.
- Methods are mutation-capable for declared `#.` fields; no immutable receiver qualifier exists in V1 syntax.
- `#` is the self binder and resolves to the implicit method receiver.
- Receiver declaration is implicit in V1 method surface syntax (no explicit `self` parameter).
- Rust lowering rule:
  - field reads use `borrow()`,
  - field writes use `borrow_mut()`.
- V1 compatibility runtime in Rust may still use `Rc<RefCell<T>>` while preserving read/write split per operation.

## 5. Identity, equality, hashing

- `is`: reference identity.
- `==`: structural equality over declared fields.
- Structural equality is cycle-safe (visited-pair algorithm) and must terminate.
- Equality compares shape and field values recursively.
- Objects are unhashable by default in V1 unless an explicit stable-hash policy is introduced later.

## 6. Aliasing and copy semantics

- Assignment and parameter passing are reference aliasing for objects.
- Mutating through one alias is visible through all aliases of same identity.
- No implicit deep copy on assignment or function return.
- Any deep-copy behavior must be explicit API surface in future versions.

## 7. Dispatch and inheritance policy

- V1 uses method dispatch on the concrete object type.
- Current Python lowering exposes methods as `Class__method` and supports member-call sugar through runtime dispatch (`obj.method(...)`).
- Classical class inheritance is out-of-profile for V1.
- Trait/interface system is out-of-profile for V1.
- Composition is the required reuse mechanism in V1.

## 8. Resource/finalization policy

- V1 does not define deterministic language-level destructors.
- Resource-safe behavior must use explicit APIs and backend runtime guarantees.
- Backends must not assume finalizer timing as part of language semantics.

## 9. Concurrency scope

- V1 object semantics are defined for a single-thread semantic domain.
- Cross-thread sharing guarantees are out-of-profile for V1.
- Rust compatibility mode (`Rc<RefCell<T>>`) is intentionally non-`Send`.

## 10. Backend lowering invariants

- Python:
  - identity uses Python object identity semantics.
  - structural equality follows this contract, not incidental host behavior where they diverge.
- WASM/TypeScript:
  - identity uses object reference identity.
  - structural equality must remain cycle-safe and shape-aware.
- Rust:
  - compatibility mode allows interior mutability for parity.
  - borrow type (`borrow` vs `borrow_mut`) follows operation kind.

## 11. Error categories

- Compile-time:
  - unknown field read/write when statically resolvable,
  - invalid forward-reference in initialization order.
- Runtime:
  - unknown field read/write only when static proof is not possible.

## 12. Conformance requirements

Backends are conformant only if they pass object semantics tests for:

- alias identity (`is`) and alias-visible mutation,
- closed-shape missing-field read/write rejection,
- structural equality for acyclic objects,
- structural equality for cyclic self-referential graphs (true and false cases),
- deterministic initialization ordering rules.

Current executable conformance anchor:

- `src/conformance/cases/runtime_v0_core.json` object cases,
- `src/conformance/run_stdlib_conformance.py`.
- `src/transpiler/backend_object_regression_tests.py` cross-backend emission regression.

## 13. Implementation milestone log (2026-03-04)

- Parser:
  - Deterministic top-level declaration chunk parsing added for adjacent method declarations.
  - Method tool headers are parser-regression locked.
- Semantic validator:
  - Closed-shape checks now reject unknown `#.<member>` access and unknown self-field mutation.
  - Typed `#.<method>(...)` dispatch validates arity/arg types and propagates return types.
  - Header/default class field types propagate into method type-checking (`#.<field>`).
  - Nominal object dispatch (`obj.member`, `obj.method(...)`) now validates against class shape.
- Capability validator:
  - Class-aware method call graphing (`#.m()` -> `Class__m`) with transitive capability checks.
