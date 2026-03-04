# Diamond Transpiler v0: Architecture Deep Dive

Purpose: describe the actual runtime architecture of the current codebase, not an aspirational one.

This document answers:
- how data flows from `.dmd` source to executable output,
- where semantics are defined,
- where failures can occur,
- what is stable vs. still stubbed.

---

## 1) System Boundaries

Input:
- Diamond source files (`*.dmd`)

Core pipeline:
- parse (`grammar.py` + `parse_to_ir.py`)
- semantic IR (`diamond_ir.py`)
- static semantic/type validation (`semantic_validate.py`)
- static capability validation (`capability_validate.py`)
- backend emit (`backends/*`)
- runtime shim (`runtime/diamond_runtime.py`, `runtime/diamond_runtime.js`, `runtime/diamond_runtime.rs` depending on backend)

Execution/validation paths:
- benchmark behavior harness (`run_behavior_tests.py`)
- Phase B real-project parity harness (`certification/real-repos/retry/build_and_test_transpiled.sh`)
- stdlib conformance harness (`src/conformance/run_stdlib_conformance.py`)

Current executable targets:
- Python
- Rust
- JavaScript
- Wasm (transitional parity mode via JavaScript lowering)

---

## 2) Component Map

### 2.1 Entrypoint and orchestration

- `src/transpiler/transpile.py`
  - parses CLI args (`--in`, `--backend`, `--out-dir`, `--dump-ir-json`, skip-validation toggles)
  - selects backend via registry
  - builds one parser instance
  - runs static semantic/type validation
  - runs static capability composition validation
  - iterates inputs and emits target files
  - copies Python runtime shim when backend is `python`

### 2.2 Grammar and parser

- `src/transpiler/grammar.py`
  - LALR grammar for profile-v1 style Diamond
  - includes:
    - expression forms (`?:`, match chains, map bind, ranges),
    - postfix ops (call/member/index/slice/patch/propagate),
    - exception forms (`try(...)`, `isexc(...)`, `reraise`),
    - function declarations + tool headers.

- `src/transpiler/parse_to_ir.py`
  - converts parse tree nodes to typed IR dataclasses
  - resolves operator precedence and associativity
  - maps tool symbols to `ToolOp` nodes (`t`, `c`, `b`, `e`)
  - supports D10 B-core inline modules:
    - extracts `@block{...}` segments,
    - resolves `block.symbol` references,
    - enforces private `_name` visibility,
    - flattens to mangled declaration names.
  - returns `Program(module_name, decls)`

### 2.3 IR model

- `src/transpiler/diamond_ir.py`
  - semantic, language-agnostic AST/IR
  - explicit schema version constant: `IR_VERSION = "0.1.0"`
  - node families:
    - types: `TypeName`, `TypeList`, `TypeRecord`
    - expressions: arithmetic/control/data/match/postfix
    - error/exception forms: `PropagateExpr`, `TryCatchExpr`, `ExceptionMatchExpr`, `ReraiseExpr`
    - tool ops: trace/capability/resource/error-context
  - design intent: IR represents Diamond semantics, not Python syntax.

### 2.4 Backend registry and emitters

- `src/transpiler/backends/__init__.py`
  - backend registry `BACKENDS` and `get_backend(name)`.

- `src/transpiler/backends/python_backend.py`
  - executable lowering to Python expression code
  - applies:
    - operator lowering (`$` midpoint, `/` integer division via runtime helper),
    - built-in call mapping (`ln`, `split`, `put`, etc. -> runtime funcs),
    - tool-op injection at function boundary.

- `src/transpiler/backends/rust_backend.py`
- `src/transpiler/backends/wasm_backend.py`
- `src/transpiler/backends/js_backend.py`
  - Rust and JS emitters are executable (`diamond_runtime.rs` and `diamond_runtime.js` respectively).
  - Wasm emitter currently reuses JS semantics in a compatibility mode.

### 2.5 Runtime shim (Python execution semantics)

