# Diamond v1 Limitations

Purpose: explicit boundaries of what Diamond v1 currently does not solve (or only partially solves).

Scope of evidence:
- `docs/decisions/profile_v1/AMBIGUITY_CHECKS.md`
- `docs/decisions/profile_v1/DECISION_DEFENSE.md`
- `docs/decisions/profile_v1/VALIDATION.md`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`
- `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_validation.md`
- `src/transpiler/README.md`
- `src/transpiler/runtime/diamond_runtime.py`
- `certification/real-repos/retry/README.md`

---

## 1) Syntax and Parseability Limits

1. `expr?[index]` is now parser-resolved:
- `?[` (without whitespace) is parsed as postfix propagation + index/slice.
- Ternary remains available with list-literal then-arms via `x ? [..] : y` (space) or explicit parentheses.
- Source: `docs/decisions/profile_v1/AMBIGUITY_CHECKS.md`.

2. Dense syntax is intentionally machine-optimized, not human-readable:
- This is a design choice, but it limits manual review/debug ergonomics.
- Source: `docs/decisions/profile_v1/DECISION_DEFENSE.md`.

3. Profile v1 grammar promotion evidence is bounded:
- Formal profile validation was done on 10 canonical profile programs (`10/10` parser check).
- Broader execution validation exists, but grammar promotion itself was originally framed on that 10-program set.
- Source: `docs/decisions/profile_v1/VALIDATION.md`.

4. Contract comments are orchestration metadata, not semantics:
- `// ...` line comments are parser-ignored and used by C-contract context packs.
- Contract comment headers (`//@block exposes ...`) do not provide executable symbol bodies by themselves.
- Full compilation still requires complete block source files.

---

## 2) Semantic/Type-System Limits

1. Static semantic/type validation is conservative (not full HM-style typing):
- v1 transpiler now runs a static semantic pass before backend emit (`semantic_validate.py`).
- It catches high-confidence issues (undefined symbols, arity mismatches, obvious type mismatches, invalid `reraise` placement).
- It is intentionally not a complete type system: dynamic paths (`O`/external calls/runtime-polymorphic helpers) still rely on runtime semantics.

2. Builtin semantics are runtime-coupled:
- Behavior of core helpers (`fold`, `member`, `patch`, conversions, etc.) is defined by runtime shim implementation rather than a separately verified formal semantics layer.
- v1 now mitigates drift with explicit semantic contracts and runtime conformance cases, but semantics are still anchored to runtime behavior in practice.
- Source: `src/transpiler/runtime/diamond_runtime.py`.
- Source: `docs/decisions/profile_v1/SEMANTIC_CONTRACTS.md`, `src/conformance/run_stdlib_conformance.py`.

3. Exception model is now expressive but still early:
- `try(...)`, `isexc(...)`, and `reraise` are implemented and tested, but this area is new relative to the older profile corpus and should be considered higher-change-risk.

---

## 3) Backend and Runtime Limits

1. Only Python backend is executable:
- Rust/Wasm/JS emitters are stubs/non-executable placeholders.
- Source: `src/transpiler/README.md`.

2. Capability enforcement is deny-by-policy, not OS-sandbox:
- `cap_check(...)` now enforces declared capabilities under runtime policy (`allow_all` / `allow_list`) and raises `PermissionError` on denial.
- Static transpile-time composition validation enforces declared-vs-computed capability requirements before emit.
- Current limit: this is language/runtime policy enforcement, not operating-system sandboxing.
- Source: `src/transpiler/runtime/diamond_runtime.py`.
- Source: `src/transpiler/capability_validate.py`.

3. Resource limits are opt-in and global:
- Resource accounting exists, but `RESOURCE_LIMIT` defaults to `None` (no enforcement).
- Source: `src/transpiler/runtime/diamond_runtime.py`.

4. Tooling observability is in-memory:
- Trace events are appended to in-memory lists; no persistence/export contract is standardized yet.

---

## 4) Compression/Economics Limits

1. Performance is shape-dependent at per-program level:
- Final validated portfolio passes all gates in aggregate, but per-program outcomes vary widely.
- In gate-lock run:
  - best net reduction: `69.81%` (`01_fizzbuzz`)
  - weakest net reduction: `10.60%` (`05_rate_limiter_token_bucket`)
- Source: `research/benchmarks/measurements/construct_tool_portfolio14_v4_gate_lock_q1.csv`.

2. Not every program beats Python-with-tools by >=60% individually:
- In gate-lock run, several programs are below `0.60` on `vs_python_with_tools`:
  - `05`, `06`, `09`, `16`
- Portfolio still passes due strong aggregate (`65.29%`).

3. Optimization target is currently tokenizer-specific:
- The measured lock is based on Qwen tokenizer setup; cross-tokenizer parity is not yet established as a locked result.

---

## 5) Validation Coverage Limits

1. Benchmarks are representative, not exhaustive:
- The validated construct-tool portfolio run covers 14 programs.
- This is strong evidence, but not full language-completeness across arbitrary production code shapes.

2. Real-project port evidence is still limited in breadth:
- Phase B currently includes three projects:
  - `invl/retry` (`9/9`),
  - `pytest-dev/iniconfig` (`49/49`),
  - `hukkin/tomli` (`16/16`, `744` subtests) with differential case parity on executable corpus.
- This is strong evidence, but still a small sample of software domains.
- Source:
  - `certification/real-repos/REAL_REPO_CERTIFICATION_2026-03-03.md`
  - `docs/reference/certification/tomli/RESULTS.md`

3. Behavioral equivalence depends on adapters/runtime shims:
- For real-project parity runs, compatibility adapters are used where needed (e.g., module surface expectations).
- This is valid engineering, but it means parity is not yet entirely “direct lowering with zero glue.”

4. C-contract context snapshots execute via explicit stubs:
- They are intended for LLM chunk-context exchange (dependency contracts + active block).
- Contract-only dependencies transpile to external stubs that raise `NotImplementedError` when invoked.
- Full parity execution still requires complete module sources.

---

## 6) Governance/Freeze Limits

1. Syntax is “v1 locked” by current gates, but still operationally evolvable:
- Several documented caveats are explicitly deferred until triggered by real ports.
- This means freeze is pragmatic, not mathematically final.

2. Profile-system vision is ahead of implementation completeness:
- Surface-profile generation and tokenizer-aware strategy are documented and partially exercised, but full multi-tokenizer operationalization is still an open execution track.

---

## Current Practical Interpretation

Diamond v1 is currently strong on:
- measured token economics at portfolio level,
- parser/IR/backend coherence for Python execution,
- construct-tool composition economics,
- initial real-project port proof.

Diamond v1 is currently limited by:
- dense-syntax ergonomics around ternary/list formatting conventions,
- non-executable non-Python backends,
- capability enforcement not yet wired to host/OS sandbox primitives,
- tokenizer-specific optimization lock,
- still-small real-project sample size.
