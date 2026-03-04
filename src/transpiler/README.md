# Transpiler v0 Architecture

Deep dive:
- `src/transpiler/ARCHITECTURE_DEEP_DIVE.md`
- `docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md` (normative semantics for backend parity)

Diamond transpilation is structured as:

Diamond source
- Parser (`grammar.py` + `parse_to_ir.py`)
- IR (`diamond_ir.py`) [language-agnostic]
- Backend emitter (`backends/*`)

Backends currently wired:
- `python` (v0 correctness target, executable lowering)
- `rust` (executable, uses `diamond_runtime.rs`)
- `wasm` (transitional parity mode, reuses JS executable lowering)
- `js` (executable)

## Design Constraint

The IR must represent Diamond semantics, not Python semantics.
Backends translate the same IR into target-language idioms.

## Current Scope

Implemented:
- Parse `.dmd` into semantic IR:
  - `Program`, `FuncDecl`, `Param`
  - structured `TypeExpr` nodes (`TypeName`, `TypeList`, `TypeRecord`)
  - structured `Expr` nodes (binary/unary/ternary, sequence `;`, match arms, calls, member/index/slice, map/list, patch, binder, range, propagate, `try(...)`, `isexc(...)`, `reraise`)
- structured tool-op nodes on functions (`TraceEntryOp`, `TraceExitOp`, `CapabilityCheckOp`, `ResourceIncrementOp`, `ErrorContextOp`)
- D10 B-core inline modules:
  - parse `@block[cap:...] { decl* }` sources,
  - resolve qualified refs (`block.symbol`),
  - enforce private visibility (`_name`),
  - flatten to mangled declarations (`block__symbol`) in IR.
  - parse `//@block exposes ...` contract comments and emit external stub declarations for context-pack transpilation.
- Emit executable Python plus executable Rust and JS emitters; wasm is currently parity-mode (JS executable).
- Optional IR JSON dumps with explicit `_kind` tags for every node.
- IR JSON root now includes `ir_version` (currently `0.1.0`).
- Grammar keeps `true`/`false` as boolean literals to avoid `t`/`f` identifier collisions in compressed code.
- Python backend lowers expressions to executable Python and imports a shared runtime shim (`diamond_runtime.py`).
- Static semantic/type validation runs before backend emission; high-confidence errors fail transpilation.
- Static capability composition validation runs before backend emission; missing declared capabilities fail transpilation.
- Runtime capability policy enforcement is active in Python runtime:
  - `allow_all` (default) and `allow_list` modes
  - denied capability checks raise `PermissionError`.
  - Compatibility note: Python lowering currently treats unbound names `t`/`f` as `True`/`False` for legacy corpus files that still encode booleans that way.
  - Exception handling lowering:
    - `try(body, e: handler)` -> `dm.try_catch(lambda: body, lambda e: handler)`
    - `isexc(e, ...)` -> `isinstance(...)`
    - `reraise` -> handler-scoped rethrow via `dm.RERAISE` sentinel + bare `raise` inside runtime `try_catch`.

Pending:
- WAT-native Wasm codegen and Wasm-specific validation parity.

## Commands

Python backend:

```bash
. .venv/bin/activate
python src/transpiler/transpile.py \
  --in docs/decisions/profile_v1/programs \
  --backend python \
  --out-dir src/transpiler/out/python \
  --dump-ir-json
```

This command also copies `runtime/diamond_runtime.py` to the output directory as `diamond_runtime.py`.

Other backends:

```bash
python src/transpiler/transpile.py --in docs/decisions/profile_v1/programs --backend rust --out-dir src/transpiler/out/rust
python src/transpiler/transpile.py --in docs/decisions/profile_v1/programs --backend wasm --out-dir src/transpiler/out/wasm
python src/transpiler/transpile.py --in docs/decisions/profile_v1/programs --backend js   --out-dir src/transpiler/out/js
```

Compatibility wrapper (old command):

```bash
python src/transpiler/diamond_to_python_stubs.py --in docs/decisions/profile_v1/programs --out-dir src/transpiler/out/profile_v1
```

Behavior checks (start with hardest math-heavy shapes):

```bash
python src/transpiler/run_behavior_tests.py
python src/transpiler/run_behavior_tests.py --batch batch1
python src/transpiler/run_behavior_tests.py --batch all_profile10
python src/transpiler/parser_regression_tests.py
python src/transpiler/semantic_validation_tests.py
python src/transpiler/semantic_validate.py --in docs/decisions/profile_v1/programs
python src/transpiler/module_system_regression_tests.py
python src/transpiler/capability_validation_tests.py
python src/transpiler/capability_validate.py --in docs/decisions/profile_v1/programs
python src/transpiler/capability_validate.py --in certification/real-repos/retry/diamond --max-warnings 4
python src/transpiler/diagnose_regression_tests.py
python src/conformance/run_stdlib_conformance.py
```

Diagnose mode (machine-readable parser diagnostics):

```bash
python src/transpiler/diagnose.py --in docs/decisions/profile_v1/programs/01_fizzbuzz.dmd --pretty
python src/transpiler/diagnose.py --in docs/decisions/profile_v1/programs --out /tmp/diamond_diagnose.json
```

CI gate checks (behavior + construct-tool thresholds):

```bash
./scripts/ci/validate_v1_gates.sh
```

Latest local run (profile10 harness):
- `40/40` passing across `01,04,06,07,08,09,10,11,15,16`.

Latest local run (portfolio14 transpile smoke):
- `14/14` Diamond files in `fn_error_portfolio14_v4_math_patch/diamond_full` transpile successfully to Python.

Latest local run (portfolio14 behavior harness):
- `61/61` passing across full portfolio14-v4 batch.

Phase B (`invl/retry`) local run:
- `retry_call` subset: `4/4` passing
- Full upstream tests: `9/9` passing against transpiled Diamond core.

Known parsing note:
- `expr?` propagation is first-class for call/member/operator endings.
- `expr?[index]` is explicitly supported as postfix propagate+index/slice (`?[` form).
- If a ternary then-arm starts with a list literal, use `x ? [..] : y` (space) or parenthesize.
- `// ...` line comments are parser-ignored.
- Module sources may include leading contract metadata comments (`//@block exposes ...`) before `@block` declarations.

Capability validation note:
- Explicit capabilities are declared as extra tool-header identifiers (excluding control tools `c,t,b,e`).
- Computed requirements are transitive over local function calls plus capability-sensitive builtins.
- If explicit declaration exists, it is enforced as a restriction ceiling.
