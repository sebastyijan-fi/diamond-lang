# Diamond v1 Semantic Contracts

Purpose: lock backend-independent semantics that must remain stable as new backends are added.

Scope: this is normative for profile-v1 language behavior; implementation details may vary by backend only when results are observationally equivalent.

---

## 1) String Contract

- Source strings are Unicode string literals in `.dmd` source.
- Runtime string operations are defined over Unicode code points, not raw bytes.
- `ln(s)` returns code-point count.
- `split(s, sep)` follows exact separator matching, including Unicode separators.
- Indexing/slicing semantics:
  - `s[i]` and `s[i:j]` are semantic string index/slice operations.
  - Python backend currently uses native Python `str` indexing/slicing.
  - Future backends MUST preserve code-point behavior (not byte indexing).
- Cursor helpers:
  - `peek(s,i,d)` returns `s[i]` when in bounds, else default `d`.
  - `take(s,i,n)` returns bounded substring from `i` with length `n`.

Notes:
- Grapheme-cluster semantics are out of scope for v1.

---

## 2) Numeric Contract

- Number literals are parsed as `NumberExpr` and lowered by backend/runtime rules.
- Python backend behavior is authoritative for v1:
  - integer literals map to Python `int` (arbitrary precision),
  - decimal literals map to Python `float`.
- Diamond `/` operator is integer-floor division in v1 via `dm.idiv(a, b)`.
  - divide-by-zero raises `ZeroDivisionError`.
- Diamond `$` midpoint operator is `floor((a+b)/2)` via `dm.midpoint(a, b)`.
- Static `Z`/`R` split is not part of v1 IR yet.

---

## 3) Type Surface and Value Contract

- Top-type aliases in v1: `O`, `Any`, `any`, `Unknown`, `unknown`, `Top`, `top`.
- Unsigned integer aliases in v1: `UInt`, `uint`, `U32`, `u32`, `U64`, `u64` (numeric surface in V1).
- Pointer-sized integer aliases in v1: `USize`, `usize`, `ISize`, `isize` (numeric surface in V1).
- Byte aliases in v1: `Byte`, `byte`, `U8`, `u8`.
- Character/Unicode scalar aliases in v1: `Char`, `char`, `Rune`, `rune`.
- Byte-string aliases in v1: `Bytes`, `bytes`, `ByteString`, `bytestring` (modeled as list-of-byte semantics).
- Unit/void aliases in v1: `none`, `None`, `Unit`, `V`, `Void`, `void`.
- Bottom-type aliases in v1: `Never`, `never`, `!`.
- `Never` is assignable to every target type and models non-returning paths (for example, `reraise` in a handler).
- Nullability policy in v1 is non-null-by-default for concrete types.
- `none` is the absence literal and is only assignable to unit/void aliases and top-type aliases.
- Implicit nullable references and nullable type constructors are out-of-profile in v1.
- Named user-defined types are nominal in v1 (`A` is not assignable to `B` unless names match exactly).
- Record types are structural in v1 (source must satisfy required target fields with assignable field types).
- User-defined `type` aliases and `newtype` declarations are out-of-profile in v1 and rejected by parser surface.
- Built-in canonical type aliases listed in this contract are the only alias surface in v1.
- Overloading is out-of-profile in v1: duplicate top-level function names are compile-time errors.
- Method overloading by parameter type/arity is out-of-profile in v1: duplicate class-method names are compile-time errors.
- Function signatures have exactly one return slot in v1.
- Multi-return signatures are out-of-profile in v1 and rejected by parser surface.
- Multi-value results in v1 must be encoded as a single list/record payload in that one return slot.
- Enum/union/tagged-union declaration syntax is out-of-profile in v1 and rejected by parser surface.
- Generic function/type-parameter syntax is out-of-profile in v1 and rejected by parser surface.
- `Char` accepts single-codepoint string literals; multi-codepoint string literals are `Str` and are not assignable to `Char`.
- Macro/annotation/compile-time-eval syntax is out-of-profile in v1 and rejected by parser surface.
- Reflection/source-generation syntax is out-of-profile in v1 and rejected by parser surface.
- Effect typing/algebraic-effects syntax is out-of-profile in v1 and rejected by parser surface.

- Lists and records are value-level language constructs.
- Runtime helper operations that update records (`patch`, `put`, `del_`) MUST return new records and must not mutate input arguments.
- Record equality is structural.
- Identity/reference checks are not part of Diamond language semantics.

---

## 4) Error Contract

Diamond v1 uses exception transport semantics end-to-end.

- `expr?` lowers to propagation wrapper (`dm.propagate(...)`):
  - returns value on success,
  - rethrows exception on failure,
  - records propagation error event in trace log.
- `try(body, e: handler)` lowers to `dm.try_catch(...)`:
  - catches exceptions from `body`,
  - returns handler value,
  - if handler returns `reraise` sentinel, original exception is rethrown.
- `isexc(e, T...)` lowers to exception-type checks.

Composition rule in v1:
- `?` and `try` interoperate through the same exception channel.
- No separate `Result` wrapper conversion exists in v1.

External contract stub rule:
- C-contract module comments (`//@block exposes ...`) may produce external stub declarations when dependency bodies are absent.
- Stub invocation lowers to `dm.extern_call(symbol, args)` and MUST raise `NotImplementedError` by default.
- Backends may override this only with an explicitly configured external-link mechanism that preserves failure visibility.

---

## 5) Tool Runtime Contract (v1)

- Trace ops append to in-memory `TRACE_LOG`.
- Resource counters use in-memory `RESOURCE_COUNTER`; enforcement is active only if `RESOURCE_LIMIT` is set.
- Capability checks are runtime-enforced when declared capabilities exist:
  - required capabilities are derived from function tool header identifiers excluding control tools `c,t,b,e`,
  - policy modes:
    - `allow_all` (default): permit all declared capabilities,
    - `allow_list`: deny when declared capabilities are not in granted set.
  - `cap_check` raises `PermissionError` on denial.
  - runtime policy can be configured via:
    - env vars: `DIAMOND_CAP_MODE`, `DIAMOND_CAP_GRANTED`
    - runtime helpers: `set_capability_policy(...)`, `reset_capability_policy()`.

Static composition contract:
- Capability composition is validated before backend emission:
  - computed requirement = transitive union of local callee requirements + capability-sensitive builtin usage,
  - explicit declaration (if present) is a restriction ceiling and must include computed requirement.
- Declarations are tool-header identifiers excluding control tools `c,t,b,e`.
- Missing declared capabilities are compile-time errors.

---

## 6) Conformance Requirement

Any executable backend/runtime pair must pass:
- behavior equivalence harness (`src/transpiler/run_behavior_tests.py`)
- stdlib/runtime conformance suite (`src/conformance/run_stdlib_conformance.py`)

Conformance suite is the operational check that backend changes preserve these contracts.

---

## 7) Concurrency scope (V1)

- V1 semantics are defined for a single-thread domain.
- Async/coroutine/generator constructs are out-of-profile in V1.
- Synchronization primitives and memory-ordering semantics are out-of-profile in V1.
- Structured cancellation semantics are out-of-profile in V1.

These exclusions are enforced by profile policy validation, not by ad-hoc conventions.