- `src/transpiler/runtime/diamond_runtime.py`
  - defines runtime semantics used by generated Python:
    - collection helpers (`patch`, `member`, `fold`, `range_inclusive`),
    - safety/math helpers (`idiv`, `midpoint`),
    - tool runtime (`trace_enter/exit`, `resource_tick`, `with_error_context`),
    - exception utilities (`try_catch`, `RERAISE`, `propagate`, `is_tuple`),
    - Phase-B retry helpers (`call_with`, `sleep`, `rand_uniform`, `log_retry_warning`, `make_retry_decorator`).

### 2.6 IR observability

- `src/transpiler/ir_json.py`
  - dataclass-to-JSON serializer with explicit `_kind` tags.
  - `Program` JSON includes `ir_version` for forward compatibility checks.

### 2.7 Static semantic + capability validation

- `src/transpiler/semantic_validate.py`
  - validates high-confidence semantic invariants before emit:
    - undefined value symbols,
    - local/builtin call arity checks,
    - concrete type mismatches (where inferable),
    - invalid `reraise` placement.
  - intentionally conservative for dynamic `O` paths (runtime remains authority there).

- `src/transpiler/capability_validate.py`
  - computes per-function required capabilities as transitive union over:
    - capability-sensitive builtin calls,
    - local function call graph edges.
  - compares computed requirements with explicit declared capabilities
    (tool-header identifiers excluding control tools `c,t,b,e`).
  - enforces missing-capability failures before code emission.

---

## 3) End-to-End Data Flows

### 3.1 Standard transpile flow

```text
*.dmd
  -> Lark parse tree (grammar.py)
    -> semantic IR Program (parse_to_ir.py + diamond_ir.py)
      -> static semantic/type validation (semantic_validate.py)
      -> static capability validation (capability_validate.py)
      -> backend emitter (python/rust/wasm/js)
        -> output file(s)
          -> (python only) generated code imports diamond_runtime.py
```

Operational details:
- One parser instance is reused for all files in a run.
- If `--dump-ir-json` is set, `*.ir.json` is emitted alongside outputs.

### 3.2 Behavior-harness flow (`run_behavior_tests.py`)

```text
Diamond scenario directory
  -> transpile.py (python backend)
    -> generated python modules + runtime
      -> dynamic import generated function
      -> dynamic import reference solve()
      -> case adapters/canonicalizers
      -> compare outputs case-by-case
      -> PASS/FAIL table + summary
```

Why adapters exist:
- some generated programs use compact record shapes, operation-object inputs, or encoded values;
- harness adapters normalize args/outputs to compare behavior, not syntax.

### 3.3 Phase B real-project parity flow (`invl/retry`)

```text
Diamond port source (api_dm.dmd)
  -> transpile.py (python)
    -> api_dm.py + runtime
      -> package assembly script builds retry-compatible module layout
      -> upstream tests (pytest) run against transpiled implementation
```

Current result:
- baseline upstream snapshot: `9/9` pass
- transpiled Diamond parity package: `9/9` pass

---

## 4) Semantic Responsibility Split

## 4.1 Parser responsibilities

Parser owns:
- syntactic validity and precedence/associativity;
- construction of semantically-typed IR nodes;
- deterministic mapping from tool header symbols to `ToolOp` list.

Parser does not own:
- runtime behavior of builtins;
- effect enforcement policy;
- backend-specific lowering choices.

## 4.2 Backend responsibilities

Backend owns:
- mapping IR nodes into target-language expressions/statements;
- preserving evaluation semantics through emitted structure;
- injecting function-level tool instrumentation wrappers where required.

Backend does not own:
- tokenizer optimization;
- global policy decisions for gates/benchmarks;
- persistent trace or capability policy storage.
- semantic contract definition changes (see `docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md`).

## 4.3 Runtime responsibilities (Python)

Runtime owns:
- final operational behavior of helper intrinsics and tool utilities;
- shared implementation of helpers to keep generated code concise.

Runtime capability policy:
- `cap_check` enforces declared capabilities under runtime policy modes:
  - `allow_all` (default),
  - `allow_list` (denies missing capabilities with `PermissionError`).
- Policy input can be set via env (`DIAMOND_CAP_MODE`, `DIAMOND_CAP_GRANTED`) or runtime helpers.

---

## 5) Tool-Layer Architecture

Tool-layer information originates in function declaration headers:
- example symbol set: `t` (trace), `c` (capability), `b` (resource), `e` (error context).

Flow:
1. parser maps symbols -> `ToolOp` IR nodes.
2. Python backend detects `ToolOp` presence and injects wrapper logic:
   - `cap_check`,
   - `resource_tick`,
   - `trace_enter/trace_exit`,
   - `try/except + with_error_context` for `e`.
3. runtime executes helper operations.

Design effect:
- tool semantics are attached at declaration boundaries, not bolted on by external decorators in generated output.

---

## 6) Exception and Propagation Architecture

Two parallel mechanisms now exist:

1. Propagation (`expr?`)
- lowered to `dm.propagate(lambda: expr)`
- intended for streamlined error-propagation patterns.

2. First-class exception handling
- `try(body, e: handler)` -> `dm.try_catch(lambda: body, lambda e: handler)`
- `isexc(e, T1, T2, ...)` -> `isinstance(e, (...))`
- `reraise` valid only inside handler context (compiled as runtime sentinel resolved to bare re-raise).

This split lets Diamond represent:
- concise propagation where suitable,
- explicit exception-match and rethrow behavior where needed (e.g., retry logic).

Contract note:
- v1 treats both mechanisms as exception-transport paths (no separate Result-value conversion layer).
- Normative semantics are locked in `docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md`.

---

## 7) Failure Modes and Diagnostics

### 7.1 Parse/grammar failures

Symptoms:
- Lark parse errors,
- parser `ValueError` from unsupported/invalid node shapes.

Where surfaced:
- `transpile.py` run fails for affected file.

Typical causes:
- ambiguous/unimplemented syntax form,
- grammar/parser drift for new constructs.

### 7.2 Lowering failures (backend)

Symptoms:
- backend raises `ValueError("unsupported ...")`.

Typical causes:
- new IR node not handled by backend emit logic,
- context rule violation (e.g., `reraise` outside handler).

### 7.3 Runtime semantic failures

Symptoms:
- generated Python imports but errors at execution time.

Typical causes:
- missing runtime helper,
- helper semantics mismatch with intended Diamond meaning,
- placeholder policy hooks not enforcing expected constraints.

### 7.4 Equivalence failures in harnesses

Symptoms:
- case-level mismatches (`expected != got`) in behavior harness output.

Typical causes:
- adapter/canonicalization mismatch,
- subtle lowering semantic drift,
- reference implementation semantics mismatch.

---

## 8) Invariants (Current)

The architecture currently relies on these invariants:

1. Parser and backend agree on IR node set.
2. Python backend call-map names exist in runtime shim.
3. Runtime shim is copied into output dir for Python runs.
4. Harnesses compare behavior, not source text.
5. New syntax features are not considered done until:
   - existing portfolio remains green,
   - target scenario tests pass.

---

## 9) Extension Points

### 9.1 Add a new syntax construct

Minimal path:
1. grammar production in `grammar.py`
2. IR node in `diamond_ir.py`
3. parser mapping in `parse_to_ir.py`
4. backend lowering in `python_backend.py`
5. runtime helper (if needed)
6. behavior tests + regression on portfolio batch.

### 9.2 Add/upgrade a backend

Minimal path:
1. implement real lowering in backend file
2. register extension/emitter in `backends/__init__.py`
3. add runtime strategy (embedded runtime vs stdlib mapping)
4. add backend-specific behavioral tests.

### 9.3 Harden tool-layer enforcement

Likely next steps:
1. wire capability policy to host sandbox/permission backends
2. formalize trace sink/export interface
3. scope resource counters (per function call vs global execution).

---

## 10) What Is Stable vs. In Flux

Stable:
- parse -> IR -> python emit pipeline shape,
- portfolio behavior harness workflow,
- gate-locked construct-tool profile outcomes,
- first real-project parity path (`retry`).

In flux:
- non-Python backend executability,
- policy-enforcement depth (capabilities/resources),
- parser edge ergonomics (e.g., ternary list-then-arm formatting to avoid `?[` shorthand),
- multi-tokenizer profile operationalization.
